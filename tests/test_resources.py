from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

from scripts.models import BuilderError
from scripts.resource_integrity import ResourcePreparationSettings, inspect_resource, resource_sha256
from scripts.resources import ResourceManager


class ResourceManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()
        self.manager = ResourceManager(self.root)
        self.manager.ensure_layout()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_sync_registers_file_and_directory_in_raw(self) -> None:
        (self.root / "resource" / "raw" / "cache-notes.md").write_text(
            "Cache notes",
            encoding="utf-8",
        )
        (self.root / "resource" / "raw" / "database-topic").mkdir()

        with patch("scripts.resources._now", return_value="2026-07-31T09:00:00+07:00"):
            data = self.manager.sync()

        self.assertEqual(data["items"]["cache-notes"]["kind"], "file")
        self.assertEqual(data["items"]["database-topic"]["kind"], "directory")
        self.assertEqual(data["items"]["cache-notes"]["status"], "raw")
        self.assertIsNone(data["items"]["cache-notes"]["reviewed_at"])
        self.assertEqual(data["version"], 2)
        self.assertTrue(data["items"]["cache-notes"]["content_sha256"])

    def test_review_moves_item_and_sets_timestamp(self) -> None:
        source = self.root / "resource" / "raw" / "cache-notes.md"
        source.write_text("Cache notes", encoding="utf-8")
        self.manager.sync()

        with patch("scripts.resources._now", return_value="2026-07-31T10:00:00+07:00"):
            destination = self.manager.review("cache-notes")

        data = yaml.safe_load(
            (self.root / "resource" / "index.yml").read_text(encoding="utf-8")
        )
        self.assertEqual(destination, self.root / "resource" / "pool" / source.name)
        self.assertEqual(data["items"]["cache-notes"]["status"], "pool")
        self.assertEqual(
            data["items"]["cache-notes"]["reviewed_at"],
            "2026-07-31T10:00:00+07:00",
        )

    def test_complete_requires_reviewed_lesson_then_moves_to_done(self) -> None:
        source = self.root / "resource" / "raw" / "cache-notes.md"
        source.write_text("Cache notes", encoding="utf-8")
        self.manager.sync()
        self.manager.review("cache-notes")
        lesson_dir = self.root / "knowledge" / "demo" / "lessons"
        lesson_dir.mkdir(parents=True)
        (lesson_dir / "cache.md").write_text(
            """---
id: cache
title: Cache
depth: standard
status: review
tags: []
---

## Cache
""",
            encoding="utf-8",
        )

        with patch("scripts.resources._now", return_value="2026-07-31T11:00:00+07:00"):
            destination = self.manager.complete("cache-notes", "demo", "cache")

        item = self.manager.sync()["items"]["cache-notes"]
        self.assertEqual(destination.parent.name, "done")
        self.assertEqual(item["cookbook"], "demo")
        self.assertEqual(item["lesson_id"], "cache")
        self.assertEqual(item["completed_at"], "2026-07-31T11:00:00+07:00")

    def test_complete_rejects_draft_lesson(self) -> None:
        source = self.root / "resource" / "raw" / "cache-notes.md"
        source.write_text("Cache notes", encoding="utf-8")
        self.manager.sync()
        self.manager.review("cache-notes")
        lesson_dir = self.root / "knowledge" / "demo" / "lessons"
        lesson_dir.mkdir(parents=True)
        (lesson_dir / "cache.md").write_text(
            """---
id: cache
title: Cache
depth: standard
status: draft
tags: []
---

## Cache
""",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(BuilderError, "review hoặc complete"):
            self.manager.complete("cache-notes", "demo", "cache")

    def test_inspect_directory_reports_unicode_heading_and_attachment(self) -> None:
        source = self.root / "resource" / "raw" / "unicode-notes"
        source.mkdir()
        (source / "article.md").write_text(
            "# Tiêu đề\n\nNội dung tiếng Việt.\n", encoding="utf-8"
        )
        (source / "diagram.png").write_bytes(b"\x89PNG\r\n")
        self.manager.sync()

        report = self.manager.inspect("unicode-notes")

        self.assertTrue(report["valid"])
        self.assertEqual(report["totals"]["files"], 2)
        self.assertEqual(report["totals"]["attachments"], 1)
        text_file = next(item for item in report["files"] if item["kind"] == "text")
        self.assertEqual(text_file["headings"][0]["title"], "Tiêu đề")

    def test_inspect_rejects_empty_invalid_utf8_and_symlink(self) -> None:
        settings = ResourcePreparationSettings()
        empty = self.root / "empty.md"
        empty.write_text("", encoding="utf-8")
        self.assertFalse(inspect_resource(empty, settings)["valid"])

        invalid = self.root / "invalid.md"
        invalid.write_bytes(b"\xff\xfe")
        self.assertFalse(inspect_resource(invalid, settings)["valid"])

        link = self.root / "link.md"
        link.symlink_to(empty)
        with self.assertRaisesRegex(BuilderError, "symlink"):
            inspect_resource(link, settings)

    def test_tree_hash_is_stable_and_includes_path_and_bytes(self) -> None:
        first = self.root / "first"
        first.mkdir()
        (first / "a.md").write_text("same", encoding="utf-8")
        original = resource_sha256(first)
        self.assertEqual(original, resource_sha256(first))

        (first / "a.md").rename(first / "b.md")
        self.assertNotEqual(original, resource_sha256(first))
        renamed = resource_sha256(first)
        (first / "b.md").write_text("changed", encoding="utf-8")
        self.assertNotEqual(renamed, resource_sha256(first))

    def test_load_migrates_v1_without_changing_identity_or_timestamps(self) -> None:
        source = self.root / "resource" / "raw" / "legacy.md"
        source.write_text("Legacy", encoding="utf-8")
        legacy = {
            "version": 1,
            "items": {
                "legacy": {
                    "source": "resource/raw/legacy.md",
                    "kind": "file",
                    "status": "raw",
                    "created_at": "2026-01-01T00:00:00+07:00",
                    "reviewed_at": None,
                    "completed_at": None,
                    "cookbook": None,
                    "lesson_id": None,
                }
            },
        }
        (self.root / "resource" / "index.yml").write_text(
            yaml.safe_dump(legacy, sort_keys=False), encoding="utf-8"
        )

        migrated = self.manager.sync()

        item = migrated["items"]["legacy"]
        self.assertEqual(migrated["version"], 2)
        self.assertEqual(item["created_at"], "2026-01-01T00:00:00+07:00")
        self.assertIsNone(item["parent_id"])
        self.assertEqual(item["children"], [])
        self.assertEqual(item["content_sha256"], resource_sha256(source))

    def test_sync_rejects_unindexed_archive(self) -> None:
        archive = self.root / "resource" / "archive" / "unknown"
        archive.mkdir()
        (archive / "manifest.yml").write_text("version: 1\n", encoding="utf-8")
        with self.assertRaisesRegex(BuilderError, "không thể tự đăng ký"):
            self.manager.sync()

    def test_verify_and_sync_detect_pool_tampering(self) -> None:
        source = self.root / "resource" / "raw" / "cache-notes.md"
        source.write_text("Cache notes", encoding="utf-8")
        self.manager.sync()
        destination = self.manager.review("cache-notes")
        self.assertTrue(self.manager.verify("cache-notes")["valid"])

        destination.write_text("tampered", encoding="utf-8")
        self.assertFalse(self.manager.verify("cache-notes")["valid"])
        with self.assertRaisesRegex(BuilderError, "Integrity failure"):
            self.manager.sync()

    def test_review_requires_explicit_override_above_soft_limit(self) -> None:
        source = self.root / "resource" / "raw" / "large.md"
        source.write_text("word " * 3001, encoding="utf-8")
        self.manager.sync()
        with self.assertRaisesRegex(BuilderError, "soft_max_words"):
            self.manager.review("large")
        destination = self.manager.review("large", allow_large_single=True)
        self.assertEqual(destination.parent.name, "pool")

    def test_inspect_flags_ai_limit_and_hard_review_requires_reason(self) -> None:
        source = self.root / "resource" / "raw" / "huge.md"
        source.write_text("word " * 50001, encoding="utf-8")
        self.manager.sync()
        report = self.manager.inspect("huge")
        self.assertTrue(report["ai_limit_exceeded"])
        with self.assertRaisesRegex(BuilderError, "cần --reason"):
            self.manager.review("huge", allow_large_single=True)
        destination = self.manager.review(
            "huge",
            allow_large_single=True,
            override_reason="Một chủ đề đồng nhất",
        )
        self.assertEqual(destination.parent.name, "pool")


if __name__ == "__main__":
    unittest.main()

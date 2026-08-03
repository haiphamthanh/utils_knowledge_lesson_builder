from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

from scripts.models import BuilderError
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


if __name__ == "__main__":
    unittest.main()

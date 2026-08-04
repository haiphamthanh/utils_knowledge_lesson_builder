from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

from scripts.models import BuilderError
from scripts.resources import ResourceManager


class ResourcePreparationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()
        self.manager = ResourceManager(self.root)
        self.manager.ensure_layout()
        self.source = self.root / "resource" / "raw" / "system-notes"
        self.source.mkdir()
        (self.source / "a.md").write_text("# A\n\nalpha\n", encoding="utf-8")
        (self.source / "b.txt").write_text("beta\n\ngamma\n", encoding="utf-8")
        (self.source / "diagram.png").write_bytes(b"PNG-data")
        self.manager.sync()
        self.hash = self.manager.inspect("system-notes")["content_sha256"]

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def plan(self) -> dict:
        return {
            "version": 1,
            "resource_id": "system-notes",
            "source_sha256": self.hash,
            "mode": "split",
            "reason": "Hai chủ đề độc lập",
            "parts": [
                {
                    "id": "topic-a",
                    "title": "Topic A",
                    "fragments": [
                        {"path": "a.md", "start_line": 1, "end_line": 3}
                    ],
                    "attachments": ["diagram.png"],
                },
                {
                    "id": "topic-b",
                    "title": "Topic B",
                    "fragments": [
                        {"path": "b.txt", "start_line": 1, "end_line": 3}
                    ],
                    "attachments": [],
                },
            ],
            "archive_only": [],
        }

    def write_plan(self, value: dict, name: str = "plan.yml") -> Path:
        path = self.root / name
        path.write_text(
            yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        return path

    def test_prepare_has_exact_coverage_and_does_not_mutate_resources(self) -> None:
        raw_before = {
            path.relative_to(self.source): path.read_bytes()
            for path in self.source.rglob("*")
            if path.is_file()
        }
        index_before = (self.root / "resource" / "index.yml").read_bytes()

        report = self.manager.prepare("system-notes", self.write_plan(self.plan()))

        self.assertEqual(report["coverage"]["percent"], 100.0)
        self.assertEqual(report["coverage"]["gaps"], 0)
        self.assertEqual(report["coverage"]["overlaps"], 0)
        preparation = self.root / report["directory"]
        self.assertEqual(
            (preparation / "candidates" / "topic-a" / "content.md").read_bytes(),
            (self.source / "a.md").read_bytes(),
        )
        self.assertEqual(
            (preparation / "candidates" / "topic-b" / "content.md").read_bytes(),
            (self.source / "b.txt").read_bytes(),
        )
        self.assertEqual(
            (preparation / "candidates" / "topic-a" / "attachments" / "diagram.png").read_bytes(),
            b"PNG-data",
        )
        self.assertEqual(
            raw_before,
            {
                path.relative_to(self.source): path.read_bytes()
                for path in self.source.rglob("*")
                if path.is_file()
            },
        )
        self.assertEqual(index_before, (self.root / "resource" / "index.yml").read_bytes())
        self.assertFalse(any((self.root / "resource" / "pool").iterdir()))

    def test_prepare_rejects_gap_overlap_range_duplicate_and_stale_hash(self) -> None:
        cases: list[tuple[str, dict, str]] = []

        gap = deepcopy(self.plan())
        gap["parts"][0]["fragments"][0]["end_line"] = 2
        cases.append(("gap", gap, "gaps=1"))

        overlap = deepcopy(self.plan())
        overlap["parts"][1]["fragments"].append(
            {"path": "a.md", "start_line": 3, "end_line": 3}
        )
        cases.append(("overlap", overlap, "overlaps=1"))

        outside = deepcopy(self.plan())
        outside["parts"][0]["fragments"][0]["end_line"] = 99
        cases.append(("outside", outside, "Range ngoài file"))

        duplicate = deepcopy(self.plan())
        duplicate["parts"][1]["id"] = "topic-a"
        cases.append(("duplicate", duplicate, "Part id bị trùng"))

        stale = deepcopy(self.plan())
        stale["source_sha256"] = "0" * 64
        cases.append(("stale", stale, "source_sha256 stale"))

        for name, plan, message in cases:
            with self.subTest(name=name):
                with self.assertRaisesRegex(BuilderError, message):
                    self.manager.prepare("system-notes", self.write_plan(plan, f"{name}.yml"))

    def test_prepare_requires_every_attachment_decision(self) -> None:
        plan = self.plan()
        plan["parts"][0]["attachments"] = []
        with self.assertRaisesRegex(BuilderError, "Attachment chưa được"):
            self.manager.prepare("system-notes", self.write_plan(plan))
        plan["archive_only"] = ["diagram.png"]
        self.assertTrue(
            self.manager.prepare("system-notes", self.write_plan(plan))["valid"]
        )

    def test_large_single_requires_override_and_review_cannot_bypass_preparation(self) -> None:
        large = self.root / "resource" / "raw" / "large.md"
        large.write_text("word " * 8001, encoding="utf-8")
        self.manager.sync()
        source_hash = self.manager.inspect("large")["content_sha256"]
        plan = {
            "version": 1,
            "resource_id": "large",
            "source_sha256": source_hash,
            "mode": "single",
            "reason": "Một chủ đề đồng nhất",
            "parts": [],
        }
        plan_path = self.write_plan(plan, "single.yml")
        with self.assertRaisesRegex(BuilderError, "hard_max_words"):
            self.manager.prepare("large", plan_path)
        self.manager.prepare("large", plan_path, allow_large_single=True)
        with self.assertRaisesRegex(BuilderError, "không được bypass"):
            self.manager.review("large", allow_large_single=True)

    def test_finalize_split_archives_original_and_creates_verified_children(self) -> None:
        preparation = self.manager.prepare("system-notes", self.write_plan(self.plan()))
        original_hash = self.hash

        result = self.manager.finalize(
            "system-notes", preparation["preparation_id"]
        )

        self.assertTrue(result["verification"]["valid"])
        self.assertFalse(self.source.exists())
        parent = self.manager._load()["items"]["system-notes"]
        self.assertEqual(parent["status"], "archive")
        self.assertEqual(parent["children"], ["topic-a", "topic-b"])
        manifest = yaml.safe_load(
            (self.root / parent["manifest"]).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["source_sha256"], original_hash)
        for child_id in parent["children"]:
            child = self.manager._load()["items"][child_id]
            self.assertEqual(child["parent_id"], "system-notes")
            self.assertEqual(child["status"], "pool")
            self.assertTrue(self.manager.verify(child_id)["valid"])

        retry = self.manager.finalize(
            "system-notes", preparation["preparation_id"]
        )
        self.assertTrue(retry["idempotent"])

    def test_finalize_single_moves_verified_original_to_pool(self) -> None:
        single_source = self.root / "resource" / "raw" / "single.md"
        single_source.write_text("one topic\n", encoding="utf-8")
        self.manager.sync()
        source_hash = self.manager.inspect("single")["content_sha256"]
        plan = {
            "version": 1,
            "resource_id": "single",
            "source_sha256": source_hash,
            "mode": "single",
            "reason": "Một chủ đề nhỏ",
            "parts": [],
        }
        preparation = self.manager.prepare("single", self.write_plan(plan, "small.yml"))

        result = self.manager.finalize("single", preparation["preparation_id"])

        self.assertTrue(result["verification"]["valid"])
        self.assertFalse(single_source.exists())
        self.assertEqual(self.manager._load()["items"]["single"]["status"], "pool")

    def test_finalize_collision_never_removes_raw(self) -> None:
        preparation = self.manager.prepare("system-notes", self.write_plan(self.plan()))
        collision = self.root / "resource" / "pool" / "topic-a"
        collision.mkdir()
        (collision / "content.md").write_text("different", encoding="utf-8")

        with self.assertRaisesRegex(BuilderError, "collision"):
            self.manager.finalize("system-notes", preparation["preparation_id"])
        self.assertTrue(self.source.exists())

    def test_finalize_index_failure_keeps_raw_and_retry_is_safe(self) -> None:
        preparation = self.manager.prepare("system-notes", self.write_plan(self.plan()))
        real_save = self.manager._save
        with patch.object(self.manager, "_save", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(OSError, "disk full"):
                self.manager.finalize("system-notes", preparation["preparation_id"])
        self.assertTrue(self.source.exists())

        self.manager._save = real_save
        result = self.manager.finalize("system-notes", preparation["preparation_id"])
        self.assertTrue(result["verification"]["valid"])
        self.assertFalse(self.source.exists())

    def test_finalize_interruption_after_index_removes_raw_on_retry(self) -> None:
        preparation = self.manager.prepare("system-notes", self.write_plan(self.plan()))
        with patch(
            "scripts.resource_preparation.ResourcePreparationEngine._remove_raw",
            side_effect=OSError("interrupted"),
        ):
            with self.assertRaisesRegex(OSError, "interrupted"):
                self.manager.finalize("system-notes", preparation["preparation_id"])
        self.assertTrue(self.source.exists())
        self.assertEqual(
            self.manager._load()["items"]["system-notes"]["status"], "archive"
        )

        retry = self.manager.finalize("system-notes", preparation["preparation_id"])
        self.assertTrue(retry["idempotent"])
        self.assertFalse(self.source.exists())

    def test_verify_detects_tampering_after_split(self) -> None:
        preparation = self.manager.prepare("system-notes", self.write_plan(self.plan()))
        self.manager.finalize("system-notes", preparation["preparation_id"])
        content = self.root / "resource" / "pool" / "topic-a" / "content.md"
        content.write_text("tampered", encoding="utf-8")
        report = self.manager.verify("topic-a")
        self.assertFalse(report["valid"])
        self.assertTrue(any("checksum" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()

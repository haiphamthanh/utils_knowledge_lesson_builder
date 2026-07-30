from pathlib import Path
import tempfile
import unittest

import yaml

from knowledge_builder.authoring import create_lesson
from knowledge_builder.loading import parse_lesson
from knowledge_builder.models import BuilderError


class AuthoringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "templates").mkdir()
        (self.root / "templates" / "lesson.md").write_text(
            """---
id: lesson-id
title: "Tên bài học"
depth: standard
status: draft
tags: []
---

## Tên bài học

### Nhu cầu

Điền nội dung.
""",
            encoding="utf-8",
        )
        cookbook_dir = self.root / "src" / "demo"
        (cookbook_dir / "lessons").mkdir(parents=True)
        (cookbook_dir / "cookbook.yml").write_text(
            "id: demo\ntitle: Demo\n",
            encoding="utf-8",
        )
        (cookbook_dir / "graph.yml").write_text(
            "nodes: {}\nrelations: []\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_lesson_adds_draft_and_graph_node(self) -> None:
        target = create_lesson(
            root=self.root,
            cookbook_id="demo",
            lesson_id="cache",
            title="Cache",
            depth="standard",
        )

        lesson = parse_lesson(target)
        graph = yaml.safe_load(
            (self.root / "src" / "demo" / "graph.yml").read_text(encoding="utf-8")
        )
        self.assertEqual(lesson.id, "cache")
        self.assertEqual(lesson.status, "draft")
        self.assertEqual(graph["nodes"]["cache"]["title"], "Cache")

    def test_create_lesson_never_overwrites_existing_file(self) -> None:
        target = self.root / "src" / "demo" / "lessons" / "cache.md"
        target.write_text("keep me", encoding="utf-8")

        with self.assertRaisesRegex(BuilderError, "đã tồn tại"):
            create_lesson(
                root=self.root,
                cookbook_id="demo",
                lesson_id="cache",
                title="Cache",
                depth="standard",
            )

        self.assertEqual(target.read_text(encoding="utf-8"), "keep me")


if __name__ == "__main__":
    unittest.main()


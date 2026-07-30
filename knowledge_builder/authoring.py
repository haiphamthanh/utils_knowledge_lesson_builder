from __future__ import annotations

from pathlib import Path

import yaml

from knowledge_builder.io_utils import atomic_write
from knowledge_builder.loading import load_yaml, require_slug
from knowledge_builder.models import ALLOWED_DEPTHS, BuilderError


def create_lesson(
    root: Path,
    cookbook_id: str,
    lesson_id: str,
    title: str,
    depth: str,
) -> Path:
    root = root.resolve()
    cookbook_id = require_slug(cookbook_id, "Cookbook id")
    lesson_id = require_slug(lesson_id, "Lesson id")
    title = title.strip()
    if not title:
        raise BuilderError("Lesson title không được để trống")
    if depth not in ALLOWED_DEPTHS:
        raise BuilderError(f"depth phải thuộc {sorted(ALLOWED_DEPTHS)}")

    cookbook_dir = root / "src" / cookbook_id
    cookbook_path = cookbook_dir / "cookbook.yml"
    cookbook = load_yaml(cookbook_path)
    if cookbook.get("id") != cookbook_id:
        raise BuilderError(
            f"id trong {cookbook_path} phải khớp tên thư mục '{cookbook_id}'"
        )

    lesson_template_path = root / "templates" / "lesson.md"
    if not lesson_template_path.is_file():
        raise BuilderError(f"Không tìm thấy lesson template: {lesson_template_path}")
    template = lesson_template_path.read_text(encoding="utf-8")
    parts = template.split("---", 2)
    if len(parts) != 3:
        raise BuilderError(f"Lesson template không hợp lệ: {lesson_template_path}")
    body = parts[2].lstrip().replace("## Tên bài học", f"## {title}", 1)

    lessons_dir = cookbook_dir / "lessons"
    target = lessons_dir / f"{lesson_id}.md"
    if target.exists():
        raise BuilderError(f"Lesson đã tồn tại: {target}")

    graph_path = cookbook_dir / "graph.yml"
    graph = load_yaml(graph_path)
    nodes = graph.get("nodes")
    if not isinstance(nodes, dict):
        raise BuilderError(f"'nodes' phải là mapping trong {graph_path}")
    if lesson_id in nodes:
        raise BuilderError(f"Graph node đã tồn tại: {lesson_id}")
    nodes[lesson_id] = {"title": title}

    metadata = {
        "id": lesson_id,
        "title": title,
        "depth": depth,
        "status": "draft",
        "tags": [],
    }
    lesson_text = (
        "---\n"
        + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False)
        + "---\n\n"
        + body
    )
    graph_text = yaml.safe_dump(graph, allow_unicode=True, sort_keys=False)

    lessons_dir.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("x", encoding="utf-8") as file:
            file.write(lesson_text)
        atomic_write(graph_path, graph_text)
    except Exception:
        if target.exists():
            target.unlink()
        raise
    return target

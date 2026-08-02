from __future__ import annotations

from pathlib import Path

from knowledge_builder.loading import (
    load_lessons,
    load_yaml,
    parse_chapters,
    require_slug,
    require_string,
)
from knowledge_builder.models import (
    BuildPlan,
    BuilderError,
)
from knowledge_builder.validation import validate_graph, validate_path


def create_plan(
    root: Path,
    cookbook_id: str,
    path_id: str | None,
    template_id: str | None,
    format_id: str | None,
    include_optional: bool,
    include_draft: bool,
) -> BuildPlan:
    root = root.resolve()
    settings = load_yaml(root / "config.yml")
    cookbook_id = require_slug(cookbook_id, "Cookbook id")
    cookbook_dir = root / "knowledge" / cookbook_id
    cookbook_path = cookbook_dir / "cookbook.yml"
    cookbook = load_yaml(cookbook_path)
    if cookbook.get("id") != cookbook_id:
        raise BuilderError(
            f"id trong {cookbook_path} phải khớp tên thư mục '{cookbook_id}'"
        )
    require_string(cookbook, "title", cookbook_path)

    resolved_path_id = require_slug(
        path_id or cookbook.get("default_path"), "Learning path id"
    )
    learning_path_path = cookbook_dir / "paths" / f"{resolved_path_id}.yml"
    learning_path = load_yaml(learning_path_path)
    if learning_path.get("id") != resolved_path_id:
        raise BuilderError(
            f"id trong {learning_path_path} phải là '{resolved_path_id}'"
        )
    require_string(learning_path, "title", learning_path_path)

    resolved_template_id = require_slug(
        template_id
        or cookbook.get("template")
        or settings.get("default_template"),
        "Template id",
    )
    template_dir = root / "templates" / resolved_template_id
    template_path = template_dir / "template.yml"
    template = load_yaml(template_path)
    if template.get("id") != resolved_template_id:
        raise BuilderError(f"id trong {template_path} phải là '{resolved_template_id}'")

    resolved_format_id = require_slug(
        format_id
        or cookbook.get("format")
        or settings.get("default_format"),
        "Format id",
    )
    formats = template.get("formats")
    if not isinstance(formats, dict) or resolved_format_id not in formats:
        available = ", ".join(sorted(formats)) if isinstance(formats, dict) else ""
        raise BuilderError(
            f"Template '{resolved_template_id}' không hỗ trợ format "
            f"'{resolved_format_id}'. Có: {available or '(không có)'}"
        )

    lessons = load_lessons(cookbook_dir / "lessons")
    chapters = parse_chapters(learning_path, learning_path_path)
    dependencies = validate_graph(
        load_yaml(cookbook_dir / "graph.yml"),
        lessons,
        cookbook_dir / "graph.yml",
    )
    ordered = validate_path(
        chapters, lessons, dependencies, include_optional, include_draft
    )

    raw_build_dir = settings.get("build_dir", "build")
    if not isinstance(raw_build_dir, str) or not raw_build_dir.strip():
        raise BuilderError("'build_dir' trong config.yml phải là chuỗi")
    build_dir = (root / raw_build_dir).resolve()
    if root not in build_dir.parents:
        raise BuilderError("build_dir phải nằm bên trong project")

    return BuildPlan(
        root=root,
        cookbook_id=cookbook_id,
        cookbook=cookbook,
        path_id=resolved_path_id,
        learning_path=learning_path,
        template_id=resolved_template_id,
        template=template,
        format_id=resolved_format_id,
        lessons=lessons,
        chapters=chapters,
        ordered_lesson_ids=ordered,
        build_dir=build_dir,
    )

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

from scripts.models import BuildPlan, BuilderError


def _format_config(plan: BuildPlan) -> dict[str, Any]:
    formats = plan.template["formats"]
    config = formats[plan.format_id]
    if not isinstance(config, dict):
        raise BuilderError(
            f"Cấu hình format '{plan.format_id}' trong template phải là mapping"
        )
    return config


def _document_options(plan: BuildPlan) -> list[str]:
    toc_depth = plan.template.get("toc_depth", 2)
    if (
        not isinstance(toc_depth, int)
        or isinstance(toc_depth, bool)
        or not 1 <= toc_depth <= 6
    ):
        raise BuilderError("'toc_depth' trong template.yml phải là số từ 1 đến 6")
    number_sections = plan.template.get("number_sections", True)
    if not isinstance(number_sections, bool):
        raise BuilderError("'number_sections' trong template.yml phải là boolean")
    options = ["--table-of-contents", f"--toc-depth={toc_depth}"]
    if number_sections:
        options.append("--number-sections")
    return options


def _resolve_template_asset(plan: BuildPlan, value: str, label: str) -> Path:
    templates_dir = (plan.root / "templates").resolve()
    template_dir = templates_dir / plan.template_id
    resolved = (template_dir / value).resolve()
    if templates_dir not in resolved.parents or not resolved.is_file():
        raise BuilderError(f"{label} không hợp lệ: {resolved}")
    return resolved


def _asset_values(value: object, label: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str) and value:
        return [value]
    if isinstance(value, list) and all(
        isinstance(item, str) and item for item in value
    ):
        return value
    raise BuilderError(f"'{label}' trong template.yml phải là string hoặc list string")


def _chapter_markdown(plan: BuildPlan) -> str:
    selected = set(plan.ordered_lesson_ids)
    blocks: list[str] = []
    for chapter in plan.chapters:
        chapter_lessons = [
            lesson_id
            for lesson_id in chapter.core_lessons + chapter.optional_lessons
            if lesson_id in selected
        ]
        if not chapter_lessons:
            continue
        blocks.append(f"# {chapter.title} {{#{chapter.id}}}")
        if chapter.context:
            blocks.append(chapter.context)
        blocks.append("::: {.chapter-objective}")
        blocks.append("**Sau chương này, người đọc có thể:**")
        blocks.extend(f"- {item}" for item in chapter.objective)
        blocks.append(":::")
        if chapter.out_of_scope:
            blocks.append("**Chưa đào sâu trong chương này:**")
            blocks.extend(f"- {item}" for item in chapter.out_of_scope)
        for lesson_id in chapter_lessons:
            blocks.append(plan.lessons[lesson_id].body.rstrip())
    return "\n\n".join(blocks) + "\n"


def render_source(plan: BuildPlan, destination: Path) -> None:
    metadata = {
        "lang": plan.cookbook.get("language", "vi-VN"),
        "title": plan.cookbook["title"],
        "subtitle": plan.cookbook.get("subtitle", ""),
        "author": plan.cookbook.get("author", ""),
        "date": plan.cookbook.get("edition", ""),
        "description": plan.cookbook.get("description", ""),
        "path-title": plan.learning_path["title"],
    }
    front_matter = yaml.safe_dump(
        metadata, allow_unicode=True, sort_keys=False
    ).strip()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        f"---\n{front_matter}\n---\n\n{_chapter_markdown(plan)}",
        encoding="utf-8",
    )


def build(plan: BuildPlan) -> Path:
    if shutil.which("pandoc") is None:
        raise BuilderError("Không tìm thấy pandoc trong PATH")

    format_config = _format_config(plan)
    extension = format_config.get("extension", plan.format_id)
    if not isinstance(extension, str) or not extension:
        raise BuilderError(f"extension của format '{plan.format_id}' không hợp lệ")

    output_dir = plan.build_dir / plan.cookbook_id / plan.path_id
    work_dir = plan.build_dir / ".work" / plan.cookbook_id / plan.path_id
    source_path = work_dir / "book.md"
    render_source(plan, source_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / (
        f"{plan.cookbook_id}-{plan.path_id}-{plan.template_id}.{extension}"
    )

    command = [
        "pandoc",
        str(source_path),
        "--standalone",
        *_document_options(plan),
        "--top-level-division=chapter",
        f"--resource-path={plan.root}:{plan.root / 'knowledge' / plan.cookbook_id}",
        f"--output={output_path}",
    ]
    target = format_config.get("to")
    if isinstance(target, str) and target:
        command.append(f"--to={target}")

    template_file = format_config.get("template")
    if isinstance(template_file, str) and template_file:
        resolved = _resolve_template_asset(plan, template_file, "Template file")
        command.append(f"--template={resolved}")

    for stylesheet in _asset_values(
        format_config.get("stylesheet"), "stylesheet"
    ):
        resolved = _resolve_template_asset(plan, stylesheet, "Stylesheet")
        command.append(f"--css={resolved}")

    for header_include in _asset_values(
        format_config.get("header_includes"), "header_includes"
    ):
        resolved = _resolve_template_asset(plan, header_include, "Header include")
        command.append(f"--include-in-header={resolved}")

    filters = plan.template.get("filters", [])
    if not isinstance(filters, list):
        raise BuilderError("'filters' trong template.yml phải là danh sách")
    for filter_name in filters:
        if not isinstance(filter_name, str):
            raise BuilderError("Tên filter phải là chuỗi")
        resolved = _resolve_template_asset(plan, filter_name, "Filter")
        command.append(f"--lua-filter={resolved}")

    if format_config.get("embed_resources") is True:
        command.append("--embed-resources")
    pdf_engine = format_config.get("pdf_engine")
    if isinstance(pdf_engine, str) and pdf_engine:
        if shutil.which(pdf_engine) is None:
            raise BuilderError(f"Không tìm thấy PDF engine '{pdf_engine}' trong PATH")
        command.append(f"--pdf-engine={pdf_engine}")

    try:
        subprocess.run(command, cwd=plan.root, check=True)
    except subprocess.CalledProcessError as error:
        raise BuilderError(
            f"Pandoc build thất bại với exit code {error.returncode}"
        ) from error
    return output_path

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

from knowledge_builder.core import BuildPlan, BuilderError


def _format_config(plan: BuildPlan) -> dict[str, Any]:
    formats = plan.template["formats"]
    config = formats[plan.format_id]
    if not isinstance(config, dict):
        raise BuilderError(
            f"Cấu hình format '{plan.format_id}' trong template phải là mapping"
        )
    return config


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

    template_dir = plan.root / "templates" / plan.template_id
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
        "--table-of-contents",
        "--toc-depth=2",
        "--number-sections",
        "--top-level-division=chapter",
        f"--resource-path={plan.root}:{plan.root / 'src' / plan.cookbook_id}",
        f"--output={output_path}",
    ]
    target = format_config.get("to")
    if isinstance(target, str) and target:
        command.append(f"--to={target}")

    template_file = format_config.get("template")
    if isinstance(template_file, str) and template_file:
        resolved = (template_dir / template_file).resolve()
        if template_dir.resolve() not in resolved.parents or not resolved.is_file():
            raise BuilderError(f"Template file không hợp lệ: {resolved}")
        command.append(f"--template={resolved}")

    stylesheet = format_config.get("stylesheet")
    if isinstance(stylesheet, str) and stylesheet:
        resolved = (template_dir / stylesheet).resolve()
        if template_dir.resolve() not in resolved.parents or not resolved.is_file():
            raise BuilderError(f"Stylesheet không hợp lệ: {resolved}")
        command.append(f"--css={resolved}")

    filters = plan.template.get("filters", [])
    if not isinstance(filters, list):
        raise BuilderError("'filters' trong template.yml phải là danh sách")
    for filter_name in filters:
        if not isinstance(filter_name, str):
            raise BuilderError("Tên filter phải là chuỗi")
        resolved = (template_dir / filter_name).resolve()
        if template_dir.resolve() not in resolved.parents or not resolved.is_file():
            raise BuilderError(f"Filter không hợp lệ: {resolved}")
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


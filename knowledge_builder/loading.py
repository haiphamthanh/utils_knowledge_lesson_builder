from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from knowledge_builder.models import (
    ALLOWED_DEPTHS,
    ALLOWED_STATUSES,
    ID_PATTERN,
    BuilderError,
    Chapter,
    Lesson,
)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise BuilderError(f"Không tìm thấy file: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise BuilderError(f"YAML không hợp lệ tại {path}: {error}") from error
    if not isinstance(data, dict):
        raise BuilderError(f"Nội dung YAML phải là mapping: {path}")
    return data


def require_slug(value: object, label: str) -> str:
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        raise BuilderError(
            f"{label} phải viết thường, dùng chữ/số và dấu gạch ngang: {value!r}"
        )
    return value


def require_string(mapping: dict[str, Any], key: str, source: Path) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise BuilderError(f"Thiếu chuỗi bắt buộc '{key}' trong {source}")
    return value.strip()


def string_list(value: object, label: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise BuilderError(f"{label} phải là danh sách chuỗi")
    return tuple(item.strip() for item in value)


def parse_lesson(path: Path) -> Lesson:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise BuilderError(f"Lesson phải bắt đầu bằng YAML front matter: {path}")
    try:
        end = next(
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration as error:
        raise BuilderError(f"Lesson thiếu dấu kết thúc front matter: {path}") from error

    try:
        metadata = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as error:
        raise BuilderError(f"Metadata lesson không hợp lệ tại {path}: {error}") from error
    if not isinstance(metadata, dict):
        raise BuilderError(f"Metadata lesson phải là mapping: {path}")

    lesson_id = require_slug(metadata.get("id"), f"Lesson id trong {path}")
    if path.stem != lesson_id:
        raise BuilderError(
            f"Tên file lesson phải khớp id: '{path.stem}' != '{lesson_id}'"
        )
    title = require_string(metadata, "title", path)
    depth = metadata.get("depth")
    if depth not in ALLOWED_DEPTHS:
        raise BuilderError(
            f"depth của '{lesson_id}' phải thuộc {sorted(ALLOWED_DEPTHS)}"
        )
    status = metadata.get("status")
    if status not in ALLOWED_STATUSES:
        raise BuilderError(
            f"status của '{lesson_id}' phải thuộc {sorted(ALLOWED_STATUSES)}"
        )
    tags = string_list(metadata.get("tags"), f"tags của '{lesson_id}'")
    body = "\n".join(lines[end + 1 :]).strip() + "\n"
    if not body.startswith("## "):
        raise BuilderError(
            f"Phần nội dung của '{lesson_id}' phải bắt đầu bằng heading cấp 2 (##)"
        )
    return Lesson(lesson_id, title, depth, status, tags, path, body)


def load_lessons(lessons_dir: Path) -> dict[str, Lesson]:
    if not lessons_dir.is_dir():
        raise BuilderError(f"Không tìm thấy thư mục lessons: {lessons_dir}")
    lessons: dict[str, Lesson] = {}
    for path in sorted(lessons_dir.glob("*.md")):
        lesson = parse_lesson(path)
        if lesson.id in lessons:
            raise BuilderError(f"Lesson id bị trùng: {lesson.id}")
        lessons[lesson.id] = lesson
    if not lessons:
        raise BuilderError(f"Cookbook chưa có lesson nào: {lessons_dir}")
    return lessons


def parse_chapters(
    learning_path: dict[str, Any], source: Path
) -> tuple[Chapter, ...]:
    raw_chapters = learning_path.get("chapters")
    if not isinstance(raw_chapters, list) or not raw_chapters:
        raise BuilderError(f"'chapters' phải là danh sách không rỗng trong {source}")

    chapters: list[Chapter] = []
    seen_chapters: set[str] = set()
    for raw in raw_chapters:
        if not isinstance(raw, dict):
            raise BuilderError(f"Mỗi chapter phải là mapping trong {source}")
        chapter_id = require_slug(raw.get("id"), f"Chapter id trong {source}")
        if chapter_id in seen_chapters:
            raise BuilderError(f"Chapter id bị trùng: {chapter_id}")
        seen_chapters.add(chapter_id)
        title = require_string(raw, "title", source)
        objective = string_list(raw.get("objective"), f"objective của '{chapter_id}'")
        if not objective:
            raise BuilderError(f"Chapter '{chapter_id}' phải có objective")
        chapters.append(
            Chapter(
                id=chapter_id,
                title=title,
                objective=objective,
                context=str(raw.get("context", "")).strip(),
                out_of_scope=string_list(
                    raw.get("out_of_scope"), f"out_of_scope của '{chapter_id}'"
                ),
                core_lessons=string_list(
                    raw.get("lessons"), f"lessons của '{chapter_id}'"
                ),
                optional_lessons=string_list(
                    raw.get("optional_lessons"),
                    f"optional_lessons của '{chapter_id}'",
                ),
            )
        )
    return tuple(chapters)


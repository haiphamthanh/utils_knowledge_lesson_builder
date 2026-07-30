from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALLOWED_DEPTHS = {"overview", "standard", "deep-dive"}
ALLOWED_STATUSES = {"draft", "review", "complete", "deprecated"}
ALLOWED_RELATIONS = {
    "requires",
    "builds_on",
    "part_of",
    "component_of",
    "explains",
    "applies",
    "contrasts_with",
    "related_to",
    "leads_to",
}


class BuilderError(Exception):
    """A user-facing configuration, validation, or build error."""


@dataclass(frozen=True)
class Lesson:
    id: str
    title: str
    depth: str
    status: str
    tags: tuple[str, ...]
    path: Path
    body: str


@dataclass(frozen=True)
class Chapter:
    id: str
    title: str
    objective: tuple[str, ...]
    context: str
    out_of_scope: tuple[str, ...]
    core_lessons: tuple[str, ...]
    optional_lessons: tuple[str, ...]


@dataclass(frozen=True)
class BuildPlan:
    root: Path
    cookbook_id: str
    cookbook: dict[str, Any]
    path_id: str
    learning_path: dict[str, Any]
    template_id: str
    template: dict[str, Any]
    format_id: str
    lessons: dict[str, Lesson]
    chapters: tuple[Chapter, ...]
    ordered_lesson_ids: tuple[str, ...]
    build_dir: Path


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
            index for index, line in enumerate(lines[1:], start=1)
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


def validate_graph(
    graph: dict[str, Any], lessons: dict[str, Lesson], source: Path
) -> dict[str, set[str]]:
    raw_nodes = graph.get("nodes")
    if not isinstance(raw_nodes, dict):
        raise BuilderError(f"'nodes' phải là mapping trong {source}")
    node_ids = set(raw_nodes)
    lesson_ids = set(lessons)
    if node_ids != lesson_ids:
        missing = sorted(lesson_ids - node_ids)
        unknown = sorted(node_ids - lesson_ids)
        details = []
        if missing:
            details.append(f"thiếu nodes: {', '.join(missing)}")
        if unknown:
            details.append(f"nodes không có lesson: {', '.join(unknown)}")
        raise BuilderError(f"Graph không đồng bộ ({'; '.join(details)}): {source}")

    dependencies = {lesson_id: set() for lesson_id in lesson_ids}
    relations = graph.get("relations", [])
    if not isinstance(relations, list):
        raise BuilderError(f"'relations' phải là danh sách trong {source}")
    seen: set[tuple[str, str, str]] = set()
    for relation in relations:
        if not isinstance(relation, dict):
            raise BuilderError(f"Mỗi relation phải là mapping trong {source}")
        from_id = relation.get("from")
        to_id = relation.get("to")
        relation_type = relation.get("type")
        if from_id not in lesson_ids or to_id not in lesson_ids:
            raise BuilderError(
                f"Relation tham chiếu lesson không tồn tại: {from_id} -> {to_id}"
            )
        if from_id == to_id:
            raise BuilderError(f"Relation không được tự tham chiếu: {from_id}")
        if relation_type not in ALLOWED_RELATIONS:
            raise BuilderError(
                f"Relation type '{relation_type}' không hợp lệ; "
                f"dùng một trong {sorted(ALLOWED_RELATIONS)}"
            )
        key = (from_id, to_id, relation_type)
        if key in seen:
            raise BuilderError(f"Relation bị trùng: {from_id} -> {to_id} ({relation_type})")
        seen.add(key)
        if relation_type == "requires":
            dependencies[from_id].add(to_id)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, trail: tuple[str, ...]) -> None:
        if node in visiting:
            cycle_start = trail.index(node)
            cycle = trail[cycle_start:] + (node,)
            raise BuilderError(f"Dependency cycle: {' -> '.join(cycle)}")
        if node in visited:
            return
        visiting.add(node)
        for dependency in sorted(dependencies[node]):
            visit(dependency, trail + (node,))
        visiting.remove(node)
        visited.add(node)

    for node in sorted(dependencies):
        visit(node, ())
    return dependencies


def validate_path(
    chapters: tuple[Chapter, ...],
    lessons: dict[str, Lesson],
    dependencies: dict[str, set[str]],
    include_optional: bool,
    include_draft: bool,
) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    core_ids = {
        lesson_id for chapter in chapters for lesson_id in chapter.core_lessons
    }
    optional_ids = {
        lesson_id for chapter in chapters for lesson_id in chapter.optional_lessons
    }
    if core_ids & optional_ids:
        overlap = ", ".join(sorted(core_ids & optional_ids))
        raise BuilderError(f"Lesson vừa là core vừa là optional: {overlap}")
    referenced_ids = core_ids | optional_ids
    unknown_ids = referenced_ids - set(lessons)
    if unknown_ids:
        raise BuilderError(
            f"Path tham chiếu lesson không tồn tại: {', '.join(sorted(unknown_ids))}"
        )

    for chapter in chapters:
        selected = list(chapter.core_lessons)
        if include_optional:
            selected.extend(chapter.optional_lessons)
        for lesson_id in selected:
            if lesson_id in seen:
                raise BuilderError(f"Lesson bị lặp trong path: {lesson_id}")
            lesson = lessons[lesson_id]
            if lesson.status == "deprecated":
                raise BuilderError(f"Path không được chứa lesson deprecated: {lesson_id}")
            if lesson.status == "draft" and not include_draft:
                raise BuilderError(
                    f"Lesson '{lesson_id}' đang draft; dùng --include-draft để build"
                )
            missing_before = dependencies[lesson_id] - seen
            if missing_before:
                raise BuilderError(
                    f"Lesson '{lesson_id}' xuất hiện trước prerequisite: "
                    f"{', '.join(sorted(missing_before))}"
                )
            if lesson.depth == "overview":
                deep_dependencies = [
                    item for item in dependencies[lesson_id]
                    if lessons[item].depth == "deep-dive"
                ]
                if deep_dependencies:
                    raise BuilderError(
                        f"Overview '{lesson_id}' không được phụ thuộc deep-dive: "
                        f"{', '.join(sorted(deep_dependencies))}"
                    )
            seen.add(lesson_id)
            ordered.append(lesson_id)

    for lesson_id in core_ids:
        optional_dependencies = dependencies[lesson_id] & optional_ids
        if optional_dependencies:
            raise BuilderError(
                f"Core lesson '{lesson_id}' phụ thuộc optional lesson: "
                f"{', '.join(sorted(optional_dependencies))}"
            )
    return tuple(ordered)


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
    settings_path = root / "config.yml"
    settings = load_yaml(settings_path)
    cookbook_id = require_slug(cookbook_id, "Cookbook id")
    cookbook_dir = root / "src" / cookbook_id
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

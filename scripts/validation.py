from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.models import (
    ALLOWED_RELATIONS,
    BuilderError,
    Chapter,
    Lesson,
)


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
            raise BuilderError(
                f"Relation bị trùng: {from_id} -> {to_id} ({relation_type})"
            )
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
                    item
                    for item in dependencies[lesson_id]
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

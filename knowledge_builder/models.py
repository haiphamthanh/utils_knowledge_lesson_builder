from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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


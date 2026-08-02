from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any

import yaml

from knowledge_builder.io_utils import atomic_write
from knowledge_builder.loading import parse_lesson, require_slug
from knowledge_builder.models import BuilderError


RESOURCE_STATUSES = ("raw", "pool", "done")
PUBLISHABLE_LESSON_STATUSES = {"review", "complete"}


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _item_id(name: str) -> str:
    stem = Path(name).stem if "." in name else name
    normalized = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    return require_slug(normalized, f"Resource id từ tên '{name}'")


class ResourceManager:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.resource_dir = self.root / "resource"
        self.index_path = self.resource_dir / "index.yml"

    def ensure_layout(self) -> None:
        self.resource_dir.mkdir(parents=True, exist_ok=True)
        for status in RESOURCE_STATUSES:
            (self.resource_dir / status).mkdir(exist_ok=True)
        if not self.index_path.exists():
            atomic_write(self.index_path, "version: 1\nitems: {}\n")

    def _load(self) -> dict[str, Any]:
        self.ensure_layout()
        try:
            data = yaml.safe_load(self.index_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            raise BuilderError(f"YAML không hợp lệ tại {self.index_path}: {error}") from error
        if not isinstance(data, dict) or data.get("version") != 1:
            raise BuilderError(f"{self.index_path} phải có version: 1")
        items = data.get("items")
        if not isinstance(items, dict):
            raise BuilderError(f"'items' phải là mapping trong {self.index_path}")
        return data

    def _save(self, data: dict[str, Any]) -> None:
        atomic_write(
            self.index_path,
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        )

    def _discover(self) -> dict[str, tuple[str, Path]]:
        discovered: dict[str, tuple[str, Path]] = {}
        for status in RESOURCE_STATUSES:
            directory = self.resource_dir / status
            for path in sorted(directory.iterdir()):
                if path.name.startswith("."):
                    continue
                if path.name in discovered:
                    previous_status, _ = discovered[path.name]
                    raise BuilderError(
                        f"Resource name bị trùng giữa '{previous_status}' và "
                        f"'{status}': {path.name}"
                    )
                discovered[path.name] = (status, path)
        return discovered

    def sync(self) -> dict[str, Any]:
        data = self._load()
        items: dict[str, Any] = data["items"]
        discovered = self._discover()
        ids_by_name: dict[str, str] = {}

        for item_id, item in items.items():
            require_slug(item_id, "Resource id")
            if not isinstance(item, dict):
                raise BuilderError(f"Resource '{item_id}' phải là mapping")
            source = item.get("source")
            if not isinstance(source, str) or not source:
                raise BuilderError(f"Resource '{item_id}' thiếu source")
            name = Path(source).name
            if name in ids_by_name:
                raise BuilderError(f"Nhiều resource dùng cùng tên: {name}")
            ids_by_name[name] = item_id

        now = _now()
        seen_ids: set[str] = set()
        for name, (status, path) in discovered.items():
            item_id = ids_by_name.get(name) or _item_id(name)
            if item_id in seen_ids:
                raise BuilderError(f"Resource id bị trùng sau normalize: {item_id}")
            seen_ids.add(item_id)
            item = items.get(item_id)
            if item is None:
                if item_id in items:
                    raise BuilderError(
                        f"Resource id '{item_id}' đã dùng cho item khác"
                    )
                item = {
                    "source": str(path.relative_to(self.root)),
                    "kind": "directory" if path.is_dir() else "file",
                    "status": status,
                    "created_at": now,
                    "reviewed_at": None,
                    "completed_at": None,
                    "cookbook": None,
                    "lesson_id": None,
                }
                items[item_id] = item
            else:
                item["source"] = str(path.relative_to(self.root))
                item["kind"] = "directory" if path.is_dir() else "file"
                item["status"] = status
            if status in {"pool", "done"} and not item.get("reviewed_at"):
                item["reviewed_at"] = now
            if status == "done" and not item.get("completed_at"):
                item["completed_at"] = now

        missing = sorted(set(items) - seen_ids)
        if missing:
            raise BuilderError(
                "Index tham chiếu resource không còn tồn tại: " + ", ".join(missing)
            )
        self._save(data)
        return data

    def list_items(self, status: str | None = None) -> list[dict[str, Any]]:
        if status is not None and status not in RESOURCE_STATUSES:
            raise BuilderError(f"status phải thuộc {RESOURCE_STATUSES}")
        items = self.sync()["items"]
        result = []
        for item_id, item in items.items():
            if status is None or item["status"] == status:
                result.append({"id": item_id, **item})
        return sorted(result, key=lambda item: item["id"])

    def review(self, item_id: str) -> Path:
        item_id = require_slug(item_id, "Resource id")
        data = self.sync()
        item = self._get_item(data, item_id)
        if item["status"] != "raw":
            raise BuilderError(
                f"Resource '{item_id}' phải ở raw, hiện tại là {item['status']}"
            )
        destination = self.resource_dir / "pool" / Path(item["source"]).name
        return self._move(data, item_id, item, destination, reviewed_at=_now())

    def complete(self, item_id: str, cookbook_id: str, lesson_id: str) -> Path:
        item_id = require_slug(item_id, "Resource id")
        cookbook_id = require_slug(cookbook_id, "Cookbook id")
        lesson_id = require_slug(lesson_id, "Lesson id")
        data = self.sync()
        item = self._get_item(data, item_id)
        if item["status"] != "pool":
            raise BuilderError(
                f"Resource '{item_id}' phải ở pool, hiện tại là {item['status']}"
            )

        lesson_path = (
            self.root / "knowledge" / cookbook_id / "lessons" / f"{lesson_id}.md"
        )
        if not lesson_path.is_file():
            raise BuilderError(f"Không tìm thấy lesson đích: {lesson_path}")
        lesson = parse_lesson(lesson_path)
        if lesson.status not in PUBLISHABLE_LESSON_STATUSES:
            raise BuilderError(
                f"Lesson '{lesson_id}' phải ở review hoặc complete trước khi "
                "resource được chuyển sang done"
            )

        destination = self.resource_dir / "done" / Path(item["source"]).name
        return self._move(
            data,
            item_id,
            item,
            destination,
            completed_at=_now(),
            cookbook=cookbook_id,
            lesson_id=lesson_id,
        )

    def _get_item(self, data: dict[str, Any], item_id: str) -> dict[str, Any]:
        item = data["items"].get(item_id)
        if not isinstance(item, dict):
            raise BuilderError(f"Không tìm thấy resource: {item_id}")
        return item

    def _move(
        self,
        data: dict[str, Any],
        item_id: str,
        item: dict[str, Any],
        destination: Path,
        **updates: Any,
    ) -> Path:
        source = self.root / item["source"]
        if not source.exists():
            raise BuilderError(f"Không tìm thấy resource source: {source}")
        if destination.exists():
            raise BuilderError(f"Destination đã tồn tại: {destination}")

        source.rename(destination)
        old_item = dict(item)
        try:
            item["source"] = str(destination.relative_to(self.root))
            item["status"] = destination.parent.name
            item.update(updates)
            self._save(data)
        except Exception:
            destination.rename(source)
            data["items"][item_id] = old_item
            raise
        return destination


def items_as_json(items: list[dict[str, Any]]) -> str:
    return json.dumps(items, ensure_ascii=False, indent=2)


def items_as_table(items: list[dict[str, Any]]) -> str:
    if not items:
        return "Không có resource phù hợp."
    rows = ["ID\tSTATUS\tKIND\tSOURCE"]
    rows.extend(
        f"{item['id']}\t{item['status']}\t{item['kind']}\t{item['source']}"
        for item in items
    )
    return "\n".join(rows)

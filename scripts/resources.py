from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any

import yaml

from scripts.io_utils import atomic_write
from scripts.loading import parse_lesson, require_slug
from scripts.models import BuilderError
from scripts.resource_integrity import (
    inspect_resource,
    load_resource_settings,
    resource_sha256,
)


RESOURCE_STATUSES = ("raw", "archive", "pool", "done")
IMMUTABLE_STATUSES = {"archive", "pool", "done"}
PUBLISHABLE_LESSON_STATUSES = {"review", "complete"}
INDEX_VERSION = 2


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _item_id(name: str) -> str:
    stem = Path(name).stem if "." in name else name
    normalized = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    return require_slug(normalized, f"Resource id từ tên '{name}'")


def _v2_defaults() -> dict[str, Any]:
    return {
        "content_sha256": None,
        "prepared_at": None,
        "parent_id": None,
        "children": [],
        "manifest": None,
        "preparation_id": None,
    }


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
            atomic_write(self.index_path, "version: 2\nitems: {}\n")

    def _load(self) -> dict[str, Any]:
        self.ensure_layout()
        try:
            data = yaml.safe_load(self.index_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            raise BuilderError(f"YAML không hợp lệ tại {self.index_path}: {error}") from error
        if not isinstance(data, dict) or data.get("version") not in {1, 2}:
            raise BuilderError(f"{self.index_path} phải có version: 1 hoặc 2")
        items = data.get("items")
        if not isinstance(items, dict):
            raise BuilderError(f"'items' phải là mapping trong {self.index_path}")

        changed = data["version"] == 1
        for item_id, item in items.items():
            if not isinstance(item, dict):
                raise BuilderError(f"Resource '{item_id}' phải là mapping")
            for key, value in _v2_defaults().items():
                if key not in item:
                    item[key] = list(value) if isinstance(value, list) else value
                    changed = True
            if item["content_sha256"] is None:
                source = item.get("source")
                path = self.root / source if isinstance(source, str) else None
                if path is not None and path.exists():
                    item["content_sha256"] = resource_sha256(path)
                    changed = True
        data["version"] = INDEX_VERSION
        if changed:
            self._save(data)
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
            actual_hash = resource_sha256(path)
            if item is None:
                if status == "archive":
                    raise BuilderError(
                        f"Archive '{name}' chưa có manifest/index hợp lệ; "
                        "không thể tự đăng ký bằng sync"
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
                    **_v2_defaults(),
                }
                item["content_sha256"] = actual_hash
                items[item_id] = item
            else:
                expected_hash = item.get("content_sha256")
                if status in IMMUTABLE_STATUSES and expected_hash not in {None, actual_hash}:
                    raise BuilderError(
                        f"Integrity failure cho resource '{item_id}': "
                        "content_sha256 không khớp"
                    )
                item["source"] = str(path.relative_to(self.root))
                item["kind"] = "directory" if path.is_dir() else "file"
                item["status"] = status
                item["content_sha256"] = actual_hash
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

    def inspect(self, item_id: str) -> dict[str, Any]:
        item_id = require_slug(item_id, "Resource id")
        data = self.sync()
        item = self._get_item(data, item_id)
        if item["status"] != "raw":
            raise BuilderError(f"Chỉ inspect resource ở raw: {item_id}")
        report = inspect_resource(
            self.root / item["source"], load_resource_settings(self.root)
        )
        return {"id": item_id, "status": item["status"], **report}

    def verify(self, item_id: str) -> dict[str, Any]:
        item_id = require_slug(item_id, "Resource id")
        data = self._load()
        item = self._get_item(data, item_id)
        source = self.root / item["source"]
        errors: list[str] = []
        if not source.exists():
            errors.append(f"Source không tồn tại: {item['source']}")
            actual_hash = None
        else:
            try:
                actual_hash = resource_sha256(source)
            except BuilderError as error:
                errors.append(str(error))
                actual_hash = None
        expected_hash = item.get("content_sha256")
        if not expected_hash:
            errors.append("Index chưa có content_sha256")
        elif actual_hash != expected_hash:
            errors.append("content_sha256 không khớp index")
        return {
            "id": item_id,
            "status": item.get("status"),
            "source": item.get("source"),
            "expected_sha256": expected_hash,
            "actual_sha256": actual_hash,
            "errors": errors,
            "valid": not errors,
        }

    def review(self, item_id: str, allow_large_single: bool = False) -> Path:
        item_id = require_slug(item_id, "Resource id")
        data = self.sync()
        item = self._get_item(data, item_id)
        if item["status"] != "raw":
            raise BuilderError(
                f"Resource '{item_id}' phải ở raw, hiện tại là {item['status']}"
            )
        report = inspect_resource(
            self.root / item["source"], load_resource_settings(self.root)
        )
        if not report["valid"]:
            raise BuilderError("Resource không hợp lệ: " + "; ".join(report["errors"]))
        if report["split_review_required"] and not allow_large_single:
            raise BuilderError(
                "Resource vượt soft_max_words; dùng resource prepare hoặc "
                "--allow-large-single sau khi đã review ngữ nghĩa"
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

        lesson_path = self.root / "knowledge" / cookbook_id / "lessons" / f"{lesson_id}.md"
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
            data, item_id, item, destination, completed_at=_now(),
            cookbook=cookbook_id, lesson_id=lesson_id,
        )

    def _get_item(self, data: dict[str, Any], item_id: str) -> dict[str, Any]:
        item = data["items"].get(item_id)
        if not isinstance(item, dict):
            raise BuilderError(f"Không tìm thấy resource: {item_id}")
        return item

    def _move(
        self, data: dict[str, Any], item_id: str, item: dict[str, Any],
        destination: Path, **updates: Any,
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


def report_as_json(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2)


def report_as_table(report: dict[str, Any]) -> str:
    state = "PASS" if report["valid"] else "FAIL"
    rows = [f"ID\t{report['id']}", f"STATUS\t{state}"]
    if "totals" in report:
        totals = report["totals"]
        rows.append(
            "TOTALS\t"
            f"{totals['files']} files, {totals['lines']} lines, "
            f"{totals['words']} words, {totals['bytes']} bytes"
        )
        rows.append(f"SHA256\t{report['content_sha256']}")
    else:
        rows.extend(
            [
                f"EXPECTED\t{report['expected_sha256']}",
                f"ACTUAL\t{report['actual_sha256']}",
            ]
        )
    for error in report.get("errors", []):
        rows.append(f"ERROR\t{error}")
    for warning in report.get("warnings", []):
        rows.append(f"WARNING\t{warning}")
    return "\n".join(rows)


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

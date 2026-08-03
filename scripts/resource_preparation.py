from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
from typing import Any

import yaml

from scripts.io_utils import atomic_write
from scripts.loading import require_slug
from scripts.models import BuilderError
from scripts.resource_integrity import inspect_resource, load_resource_settings


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise BuilderError(f"Không thể đọc plan YAML {path}: {error}") from error
    if not isinstance(value, dict):
        raise BuilderError("Split plan phải là YAML mapping")
    return value


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_plan(plan: dict[str, Any]) -> str:
    return yaml.safe_dump(plan, allow_unicode=True, sort_keys=True)


def _string_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise BuilderError(f"'{field}' phải là list string")
    return value


class ResourcePreparationEngine:
    def __init__(self, manager: Any) -> None:
        self.manager = manager
        self.root = manager.root

    def prepare(
        self, item_id: str, plan_path: Path, allow_large_single: bool = False
    ) -> dict[str, Any]:
        item_id = require_slug(item_id, "Resource id")
        data = self.manager.sync()
        item = self.manager._get_item(data, item_id)
        if item["status"] != "raw":
            raise BuilderError(f"Resource '{item_id}' phải ở raw để prepare")
        source = self.root / item["source"]
        settings = load_resource_settings(self.root)
        inventory = inspect_resource(source, settings)
        if not inventory["valid"]:
            raise BuilderError("Resource không hợp lệ: " + "; ".join(inventory["errors"]))

        plan = _load_yaml(plan_path.resolve())
        normalized, part_material = self._validate_plan(
            item_id, source, inventory, plan, data, allow_large_single
        )
        canonical = _canonical_plan(normalized)
        preparation_id = _sha256(
            (inventory["content_sha256"] + "\0" + canonical).encode("utf-8")
        )[:16]
        target = (
            self.root / "build" / "resource-preparation" / item_id / preparation_id
        )
        if target.exists():
            shutil.rmtree(target)
        candidates = target / "candidates"
        candidates.mkdir(parents=True)

        outputs: list[dict[str, Any]] = []
        for part, fragments in part_material:
            part_dir = candidates / part["id"]
            part_dir.mkdir()
            content = b"".join(fragment["bytes"] for fragment in fragments)
            content_path = part_dir / "content.md"
            content_path.write_bytes(content)
            provenance = {
                "version": 1,
                "parent_id": item_id,
                "source_sha256": inventory["content_sha256"],
                "part_id": part["id"],
                "title": part["title"],
                "fragments": [
                    {
                        "path": fragment["path"],
                        "start_line": fragment["start_line"],
                        "end_line": fragment["end_line"],
                        "sha256": _sha256(fragment["bytes"]),
                    }
                    for fragment in fragments
                ],
                "attachments": part["attachments"],
                "content_sha256": _sha256(content),
            }
            atomic_write(
                part_dir / "provenance.yml",
                yaml.safe_dump(provenance, allow_unicode=True, sort_keys=False),
            )
            for relative in part["attachments"]:
                attachment_target = part_dir / "attachments" / relative
                attachment_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self._source_path(source, relative), attachment_target)
            outputs.append(
                {
                    "id": part["id"],
                    "title": part["title"],
                    "content_sha256": provenance["content_sha256"],
                    "word_count": part["word_count"],
                    "fragments": len(fragments),
                    "attachments": len(part["attachments"]),
                }
            )

        report = {
            "version": 1,
            "preparation_id": preparation_id,
            "resource_id": item_id,
            "mode": normalized["mode"],
            "source_sha256": inventory["content_sha256"],
            "coverage": {
                "total_lines": inventory["totals"]["lines"],
                "assigned_lines": inventory["totals"]["lines"],
                "percent": 100.0,
                "gaps": 0,
                "overlaps": 0,
            },
            "archive_only": normalized.get("archive_only", []),
            "outputs": outputs,
            "valid": True,
        }
        atomic_write(target / "plan.yml", canonical)
        atomic_write(
            target / "report.yml",
            yaml.safe_dump(report, allow_unicode=True, sort_keys=False),
        )
        return {**report, "directory": str(target.relative_to(self.root))}

    def _validate_plan(
        self,
        item_id: str,
        source: Path,
        inventory: dict[str, Any],
        plan: dict[str, Any],
        data: dict[str, Any],
        allow_large_single: bool,
    ) -> tuple[dict[str, Any], list[tuple[dict[str, Any], list[dict[str, Any]]]]]:
        if plan.get("version") != 1:
            raise BuilderError("Plan phải có version: 1")
        if plan.get("resource_id") != item_id:
            raise BuilderError("resource_id trong plan không khớp")
        if plan.get("source_sha256") != inventory["content_sha256"]:
            raise BuilderError("source_sha256 stale hoặc không khớp resource")
        mode = plan.get("mode")
        if mode not in {"single", "split"}:
            raise BuilderError("mode phải là single hoặc split")
        reason = plan.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise BuilderError("Plan phải có reason")
        if mode == "single":
            if plan.get("parts"):
                raise BuilderError("Plan single không được khai báo parts")
            if inventory["hard_split_required"] and not allow_large_single:
                raise BuilderError(
                    "Resource vượt hard_max_words; cần split hoặc "
                    "--allow-large-single với lý do đã được xác nhận"
                )
            return (
                {
                    "version": 1,
                    "resource_id": item_id,
                    "source_sha256": inventory["content_sha256"],
                    "mode": "single",
                    "reason": reason.strip(),
                    "parts": [],
                    "archive_only": [],
                },
                [],
            )

        parts = plan.get("parts")
        if not isinstance(parts, list) or len(parts) < 2:
            raise BuilderError("Plan split phải có ít nhất hai parts")
        text_files = {
            entry["path"]: entry for entry in inventory["files"] if entry["kind"] == "text"
        }
        attachments = {
            entry["path"] for entry in inventory["files"] if entry["kind"] == "attachment"
        }
        coverage = {
            path: [0] * entry["line_count"] for path, entry in text_files.items()
        }
        existing_ids = set(data["items"])
        seen_ids: set[str] = set()
        assigned_attachments: set[str] = set()
        normalized_parts: list[dict[str, Any]] = []
        material: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []

        for raw_part in parts:
            if not isinstance(raw_part, dict):
                raise BuilderError("Mỗi part phải là mapping")
            part_id = require_slug(raw_part.get("id"), "Part id")
            if part_id in seen_ids or part_id in existing_ids:
                raise BuilderError(f"Part id bị trùng index/plan: {part_id}")
            if (self.root / "resource" / "pool" / part_id).exists():
                raise BuilderError(f"Part id đã tồn tại trên filesystem: {part_id}")
            seen_ids.add(part_id)
            title = raw_part.get("title")
            if not isinstance(title, str) or not title.strip():
                raise BuilderError(f"Part '{part_id}' thiếu title")
            raw_fragments = raw_part.get("fragments")
            if not isinstance(raw_fragments, list) or not raw_fragments:
                raise BuilderError(f"Part '{part_id}' phải có fragments")
            fragments: list[dict[str, Any]] = []
            word_count = 0
            for fragment in raw_fragments:
                if not isinstance(fragment, dict):
                    raise BuilderError("Fragment phải là mapping")
                relative = fragment.get("path")
                start = fragment.get("start_line")
                end = fragment.get("end_line")
                if relative not in text_files:
                    raise BuilderError(f"Fragment tham chiếu text file không hợp lệ: {relative}")
                if not isinstance(start, int) or not isinstance(end, int):
                    raise BuilderError("start_line/end_line phải là số nguyên")
                line_count = text_files[relative]["line_count"]
                if start < 1 or end < start or end > line_count:
                    raise BuilderError(
                        f"Range ngoài file {relative}: {start}-{end}/{line_count}"
                    )
                lines = self._source_path(source, relative).read_bytes().splitlines(keepends=True)
                raw_bytes = b"".join(lines[start - 1 : end])
                word_count += len(raw_bytes.decode("utf-8").split())
                for index in range(start - 1, end):
                    coverage[relative][index] += 1
                fragments.append(
                    {"path": relative, "start_line": start, "end_line": end, "bytes": raw_bytes}
                )
            part_attachments = _string_list(raw_part.get("attachments", []), "attachments")
            for relative in part_attachments:
                if relative not in attachments:
                    raise BuilderError(f"Attachment không hợp lệ: {relative}")
                assigned_attachments.add(relative)
            normalized_part = {
                "id": part_id,
                "title": title.strip(),
                "fragments": [
                    {key: fragment[key] for key in ("path", "start_line", "end_line")}
                    for fragment in fragments
                ],
                "attachments": part_attachments,
                "word_count": word_count,
            }
            normalized_parts.append(normalized_part)
            material.append((normalized_part, fragments))

        gaps = sum(value == 0 for values in coverage.values() for value in values)
        overlaps = sum(value > 1 for values in coverage.values() for value in values)
        if gaps or overlaps:
            raise BuilderError(f"Coverage không hợp lệ: gaps={gaps}, overlaps={overlaps}")
        archive_only = set(_string_list(plan.get("archive_only", []), "archive_only"))
        if not archive_only <= attachments:
            raise BuilderError("archive_only chứa attachment không hợp lệ")
        missing_attachments = attachments - assigned_attachments - archive_only
        if missing_attachments:
            raise BuilderError(
                "Attachment chưa được copy hoặc đánh dấu archive-only: "
                + ", ".join(sorted(missing_attachments))
            )
        normalized = {
            "version": 1,
            "resource_id": item_id,
            "source_sha256": inventory["content_sha256"],
            "mode": "split",
            "reason": reason.strip(),
            "parts": normalized_parts,
            "archive_only": sorted(archive_only),
        }
        return normalized, material

    @staticmethod
    def _source_path(source: Path, relative: str) -> Path:
        return source if source.is_file() and relative == source.name else source / relative

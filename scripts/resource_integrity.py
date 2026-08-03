from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Any

import yaml

from scripts.models import BuilderError


DEFAULT_TEXT_EXTENSIONS = (".md", ".markdown", ".txt")
DEFAULT_SOFT_MAX_WORDS = 3_000
DEFAULT_HARD_MAX_WORDS = 8_000
DEFAULT_MAX_AI_WORDS = 50_000
WORD_PATTERN = re.compile(r"\b[\w'-]+\b", re.UNICODE)
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class ResourcePreparationSettings:
    text_extensions: tuple[str, ...] = DEFAULT_TEXT_EXTENSIONS
    soft_max_words: int = DEFAULT_SOFT_MAX_WORDS
    hard_max_words: int = DEFAULT_HARD_MAX_WORDS
    max_ai_words: int = DEFAULT_MAX_AI_WORDS


def load_resource_settings(root: Path) -> ResourcePreparationSettings:
    config_path = root / "config.yml"
    if not config_path.is_file():
        return ResourcePreparationSettings()
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise BuilderError(f"YAML không hợp lệ tại {config_path}: {error}") from error
    if not isinstance(config, dict):
        raise BuilderError(f"Nội dung YAML phải là mapping: {config_path}")
    raw = config.get("resource_preparation", {})
    if not isinstance(raw, dict):
        raise BuilderError("'resource_preparation' trong config.yml phải là mapping")

    extensions = raw.get("text_extensions", list(DEFAULT_TEXT_EXTENSIONS))
    if not isinstance(extensions, list) or not extensions or not all(
        isinstance(value, str) and value.startswith(".") for value in extensions
    ):
        raise BuilderError("resource_preparation.text_extensions không hợp lệ")

    def positive_int(key: str, default: int) -> int:
        value = raw.get(key, default)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise BuilderError(f"resource_preparation.{key} phải là số nguyên dương")
        return value

    soft = positive_int("soft_max_words", DEFAULT_SOFT_MAX_WORDS)
    hard = positive_int("hard_max_words", DEFAULT_HARD_MAX_WORDS)
    maximum = positive_int("max_ai_words", DEFAULT_MAX_AI_WORDS)
    if not soft < hard <= maximum:
        raise BuilderError(
            "resource_preparation phải thỏa soft_max_words < hard_max_words "
            "<= max_ai_words"
        )
    return ResourcePreparationSettings(
        text_extensions=tuple(sorted({value.lower() for value in extensions})),
        soft_max_words=soft,
        hard_max_words=hard,
        max_ai_words=maximum,
    )


def _resource_files(source: Path) -> list[tuple[str, Path]]:
    if source.is_symlink():
        raise BuilderError(f"Resource không được là symlink: {source}")
    if source.is_file():
        return [(source.name, source)]
    if not source.is_dir():
        raise BuilderError(f"Resource không phải file hoặc directory: {source}")

    files: list[tuple[str, Path]] = []
    for path in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise BuilderError(f"Resource không được chứa symlink: {path}")
        if path.is_file():
            files.append((path.relative_to(source).as_posix(), path))
    return files


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resource_sha256(source: Path) -> str:
    digest = hashlib.sha256()
    for relative, path in _resource_files(source):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as file:
            for block in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(block)
        digest.update(b"\0")
    return digest.hexdigest()


def inspect_resource(
    source: Path,
    settings: ResourcePreparationSettings,
) -> dict[str, Any]:
    files = _resource_files(source)
    entries: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    total_bytes = 0
    total_lines = 0
    total_words = 0
    text_count = 0
    attachment_count = 0

    for relative, path in files:
        size = path.stat().st_size
        total_bytes += size
        entry: dict[str, Any] = {
            "path": relative,
            "size_bytes": size,
            "sha256": file_sha256(path),
        }
        if path.suffix.lower() in settings.text_extensions:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                errors.append(f"Text file không phải UTF-8: {relative}")
                entry["kind"] = "invalid-text"
                entries.append(entry)
                continue
            lines = text.splitlines(keepends=True)
            words = len(WORD_PATTERN.findall(text))
            headings = [
                {
                    "line": index,
                    "level": len(match.group(1)),
                    "title": match.group(2).strip(),
                }
                for index, line in enumerate(lines, start=1)
                if (match := HEADING_PATTERN.match(line.rstrip("\r\n")))
            ]
            entry.update(
                kind="text",
                line_count=len(lines),
                word_count=words,
                headings=headings,
            )
            text_count += 1
            total_lines += len(lines)
            total_words += words
        else:
            entry["kind"] = "attachment"
            attachment_count += 1
        entries.append(entry)

    if not files:
        errors.append("Resource không chứa file nào")
    if total_bytes == 0:
        errors.append("Resource rỗng")
    if text_count == 0:
        errors.append("Resource không có text file được hỗ trợ")
    if total_words == 0 and text_count:
        errors.append("Resource không có nội dung text")
    if attachment_count:
        warnings.append(
            f"Có {attachment_count} attachment; attachment chỉ được copy nguyên file"
        )
    if total_words > settings.soft_max_words:
        warnings.append("Resource vượt soft_max_words và cần review khả năng split")
    if total_words > settings.hard_max_words:
        warnings.append("Resource vượt hard_max_words; mặc định phải split")
    if total_words > settings.max_ai_words:
        warnings.append("Resource vượt max_ai_words; cần outline hoặc xử lý thủ công")

    return {
        "source": str(source),
        "kind": "directory" if source.is_dir() else "file",
        "content_sha256": resource_sha256(source),
        "totals": {
            "files": len(files),
            "text_files": text_count,
            "attachments": attachment_count,
            "bytes": total_bytes,
            "lines": total_lines,
            "words": total_words,
        },
        "thresholds": {
            "soft_max_words": settings.soft_max_words,
            "hard_max_words": settings.hard_max_words,
            "max_ai_words": settings.max_ai_words,
        },
        "split_review_required": total_words > settings.soft_max_words,
        "hard_split_required": total_words > settings.hard_max_words,
        "ai_limit_exceeded": total_words > settings.max_ai_words,
        "files": entries,
        "errors": errors,
        "warnings": warnings,
        "valid": not errors,
    }

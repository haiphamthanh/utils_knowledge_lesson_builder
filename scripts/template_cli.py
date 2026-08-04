from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.loading import load_yaml, require_slug


def add_template_parser(subparsers: argparse._SubParsersAction) -> None:
    template_parser = subparsers.add_parser(
        "template", help="Khám phá template workbook"
    )
    commands = template_parser.add_subparsers(
        dest="template_command", required=True
    )
    list_parser = commands.add_parser("list", help="Liệt kê template khả dụng")
    list_parser.add_argument("--json", action="store_true", help="Xuất JSON")


def list_templates(root: Path) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = []
    for manifest in sorted((root / "templates").glob("*/template.yml")):
        data = load_yaml(manifest)
        template_id = require_slug(data.get("id"), f"Template id trong {manifest}")
        if manifest.parent.name != template_id:
            continue
        formats = data.get("formats", {})
        templates.append(
            {
                "id": template_id,
                "name": data.get("name", template_id),
                "description": data.get("description", ""),
                "formats": sorted(formats) if isinstance(formats, dict) else [],
                "number_sections": data.get("number_sections", True),
                "toc_depth": data.get("toc_depth", 2),
                "inspired_by": data.get("inspired_by", []),
            }
        )
    return templates


def templates_as_table(templates: list[dict[str, Any]]) -> str:
    rows = ["ID\tFORMATS\tNUMBERING\tDESCRIPTION"]
    for template in templates:
        numbering = "academic" if template["number_sections"] else "custom/none"
        rows.append(
            f"{template['id']}\t{','.join(template['formats'])}\t{numbering}\t"
            f"{template['description']}"
        )
    return "\n".join(rows)


def handle_template_command(args: argparse.Namespace, root: Path) -> None:
    if args.template_command == "list":
        templates = list_templates(root)
        print(
            json.dumps(templates, ensure_ascii=False, indent=2)
            if args.json
            else templates_as_table(templates)
        )
        return
    raise AssertionError(f"Unsupported template command: {args.template_command}")

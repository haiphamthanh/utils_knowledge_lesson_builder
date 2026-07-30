from __future__ import annotations

import argparse
import sys
from pathlib import Path

from knowledge_builder.builder import build
from knowledge_builder.core import create_plan
from knowledge_builder.models import BuilderError


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def add_selection_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("cookbook", help="ID cookbook, ví dụ web-system-foundations")
    parser.add_argument("--path", dest="path_id", help="Learning path; mặc định lấy từ cookbook.yml")
    parser.add_argument("--template", dest="template_id", help="Tên thư mục trong templates/")
    parser.add_argument("--format", dest="format_id", help="Format do template hỗ trợ")
    parser.add_argument(
        "--include-optional",
        action="store_true",
        help="Đưa optional lessons vào bản build",
    )
    parser.add_argument(
        "--include-draft",
        action="store_true",
        help="Cho phép lesson draft xuất hiện trong bản build",
    )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="build.sh",
        description="Build cookbook từ lessons, knowledge graph và learning path.",
    )
    subparsers = root.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build", help="Validate rồi build tài liệu")
    add_selection_arguments(build_parser)
    validate_parser = subparsers.add_parser("validate", help="Chỉ validate cấu trúc")
    add_selection_arguments(validate_parser)
    return root


def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    try:
        plan = create_plan(
            root=project_root(),
            cookbook_id=args.cookbook,
            path_id=args.path_id,
            template_id=args.template_id,
            format_id=args.format_id,
            include_optional=args.include_optional,
            include_draft=args.include_draft,
        )
        print(
            f"[knowledge-builder] Valid: {plan.cookbook_id}/{plan.path_id} "
            f"({len(plan.ordered_lesson_ids)} lessons, "
            f"template={plan.template_id}, format={plan.format_id})"
        )
        if args.command == "build":
            output = build(plan)
            print(f"[knowledge-builder] Created: {output.relative_to(plan.root)}")
    except BuilderError as error:
        print(f"[knowledge-builder] Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error

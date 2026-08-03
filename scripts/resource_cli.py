from __future__ import annotations

import argparse
from pathlib import Path

from scripts.models import BuilderError
from scripts.resources import (
    RESOURCE_STATUSES,
    ResourceManager,
    items_as_json,
    items_as_table,
    report_as_json,
    report_as_table,
)


def add_resource_parser(subparsers: argparse._SubParsersAction) -> None:
    resource_parser = subparsers.add_parser(
        "resource", help="Quản lý lifecycle raw → archive/pool → done"
    )
    commands = resource_parser.add_subparsers(dest="resource_command", required=True)
    commands.add_parser("sync", help="Đồng bộ item trên filesystem vào index.yml")

    list_parser = commands.add_parser("list", help="Liệt kê resource")
    list_parser.add_argument("--status", choices=RESOURCE_STATUSES)
    list_parser.add_argument("--json", action="store_true", help="Xuất JSON")

    inspect_parser = commands.add_parser("inspect", help="Kiểm kê resource raw")
    inspect_parser.add_argument("item_id")
    inspect_parser.add_argument("--json", action="store_true", help="Xuất JSON")

    verify_parser = commands.add_parser("verify", help="Kiểm tra integrity resource")
    verify_parser.add_argument("item_id")
    verify_parser.add_argument("--json", action="store_true", help="Xuất JSON")

    review_parser = commands.add_parser("review", help="Chuyển raw nhỏ sang pool")
    review_parser.add_argument("item_id")
    review_parser.add_argument(
        "--allow-large-single", action="store_true",
        help="Giữ nguyên resource vượt soft limit sau review ngữ nghĩa",
    )

    complete_parser = commands.add_parser(
        "complete", help="Chuyển pool sang done sau khi lesson đã review"
    )
    complete_parser.add_argument("item_id")
    complete_parser.add_argument("--cookbook", required=True)
    complete_parser.add_argument("--lesson", required=True, dest="lesson_id")


def handle_resource_command(args: argparse.Namespace, root: Path) -> None:
    manager = ResourceManager(root)
    if args.resource_command == "sync":
        data = manager.sync()
        print(f"[knowledge-builder] Synced {len(data['items'])} resource(s).")
        return
    if args.resource_command == "list":
        items = manager.list_items(args.status)
        print(items_as_json(items) if args.json else items_as_table(items))
        return
    if args.resource_command in {"inspect", "verify"}:
        report = (
            manager.inspect(args.item_id)
            if args.resource_command == "inspect"
            else manager.verify(args.item_id)
        )
        print(report_as_json(report) if args.json else report_as_table(report))
        if not report["valid"]:
            raise BuilderError(f"Resource {args.resource_command} failed")
        return
    if args.resource_command == "review":
        destination = manager.review(args.item_id, args.allow_large_single)
        print(f"[knowledge-builder] Reviewed and moved: {destination.relative_to(root)}")
        return
    if args.resource_command == "complete":
        destination = manager.complete(args.item_id, args.cookbook, args.lesson_id)
        print(f"[knowledge-builder] Completed and moved: {destination.relative_to(root)}")
        return
    raise AssertionError(f"Unsupported resource command: {args.resource_command}")

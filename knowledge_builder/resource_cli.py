from __future__ import annotations

import argparse
from pathlib import Path

from knowledge_builder.resources import ResourceManager, items_as_json, items_as_table


def add_resource_parser(subparsers: argparse._SubParsersAction) -> None:
    resource_parser = subparsers.add_parser(
        "resource",
        help="Quản lý lifecycle raw → pool → done",
    )
    commands = resource_parser.add_subparsers(
        dest="resource_command",
        required=True,
    )
    commands.add_parser("sync", help="Đồng bộ item trên filesystem vào index.yml")

    list_parser = commands.add_parser("list", help="Liệt kê resource")
    list_parser.add_argument("--status", choices=("raw", "pool", "done"))
    list_parser.add_argument("--json", action="store_true", help="Xuất JSON")

    review_parser = commands.add_parser("review", help="Chuyển raw sang pool")
    review_parser.add_argument("item_id")

    complete_parser = commands.add_parser(
        "complete",
        help="Chuyển pool sang done sau khi lesson đã review",
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
    if args.resource_command == "review":
        destination = manager.review(args.item_id)
        print(
            "[knowledge-builder] Reviewed and moved: "
            f"{destination.relative_to(root)}"
        )
        return
    if args.resource_command == "complete":
        destination = manager.complete(
            args.item_id,
            args.cookbook,
            args.lesson_id,
        )
        print(
            "[knowledge-builder] Completed and moved: "
            f"{destination.relative_to(root)}"
        )
        return
    raise AssertionError(f"Unsupported resource command: {args.resource_command}")


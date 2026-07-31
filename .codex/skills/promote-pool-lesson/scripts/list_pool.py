#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


def find_project(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / "build.sh").is_file() and (
            candidate / "resource" / "index.yml"
        ).is_file():
            return candidate
    raise RuntimeError(f"Không tìm thấy Knowledge Lesson Builder project từ: {start}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Liệt kê resource item sẵn sàng trong pool dưới dạng JSON."
    )
    parser.add_argument(
        "--project",
        type=Path,
        default=Path.cwd(),
        help="Project root hoặc một thư mục con của project.",
    )
    args = parser.parse_args()

    try:
        root = find_project(args.project)
        result = subprocess.run(
            [
                str(root / "build.sh"),
                "resource",
                "list",
                "--status",
                "pool",
                "--json",
            ],
            cwd=root,
            check=True,
            text=True,
            capture_output=True,
        )
    except (RuntimeError, subprocess.CalledProcessError) as error:
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr.strip(), file=sys.stderr)
        else:
            print(str(error), file=sys.stderr)
        raise SystemExit(1) from error

    print(result.stdout.strip())


if __name__ == "__main__":
    main()

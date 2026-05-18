"""CLI entry point for the envguard sort command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.loader import load_env_file
from envguard.sorter import render_sorted_env, sort_env


def build_sort_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    description = "Sort variables in a .env file alphabetically or by prefix group."
    if parent is not None:
        parser = parent.add_parser("sort", description=description, help=description)
    else:
        parser = argparse.ArgumentParser(prog="envguard-sort", description=description)

    parser.add_argument("env_file", help="Path to the .env file to sort.")
    parser.add_argument(
        "--group-by-prefix",
        action="store_true",
        default=False,
        help="Group variables by their key prefix before sorting.",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        default=False,
        help="Write sorted output back to the original file.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        default=False,
        help="Exit with code 1 if the file is not already sorted (dry-run).",
    )
    return parser


def run_sort(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"[error] File not found: {env_path}", file=sys.stderr)
        return 2

    try:
        env = load_env_file(str(env_path))
    except Exception as exc:  # pragma: no cover
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    report = sort_env(env, group_by_prefix=args.group_by_prefix)
    rendered = render_sorted_env(report, group_by_prefix=args.group_by_prefix)

    if args.check:
        if report.has_changes:
            print(f"[sort] {report.summary()}")
            return 1
        print("[sort] File is already sorted.")
        return 0

    if args.in_place:
        env_path.write_text(rendered + "\n", encoding="utf-8")
        print(f"[sort] Written sorted output to {env_path}")
    else:
        print(rendered)

    return 0


def main() -> None:  # pragma: no cover
    parser = build_sort_parser()
    args = parser.parse_args()
    sys.exit(run_sort(args))


if __name__ == "__main__":  # pragma: no cover
    main()

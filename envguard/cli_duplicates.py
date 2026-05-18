"""CLI entry-point for the duplicate-key detector."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.duplicates import find_duplicates


def build_duplicates_parser(parent: argparse._SubParsersAction | None = None):
    description = "Detect duplicate keys inside a .env file."
    if parent is not None:
        parser = parent.add_parser("duplicates", help=description)
    else:
        parser = argparse.ArgumentParser(
            prog="envguard-duplicates", description=description
        )
    parser.add_argument("env_file", help="Path to the .env file to inspect.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 even when only warnings are present (always the case here).",
    )
    return parser


def run_duplicates(args: argparse.Namespace) -> int:
    try:
        report = find_duplicates(args.env_file)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(report.summary())
    if report.has_duplicates:
        for dup in report.duplicates:
            print(f"  - {dup}")
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_duplicates_parser()
    sys.exit(run_duplicates(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()

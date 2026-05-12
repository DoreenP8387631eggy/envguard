"""CLI entry point for the envguard compare command."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envguard.comparator import compare_env_files, CompareReport
from envguard.masker import mask_env


def build_compare_parser(subparsers=None) -> argparse.ArgumentParser:
    kwargs = dict(
        description="Compare two .env files and report differences.",
    )
    if subparsers is not None:
        parser = subparsers.add_parser("compare", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("old", help="Path to the baseline .env file")
    parser.add_argument("new", help="Path to the updated .env file")
    parser.add_argument(
        "--mask",
        action="store_true",
        default=False,
        help="Mask sensitive values in output",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colored output",
    )
    return parser


def _format_report(report: CompareReport, mask: bool, color: bool) -> List[str]:
    lines: List[str] = []
    lines.append(f"Summary: {report.summary()}")
    if not report.has_changes:
        return lines

    lines.append("")
    for change in report.all_changes():
        line = str(change)
        if mask and change.change_type != "removed" and change.new_value:
            from envguard.masker import is_sensitive, mask_value
            if is_sensitive(change.key):
                line = line.replace(repr(change.new_value), repr(mask_value(change.new_value)))
        if mask and change.change_type != "added" and change.old_value:
            from envguard.masker import is_sensitive, mask_value
            if is_sensitive(change.key):
                line = line.replace(repr(change.old_value), repr(mask_value(change.old_value)))
        lines.append(line)

    return lines


def run_compare(args: argparse.Namespace) -> int:
    try:
        report, warnings = compare_env_files(args.old, args.new)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 2

    for warn in warnings:
        print(f"Warning: {warn}", file=sys.stderr)

    color = not getattr(args, "no_color", False)
    lines = _format_report(report, mask=args.mask, color=color)
    print("\n".join(lines))

    return 1 if report.has_changes else 0


def main() -> None:
    parser = build_compare_parser()
    args = parser.parse_args()
    sys.exit(run_compare(args))


if __name__ == "__main__":
    main()

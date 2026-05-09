"""CLI sub-command: envguard lint — style-check a .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.linter import lint_env_file


def build_lint_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Lint a .env file for style and best-practice issues."
    if subparsers is not None:
        parser = subparsers.add_parser("lint", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envguard lint", description=description)

    parser.add_argument("env_file", help="Path to the .env file to lint")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status on warnings as well as errors",
    )
    parser.add_argument(
        "--no-warnings",
        dest="no_warnings",
        action="store_true",
        help="Suppress warning output (errors still shown)",
    )
    return parser


def run_lint(args: argparse.Namespace) -> int:
    """Execute the lint command; returns an exit code."""
    result = lint_env_file(args.env_file)

    for issue in result.issues:
        if issue.severity == "warning" and args.no_warnings:
            continue
        print(str(issue))

    total = result.error_count + result.warning_count
    label = Path(args.env_file).name

    if result.passed and result.warning_count == 0:
        print(f"✔  {label}: no issues found.")
        return 0

    print(
        f"\n{label}: {result.error_count} error(s), {result.warning_count} warning(s)."
    )

    if not result.passed:
        return 1
    if args.strict and result.warning_count:
        return 1
    return 0


def main(argv=None) -> None:  # pragma: no cover
    parser = build_lint_parser()
    args = parser.parse_args(argv)
    sys.exit(run_lint(args))


if __name__ == "__main__":  # pragma: no cover
    main()

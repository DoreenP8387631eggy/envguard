"""CLI entry-point for the deprecation scanner."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from envguard.deprecator import DeprecationRegistry, build_registry, scan_for_deprecated
from envguard.loader import load_env_file


def build_deprecate_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envguard-deprecate",
        description="Scan a .env file for deprecated variable names.",
    )
    parser.add_argument("env_file", help="Path to the .env file to scan.")
    parser.add_argument(
        "--registry",
        required=True,
        help="Path to a JSON file defining deprecated variables.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any deprecated variables are found.",
    )
    return parser


def _load_registry(path: str) -> DeprecationRegistry:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, list):
        raise ValueError("Registry JSON must be a list of objects.")
    return build_registry(data)


def run_deprecate(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(args.env_file)
    except FileNotFoundError:
        print(f"ERROR: env file not found: {args.env_file}", file=sys.stderr)
        return 2

    try:
        registry = _load_registry(args.registry)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: invalid registry file: {exc}", file=sys.stderr)
        return 2

    report = scan_for_deprecated(env, registry)
    print(report.summary())

    if args.strict and report.has_hits:
        return 1
    return 0


def main(argv: List[str] | None = None) -> None:
    parser = build_deprecate_parser()
    args = parser.parse_args(argv)
    sys.exit(run_deprecate(args))


if __name__ == "__main__":
    main()

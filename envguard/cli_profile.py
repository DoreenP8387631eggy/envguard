"""CLI entry-point for the envguard profile sub-command."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envguard.loader import load_env_file
from envguard.profiler import profile_env


def build_profile_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    description = "Profile a .env file for suspicious or anomalous values."
    if parent is not None:
        parser = parent.add_parser("profile", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envguard-profile", description=description)

    parser.add_argument("env_file", help="Path to the .env file to profile.")
    parser.add_argument(
        "--entropy-threshold",
        type=float,
        default=3.5,
        metavar="FLOAT",
        help="Shannon entropy threshold above which a value is flagged (default: 3.5).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Exit with code 1 even when only warnings are present.",
    )
    return parser


def run_profile(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    try:
        env = load_env_file(str(env_path))
    except FileNotFoundError:
        print(f"[ERROR] File not found: {env_path}", file=sys.stderr)
        return 2

    report = profile_env(env, entropy_threshold=args.entropy_threshold)

    if args.format == "json":
        output = {
            "passed": report.passed,
            "stats": report.stats,
            "issues": [
                {"level": i.level, "key": i.key, "message": i.message}
                for i in report.issues
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        status = "PASSED" if report.passed else "FAILED"
        print(f"Profile result: {status}")
        print(f"  Total keys : {report.stats.get('total_keys', 0)}")
        for issue in report.issues:
            print(f"  {issue}")

    if not report.passed:
        return 1
    if args.fail_on_warnings and report.warnings():
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_profile_parser()
    args = parser.parse_args()
    sys.exit(run_profile(args))


if __name__ == "__main__":  # pragma: no cover
    main()

"""CLI entry-point for the env-file merge command."""

from __future__ import annotations

import argparse
import sys

from envguard.merger import MergeStrategy, merge_env_files
from envguard.loader import EnvFileNotFoundError


def build_merge_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: E501
    kwargs = dict(
        prog="envguard merge",
        description="Merge multiple .env files with conflict detection.",
    )
    parser = (
        parent.add_parser("merge", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".env files to merge (in order of precedence for first-wins strategy)",
    )
    parser.add_argument(
        "--strategy",
        choices=[s.value for s in MergeStrategy],
        default=MergeStrategy.LAST_WINS.value,
        help="Conflict resolution strategy (default: last_wins)",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        default=None,
        help="Write merged result to FILE instead of stdout",
    )
    parser.add_argument(
        "--ignore-missing",
        action="store_true",
        help="Skip files that do not exist instead of aborting",
    )
    parser.add_argument(
        "--show-conflicts",
        action="store_true",
        help="Print conflict details to stderr",
    )
    return parser


def run_merge(args: argparse.Namespace) -> int:
    strategy = MergeStrategy(args.strategy)
    try:
        report = merge_env_files(
            paths=args.files,
            strategy=strategy,
            ignore_missing=args.ignore_missing,
        )
    except EnvFileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.show_conflicts and report.has_conflicts:
        for conflict in report.conflicts:
            print(str(conflict), file=sys.stderr)

    lines = [f"{k}={v}" for k, v in sorted(report.merged.items())]
    output_text = "\n".join(lines) + ("\n" if lines else "")

    if args.output:
        with open(args.output, "w") as fh:
            fh.write(output_text)
    else:
        print(output_text, end="")

    print(report.summary, file=sys.stderr)
    return 1 if report.has_conflicts else 0


def main() -> None:  # pragma: no cover
    parser = build_merge_parser()
    sys.exit(run_merge(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()

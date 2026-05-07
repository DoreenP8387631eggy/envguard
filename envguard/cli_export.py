"""CLI sub-command handler for `envguard export`."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from envguard.cli import load_schema_from_file
from envguard.exporter import ExportFormat, export_schema


def build_export_parser(sub) -> ArgumentParser:  # type: ignore[no-untyped-def]
    """Attach the *export* sub-command to an existing sub-parsers group."""
    p: ArgumentParser = sub.add_parser(
        "export",
        help="Export the schema as a dotenv template, JSON Schema, or Markdown docs.",
    )
    p.add_argument("schema", help="Path to the Python schema file (e.g. example_schema.py).")
    p.add_argument(
        "--format",
        choices=[f.value for f in ExportFormat],
        default=ExportFormat.DOTENV.value,
        dest="fmt",
        help="Output format (default: dotenv).",
    )
    p.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write output to this file instead of stdout.",
    )
    return p


def run_export(args: Namespace) -> int:
    """Execute the export command; returns an exit code."""
    try:
        schema = load_schema_from_file(args.schema)
    except Exception as exc:  # noqa: BLE001
        print(f"[envguard] Failed to load schema: {exc}", file=sys.stderr)
        return 1

    fmt = ExportFormat(args.fmt)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as fh:
            export_schema(schema, fmt, fh)
        print(f"[envguard] Exported {fmt.value} to {out_path}")
    else:
        export_schema(schema, fmt, sys.stdout)

    return 0

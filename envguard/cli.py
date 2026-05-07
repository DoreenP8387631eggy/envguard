"""Command-line interface for envguard."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

from .auditor import audit
from .differ import diff_env_files, diff_env_against_schema
from .loader import EnvFileNotFoundError, EnvParseError
from .reporter import OutputFormat, format_report
from .schema import EnvSchema


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envguard",
        description="Validate and audit .env files against a schema.",
    )
    sub = parser.add_subparsers(dest="command")

    # --- audit sub-command ---
    audit_p = sub.add_parser("audit", help="Audit a .env file against a schema.")
    audit_p.add_argument("env_file", help="Path to the .env file")
    audit_p.add_argument("schema_file", help="Path to the Python schema file")
    audit_p.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        dest="output_format",
    )
    audit_p.add_argument(
        "--strict", action="store_true", help="Exit non-zero on warnings too"
    )

    # --- diff sub-command ---
    diff_p = sub.add_parser("diff", help="Diff two .env files or a .env against its schema.")
    diff_p.add_argument("left", help="First .env file (or .env file when using --schema)")
    diff_p.add_argument(
        "right", nargs="?", help="Second .env file (omit when using --schema)"
    )
    diff_p.add_argument("--schema", dest="schema_file", help="Schema file to diff against")
    diff_p.add_argument(
        "--no-mask", action="store_true", help="Show actual values instead of masking"
    )

    return parser


def load_schema_from_file(path: str) -> EnvSchema:
    spec = importlib.util.spec_from_file_location("_envguard_schema", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load schema from {path!r}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    if not hasattr(module, "schema") or not isinstance(module.schema, EnvSchema):
        raise SystemExit(f"Schema file {path!r} must define a top-level 'schema' (EnvSchema).")
    return module.schema  # type: ignore[return-value]


def _run_audit(args: argparse.Namespace) -> int:
    schema = load_schema_from_file(args.schema_file)
    try:
        report = audit(args.env_file, schema)
    except (EnvFileNotFoundError, EnvParseError) as exc:
        print(f"envguard error: {exc}", file=sys.stderr)
        return 2
    fmt = OutputFormat(args.output_format)
    print(format_report(report, fmt))
    if report.errors:
        return 1
    if args.strict and report.warnings:
        return 1
    return 0


def _run_diff(args: argparse.Namespace) -> int:
    try:
        if args.schema_file:
            schema = load_schema_from_file(args.schema_file)
            result = diff_env_against_schema(args.left, schema)
        elif args.right:
            result = diff_env_files(args.left, args.right, mask_values=not args.no_mask)
        else:
            print("envguard diff: provide a second .env file or --schema.", file=sys.stderr)
            return 2
    except (EnvFileNotFoundError, EnvParseError) as exc:
        print(f"envguard error: {exc}", file=sys.stderr)
        return 2
    print(result.summary())
    return 1 if result.has_diff else 0


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "audit":
        sys.exit(_run_audit(args))
    elif args.command == "diff":
        sys.exit(_run_diff(args))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":  # pragma: no cover
    main()

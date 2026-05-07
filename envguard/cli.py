"""Command-line interface for envguard."""

import argparse
import sys
from pathlib import Path

from envguard.loader import load_env_file, load_env_with_os_override, EnvFileNotFoundError, EnvParseError
from envguard.auditor import audit
from envguard.reporter import format_report, OutputFormat
from envguard.schema import EnvSchema


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envguard",
        description="Validate and audit .env files against a schema.",
    )
    parser.add_argument(
        "env_file",
        type=str,
        help="Path to the .env file to validate.",
    )
    parser.add_argument(
        "schema_file",
        type=str,
        help="Path to the Python schema file defining EnvSchema.",
    )
    parser.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        help="Output format: text, json, or github (default: text).",
    )
    parser.add_argument(
        "--os-override",
        action="store_true",
        default=False,
        help="Allow OS environment variables to override .env values.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit with non-zero code on warnings as well as errors.",
    )
    return parser


def load_schema_from_file(schema_path: str) -> EnvSchema:
    """Dynamically load an EnvSchema instance from a Python file."""
    import importlib.util

    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    spec = importlib.util.spec_from_file_location("_envguard_schema", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "schema"):
        raise AttributeError(
            f"Schema file '{schema_path}' must define a top-level 'schema' variable of type EnvSchema."
        )
    return module.schema


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.os_override:
            env_vars = load_env_with_os_override(args.env_file)
        else:
            env_vars = load_env_file(args.env_file)
    except EnvFileNotFoundError as exc:
        print(f"[envguard] ERROR: {exc}", file=sys.stderr)
        return 2
    except EnvParseError as exc:
        print(f"[envguard] PARSE ERROR: {exc}", file=sys.stderr)
        return 2

    try:
        schema = load_schema_from_file(args.schema_file)
    except (FileNotFoundError, AttributeError) as exc:
        print(f"[envguard] SCHEMA ERROR: {exc}", file=sys.stderr)
        return 2

    report = audit(env_vars, schema)
    output_format = OutputFormat(args.format)
    print(format_report(report, output_format))

    if report.errors:
        return 1
    if args.strict and report.warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""CLI entry-point for the cross-field validator."""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Optional

from envguard.loader import load_env_file
from envguard.validator import EnvValidator, ValidationResult


def build_validate_parser(sub: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    description = "Run cross-field validation rules against a .env file."
    if sub is not None:
        parser = sub.add_parser("validate", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envguard-validate", description=description)
    parser.add_argument("env_file", help="Path to the .env file")
    parser.add_argument(
        "--rules",
        required=True,
        metavar="RULES_PY",
        help="Python file that exposes an EnvValidator instance named 'validator'",
    )
    return parser


def _load_validator(rules_path: str) -> EnvValidator:
    path = Path(rules_path)
    if not path.exists():
        print(f"error: rules file not found: {rules_path}", file=sys.stderr)
        sys.exit(2)
    spec = importlib.util.spec_from_file_location("_envguard_rules", path)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    if not hasattr(module, "validator"):
        print("error: rules file must define a top-level 'validator' (EnvValidator) instance.", file=sys.stderr)
        sys.exit(2)
    return module.validator  # type: ignore[return-value]


def run_validate(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(args.env_file)
    except FileNotFoundError:
        print(f"error: env file not found: {args.env_file}", file=sys.stderr)
        return 2

    validator = _load_validator(args.rules)
    result: ValidationResult = validator.validate(env)

    if result.passed:
        print(f"envguard-validate: all {len(validator.rules)} rule(s) passed.")
        return 0

    print(f"envguard-validate: {len(result.violations)} violation(s) found.")
    for v in result.violations:
        print(f"  {v}")
    return 1


def main() -> None:  # pragma: no cover
    parser = build_validate_parser()
    sys.exit(run_validate(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()

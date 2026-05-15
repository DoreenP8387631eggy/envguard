"""Tests for envguard.cli_validate."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envguard.cli_validate import build_validate_parser, run_validate


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\n")
    return p


@pytest.fixture()
def rules_file(tmp_path: Path) -> Path:
    p = tmp_path / "rules.py"
    p.write_text(textwrap.dedent("""
        from envguard.validator import EnvValidator, ValidationRule

        validator = EnvValidator()
        validator.add_rule(ValidationRule(
            name="db_together",
            check=lambda env: (
                None
                if ("DB_HOST" in env) == ("DB_PORT" in env)
                else "DB_HOST and DB_PORT must both be present or both absent"
            ),
        ))
    """))
    return p


@pytest.fixture()
def failing_rules_file(tmp_path: Path) -> Path:
    p = tmp_path / "failing_rules.py"
    p.write_text(textwrap.dedent("""
        from envguard.validator import EnvValidator, ValidationRule

        validator = EnvValidator()
        validator.add_rule(ValidationRule(
            name="always_fail",
            check=lambda env: "this always fails",
        ))
    """))
    return p


def _args(env_file, rules_file):
    parser = build_validate_parser()
    return parser.parse_args([str(env_file), "--rules", str(rules_file)])


def test_passing_rules_exit_zero(env_file, rules_file):
    code = run_validate(_args(env_file, rules_file))
    assert code == 0


def test_failing_rules_exit_one(env_file, failing_rules_file):
    code = run_validate(_args(env_file, failing_rules_file))
    assert code == 1


def test_missing_env_file_exits_two(tmp_path, rules_file):
    args = _args(tmp_path / "no.env", rules_file)
    code = run_validate(args)
    assert code == 2


def test_missing_rules_file_exits_two(env_file, tmp_path):
    args = _args(env_file, tmp_path / "no_rules.py")
    code = run_validate(args)
    assert code == 2


def test_rules_file_without_validator_symbol_exits_two(env_file, tmp_path):
    bad_rules = tmp_path / "bad.py"
    bad_rules.write_text("x = 1\n")
    args = _args(env_file, bad_rules)
    code = run_validate(args)
    assert code == 2

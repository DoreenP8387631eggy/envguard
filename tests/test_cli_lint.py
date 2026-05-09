"""Tests for envguard.cli_lint."""
from pathlib import Path

import pytest

from envguard.cli_lint import build_lint_parser, run_lint


@pytest.fixture
def env_file(tmp_path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content, encoding="utf-8")
        return p
    return _write


def _args(env_path, strict=False, no_warnings=False):
    parser = build_lint_parser()
    flags = [str(env_path)]
    if strict:
        flags.append("--strict")
    if no_warnings:
        flags.append("--no-warnings")
    return parser.parse_args(flags)


def test_clean_env_exits_zero(env_file):
    p = env_file("DATABASE_URL=postgres://localhost/db\n")
    assert run_lint(_args(p)) == 0


def test_missing_file_exits_one():
    args = _args("/nonexistent/.env")
    assert run_lint(args) == 1


def test_warning_exits_zero_without_strict(env_file):
    p = env_file("my_key=value\n")  # W001
    assert run_lint(_args(p, strict=False)) == 0


def test_warning_exits_one_with_strict(env_file):
    p = env_file("my_key=value\n")  # W001
    assert run_lint(_args(p, strict=True)) == 1


def test_no_warnings_flag_suppresses_output(env_file, capsys):
    p = env_file("my_key=value\n")  # W001
    run_lint(_args(p, no_warnings=True))
    captured = capsys.readouterr()
    assert "W001" not in captured.out


def test_error_always_exits_one(env_file):
    p = env_file("NOT_VALID\n")  # E002
    assert run_lint(_args(p)) == 1


def test_duplicate_key_reported(env_file, capsys):
    p = env_file("FOO=1\nFOO=2\n")
    run_lint(_args(p))
    captured = capsys.readouterr()
    assert "W002" in captured.out


def test_build_lint_parser_returns_parser():
    parser = build_lint_parser()
    assert parser is not None

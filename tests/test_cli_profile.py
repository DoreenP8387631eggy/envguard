"""Tests for envguard.cli_profile."""
import argparse
import json
from pathlib import Path

import pytest

from envguard.cli_profile import build_profile_parser, run_profile


@pytest.fixture()
def env_file(tmp_path: Path):
    return tmp_path / ".env"


def _write(path: Path, content: str) -> None:
    path.write_text(content)


def _args(env_file: str, fmt: str = "text", threshold: float = 3.5, fail_on_warnings: bool = False):
    parser = build_profile_parser()
    argv = [env_file, "--format", fmt, "--entropy-threshold", str(threshold)]
    if fail_on_warnings:
        argv.append("--fail-on-warnings")
    return parser.parse_args(argv)


def test_clean_env_exits_zero(env_file: Path):
    _write(env_file, "HOST=localhost\nPORT=5432\n")
    code = run_profile(_args(str(env_file)))
    assert code == 0


def test_missing_file_exits_two(env_file: Path):
    code = run_profile(_args(str(env_file)))
    assert code == 2


def test_placeholder_triggers_warning_text(env_file: Path, capsys):
    _write(env_file, "API_KEY=<your-api-key>\n")
    code = run_profile(_args(str(env_file)))
    captured = capsys.readouterr()
    assert "API_KEY" in captured.out
    assert code == 0  # warnings don't fail by default


def test_fail_on_warnings_exits_one(env_file: Path):
    _write(env_file, "API_KEY=<your-api-key>\n")
    code = run_profile(_args(str(env_file), fail_on_warnings=True))
    assert code == 1


def test_json_output_structure(env_file: Path, capsys):
    _write(env_file, "HOST=localhost\nEMPTY=\n")
    code = run_profile(_args(str(env_file), fmt="json"))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "passed" in data
    assert "stats" in data
    assert "issues" in data
    assert isinstance(data["issues"], list)


def test_json_output_empty_value_warning(env_file: Path, capsys):
    _write(env_file, "SECRET=\n")
    run_profile(_args(str(env_file), fmt="json"))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    keys = [i["key"] for i in data["issues"]]
    assert "SECRET" in keys


def test_build_profile_parser_standalone():
    parser = build_profile_parser()
    assert isinstance(parser, argparse.ArgumentParser)

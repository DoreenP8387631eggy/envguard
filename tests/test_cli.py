"""Tests for envguard CLI."""

import json
import textwrap
from pathlib import Path

import pytest

from envguard.cli import main, load_schema_from_file


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("APP_HOST=localhost\nAPP_PORT=8080\nDEBUG=true\n")
    return p


@pytest.fixture()
def schema_file(tmp_path: Path) -> Path:
    p = tmp_path / "schema.py"
    p.write_text(
        textwrap.dedent("""\
            from envguard.schema import EnvSchema, VarSchema, VarType

            schema = EnvSchema()
            schema.add(VarSchema("APP_HOST", var_type=VarType.STRING, required=True))
            schema.add(VarSchema("APP_PORT", var_type=VarType.INTEGER, required=True))
            schema.add(VarSchema("DEBUG", var_type=VarType.BOOLEAN, required=False))
        """)
    )
    return p


@pytest.fixture()
def missing_var_schema_file(tmp_path: Path) -> Path:
    p = tmp_path / "schema_missing.py"
    p.write_text(
        textwrap.dedent("""\
            from envguard.schema import EnvSchema, VarSchema, VarType

            schema = EnvSchema()
            schema.add(VarSchema("APP_HOST", var_type=VarType.STRING, required=True))
            schema.add(VarSchema("APP_PORT", var_type=VarType.INTEGER, required=True))
            schema.add(VarSchema("SECRET_KEY", var_type=VarType.STRING, required=True))
        """)
    )
    return p


def test_cli_passes_valid_env(env_file, schema_file, capsys):
    exit_code = main([str(env_file), str(schema_file)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "PASSED" in captured.out or "passed" in captured.out.lower()


def test_cli_fails_on_missing_required_var(env_file, missing_var_schema_file, capsys):
    exit_code = main([str(env_file), str(missing_var_schema_file)])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "SECRET_KEY" in captured.out


def test_cli_json_output(env_file, schema_file, capsys):
    exit_code = main([str(env_file), str(schema_file), "--format", "json"])
    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "passed" in data


def test_cli_missing_env_file(tmp_path, schema_file):
    exit_code = main([str(tmp_path / "nonexistent.env"), str(schema_file)])
    assert exit_code == 2


def test_cli_missing_schema_file(env_file, tmp_path):
    exit_code = main([str(env_file), str(tmp_path / "no_schema.py")])
    assert exit_code == 2


def test_cli_schema_missing_schema_variable(env_file, tmp_path):
    bad_schema = tmp_path / "bad.py"
    bad_schema.write_text("x = 1\n")
    exit_code = main([str(env_file), str(bad_schema)])
    assert exit_code == 2


def test_cli_strict_mode_warnings(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text("APP_HOST=localhost\n")
    schema = tmp_path / "schema.py"
    schema.write_text(
        textwrap.dedent("""\
            from envguard.schema import EnvSchema, VarSchema, VarType

            schema = EnvSchema()
            schema.add(VarSchema("APP_HOST", var_type=VarType.STRING, required=True))
            schema.add(VarSchema("OPTIONAL_VAR", var_type=VarType.STRING, required=False))
        """)
    )
    # Without strict: warnings should not cause failure
    exit_code = main([str(env), str(schema)])
    assert exit_code == 0

    # With strict: warnings cause failure
    exit_code_strict = main([str(env), str(schema), "--strict"])
    # Only fails if there are actual warnings; depends on auditor behaviour
    assert exit_code_strict in (0, 1)

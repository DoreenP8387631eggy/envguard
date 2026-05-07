"""Integration tests for the `envguard export` CLI sub-command."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from envguard.cli_export import run_export


@pytest.fixture()
def schema_file(tmp_path: Path) -> Path:
    """Write a minimal schema file and return its path."""
    p = tmp_path / "schema.py"
    p.write_text(
        "from envguard.schema import EnvSchema, VarType\n"
        "schema = EnvSchema()\n"
        "schema.add('SECRET_KEY', var_type=VarType.STRING, required=True, description='App secret')\n"
        "schema.add('PORT', var_type=VarType.INTEGER, required=False, default='8000')\n"
    )
    return p


def _args(schema, fmt="dotenv", output=None):
    return SimpleNamespace(schema=str(schema), fmt=fmt, output=output)


def test_export_dotenv_to_stdout(schema_file, capsys):
    code = run_export(_args(schema_file, fmt="dotenv"))
    assert code == 0
    captured = capsys.readouterr().out
    assert "SECRET_KEY=" in captured
    assert "PORT=8000" in captured


def test_export_json_schema_to_stdout(schema_file, capsys):
    code = run_export(_args(schema_file, fmt="json_schema"))
    assert code == 0
    out = capsys.readouterr().out
    doc = json.loads(out)
    assert "SECRET_KEY" in doc["required"]
    assert "PORT" not in doc["required"]


def test_export_markdown_to_stdout(schema_file, capsys):
    code = run_export(_args(schema_file, fmt="markdown"))
    assert code == 0
    out = capsys.readouterr().out
    assert "# Environment Variables Reference" in out
    assert "`SECRET_KEY`" in out


def test_export_to_file(schema_file, tmp_path):
    out_file = tmp_path / "output" / "template.env"
    code = run_export(_args(schema_file, fmt="dotenv", output=str(out_file)))
    assert code == 0
    assert out_file.exists()
    content = out_file.read_text()
    assert "SECRET_KEY" in content


def test_export_returns_1_on_bad_schema(tmp_path):
    bad = tmp_path / "bad_schema.py"
    bad.write_text("this is not valid python !!!")
    code = run_export(_args(bad, fmt="dotenv"))
    assert code == 1

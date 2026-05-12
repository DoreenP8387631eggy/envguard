"""Integration tests for envguard.cli_score."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from envguard.cli_score import build_score_parser, run_score


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("API_KEY=supersecretvalue123\nDEBUG=false\nPORT=8080\n")
    return p


@pytest.fixture
def schema_file(tmp_path: Path) -> Path:
    p = tmp_path / "schema.py"
    p.write_text(textwrap.dedent("""\
        from envguard.schema import EnvSchema, VarSchema, VarType
        schema = EnvSchema()
        schema.add(VarSchema(name="API_KEY", required=True))
        schema.add(VarSchema(name="DEBUG", required=False, var_type=VarType.BOOL))
        schema.add(VarSchema(name="PORT", required=True, var_type=VarType.INT))
    """))
    return p


@pytest.fixture
def missing_var_schema_file(tmp_path: Path) -> Path:
    p = tmp_path / "schema_missing.py"
    p.write_text(textwrap.dedent("""\
        from envguard.schema import EnvSchema, VarSchema
        schema = EnvSchema()
        schema.add(VarSchema(name="MISSING_VAR", required=True))
    """))
    return p


def _args(env_file, schema=None, min_score=70, as_json=False):
    import argparse
    ns = argparse.Namespace(
        env_file=str(env_file),
        schema=str(schema) if schema else None,
        min_score=min_score,
        as_json=as_json,
    )
    return ns


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_perfect_env_exits_zero(env_file, schema_file):
    code = run_score(_args(env_file, schema=schema_file))
    assert code == 0


def test_missing_required_var_lowers_score(env_file, missing_var_schema_file):
    code = run_score(_args(env_file, schema=missing_var_schema_file, min_score=95))
    assert code == 1


def test_no_schema_still_runs(env_file):
    code = run_score(_args(env_file))
    assert code == 0


def test_json_output_structure(env_file, schema_file, capsys):
    run_score(_args(env_file, schema=schema_file, as_json=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "score" in data
    assert "grade" in data
    assert "passed" in data
    assert "penalties" in data
    assert "notes" in data


def test_min_score_threshold_respected(env_file, schema_file):
    code = run_score(_args(env_file, schema=schema_file, min_score=0))
    assert code == 0


def test_missing_env_file_returns_two(tmp_path):
    missing = tmp_path / "nonexistent.env"
    code = run_score(_args(missing))
    assert code == 2


def test_parser_builds_without_error():
    parser = build_score_parser()
    assert parser is not None


def test_text_output_contains_score(env_file, capsys):
    run_score(_args(env_file))
    out = capsys.readouterr().out
    assert "Health Score" in out
    assert "/100" in out

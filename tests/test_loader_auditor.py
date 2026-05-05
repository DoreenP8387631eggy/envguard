"""Tests for envguard.loader and envguard.auditor."""

import textwrap
from pathlib import Path

import pytest

from envguard.auditor import audit, audit_file, AuditReport
from envguard.loader import (
    EnvFileNotFoundError,
    EnvParseError,
    load_env_file,
    load_env_with_os_override,
)
from envguard.schema import EnvSchema, VarSchema, VarType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_env(tmp_path: Path, content: str) -> Path:
    env_file = tmp_path / ".env"
    env_file.write_text(textwrap.dedent(content), encoding="utf-8")
    return str(env_file)


def simple_schema() -> EnvSchema:
    schema = EnvSchema()
    schema.add("DATABASE_URL", VarSchema(type=VarType.STRING, required=True))
    schema.add("PORT", VarSchema(type=VarType.INTEGER, required=False, default="8080"))
    schema.add("DEBUG", VarSchema(type=VarType.BOOLEAN, required=False))
    return schema


# ---------------------------------------------------------------------------
# loader tests
# ---------------------------------------------------------------------------

def test_load_basic_env(tmp_path):
    path = write_env(tmp_path, """
        DATABASE_URL=postgres://localhost/db
        PORT=5432
    """)
    result = load_env_file(path)
    assert result["DATABASE_URL"] == "postgres://localhost/db"
    assert result["PORT"] == "5432"


def test_load_strips_quotes(tmp_path):
    path = write_env(tmp_path, 'SECRET="my secret value"\n')
    result = load_env_file(path)
    assert result["SECRET"] == "my secret value"


def test_load_skips_comments_and_blanks(tmp_path):
    path = write_env(tmp_path, """
        # This is a comment

        KEY=value
    """)
    result = load_env_file(path)
    assert list(result.keys()) == ["KEY"]


def test_load_missing_file():
    with pytest.raises(EnvFileNotFoundError):
        load_env_file("/nonexistent/.env")


def test_load_parse_error(tmp_path):
    path = write_env(tmp_path, "INVALID LINE\n")
    with pytest.raises(EnvParseError):
        load_env_file(path)


def test_os_override(tmp_path, monkeypatch):
    path = write_env(tmp_path, "PORT=3000\n")
    monkeypatch.setenv("PORT", "9000")
    result = load_env_with_os_override(path, override=True)
    assert result["PORT"] == "9000"


# ---------------------------------------------------------------------------
# auditor tests
# ---------------------------------------------------------------------------

def test_audit_passes_when_all_present():
    env = {"DATABASE_URL": "postgres://localhost/db", "PORT": "5432", "DEBUG": "true"}
    report = audit(env, simple_schema())
    assert report.passed
    assert len(report.errors) == 0


def test_audit_error_on_missing_required():
    env = {"PORT": "5432"}
    report = audit(env, simple_schema())
    assert not report.passed
    assert any(i.key == "DATABASE_URL" for i in report.errors)


def test_audit_warning_on_missing_optional_no_default():
    env = {"DATABASE_URL": "postgres://localhost/db"}
    report = audit(env, simple_schema())
    assert report.passed  # no errors
    assert any(i.key == "DEBUG" for i in report.warnings)


def test_audit_file_integration(tmp_path):
    path = write_env(tmp_path, "DATABASE_URL=postgres://localhost/db\nPORT=8080\n")
    report = audit_file(path, simple_schema())
    assert report.passed


def test_audit_report_summary_failed():
    env: dict = {}
    report = audit(env, simple_schema())
    assert "FAILED" in report.summary()

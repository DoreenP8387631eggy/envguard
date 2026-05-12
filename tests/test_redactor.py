"""Tests for envguard.redactor."""

from __future__ import annotations

from pathlib import Path

import pytest

from envguard.redactor import redact_env_dict, redact_env_file, redact_line


# ---------------------------------------------------------------------------
# redact_line
# ---------------------------------------------------------------------------

def test_redact_line_sensitive_key():
    result = redact_line("SECRET_KEY=supersecret\n")
    assert result == "SECRET_KEY=***\n"


def test_redact_line_non_sensitive_key():
    result = redact_line("APP_NAME=myapp\n")
    assert result == "APP_NAME=myapp\n"


def test_redact_line_comment_unchanged():
    line = "# This is a comment\n"
    assert redact_line(line) == line


def test_redact_line_blank_unchanged():
    line = "\n"
    assert redact_line(line) == line


def test_redact_line_custom_placeholder():
    result = redact_line("API_KEY=abc123", placeholder="<REDACTED>")
    assert result == "API_KEY=<REDACTED>"


def test_redact_line_extra_sensitive():
    result = redact_line("MY_CUSTOM_VAR=value", extra_sensitive=["MY_CUSTOM_VAR"])
    assert result == "MY_CUSTOM_VAR=***"


def test_redact_line_export_prefix():
    result = redact_line("export DATABASE_PASSWORD=hunter2\n")
    assert result == "export DATABASE_PASSWORD=***\n"


# ---------------------------------------------------------------------------
# redact_env_dict
# ---------------------------------------------------------------------------

def test_redact_env_dict_masks_sensitive():
    env = {"SECRET_KEY": "abc", "APP_NAME": "myapp", "DB_PASSWORD": "pass"}
    result = redact_env_dict(env)
    assert result["SECRET_KEY"] == "***"
    assert result["DB_PASSWORD"] == "***"
    assert result["APP_NAME"] == "myapp"


def test_redact_env_dict_extra_sensitive():
    env = {"CUSTOM": "value", "OTHER": "ok"}
    result = redact_env_dict(env, extra_sensitive=["CUSTOM"])
    assert result["CUSTOM"] == "***"
    assert result["OTHER"] == "ok"


def test_redact_env_dict_does_not_mutate_original():
    env = {"API_KEY": "secret"}
    redact_env_dict(env)
    assert env["API_KEY"] == "secret"


# ---------------------------------------------------------------------------
# redact_env_file
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "APP_NAME=myapp\n"
        "SECRET_KEY=topsecret\n"
        "# comment\n"
        "DB_PASSWORD=hunter2\n"
        "PORT=8080\n",
        encoding="utf-8",
    )
    return p


def test_redact_env_file_count(env_file: Path):
    _, count = redact_env_file(env_file)
    assert count == 2  # SECRET_KEY and DB_PASSWORD


def test_redact_env_file_content(env_file: Path):
    content, _ = redact_env_file(env_file)
    assert "SECRET_KEY=***" in content
    assert "DB_PASSWORD=***" in content
    assert "APP_NAME=myapp" in content
    assert "PORT=8080" in content


def test_redact_env_file_writes_destination(env_file: Path, tmp_path: Path):
    dest = tmp_path / "out" / ".env.redacted"
    redact_env_file(env_file, destination=dest)
    assert dest.exists()
    assert "SECRET_KEY=***" in dest.read_text()


def test_redact_env_file_missing_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        redact_env_file(tmp_path / "nonexistent.env")

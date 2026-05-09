"""Tests for envguard.linter."""
from pathlib import Path

import pytest

from envguard.linter import lint_env_file, LintIssue


@pytest.fixture
def env_file(tmp_path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content, encoding="utf-8")
        return p
    return _write


def test_clean_file_has_no_issues(env_file):
    p = env_file("DATABASE_URL=postgres://localhost/db\nDEBUG=true\n")
    result = lint_env_file(p)
    assert result.passed
    assert result.issues == []


def test_missing_file_returns_error():
    result = lint_env_file("/nonexistent/.env")
    assert not result.passed
    assert result.error_count == 1
    assert result.issues[0].code == "E001"


def test_invalid_assignment_line(env_file):
    p = env_file("NOT_AN_ASSIGNMENT\n")
    result = lint_env_file(p)
    assert result.error_count == 1
    assert result.issues[0].code == "E002"


def test_lowercase_key_warning(env_file):
    p = env_file("my_key=value\n")
    result = lint_env_file(p)
    codes = [i.code for i in result.issues]
    assert "W001" in codes


def test_duplicate_key_warning(env_file):
    p = env_file("FOO=bar\nFOO=baz\n")
    result = lint_env_file(p)
    codes = [i.code for i in result.issues]
    assert "W002" in codes


def test_unquoted_whitespace_warning(env_file):
    p = env_file("GREETING=hello world\n")
    result = lint_env_file(p)
    codes = [i.code for i in result.issues]
    assert "W003" in codes


def test_quoted_whitespace_is_ok(env_file):
    p = env_file('GREETING="hello world"\n')
    result = lint_env_file(p)
    codes = [i.code for i in result.issues]
    assert "W003" not in codes


def test_trailing_whitespace_warning(env_file):
    p = env_file("FOO=bar   \n")
    result = lint_env_file(p)
    codes = [i.code for i in result.issues]
    assert "W004" in codes


def test_comments_and_blanks_skipped(env_file):
    p = env_file("# comment\n\nVALID=yes\n")
    result = lint_env_file(p)
    assert result.issues == []


def test_lint_issue_str():
    issue = LintIssue(line_no=3, code="W001", message="Bad key", severity="warning")
    assert "W001" in str(issue)
    assert "3" in str(issue)
    assert "WARNING" in str(issue)


def test_warning_count_and_error_count(env_file):
    p = env_file("my_key=hello world\nFOO=bar\nFOO=baz\n")
    result = lint_env_file(p)
    assert result.warning_count >= 2
    assert result.error_count == 0
    assert result.passed

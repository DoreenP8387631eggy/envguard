"""Tests for envguard.formatter."""
from pathlib import Path
import pytest

from envguard.formatter import (
    FormatChange,
    FormatReport,
    _format_line,
    format_env_file,
    apply_format,
)


@pytest.fixture()
def env_file(tmp_path: Path):
    p = tmp_path / ".env"

    def _write(content: str) -> Path:
        p.write_text(content, encoding="utf-8")
        return p

    return _write


# --- _format_line unit tests ---

def test_format_line_blank_preserved():
    assert _format_line("") == ""


def test_format_line_comment_preserved():
    assert _format_line("# a comment  ") == "# a comment"


def test_format_line_strips_spaces_around_equals():
    assert _format_line("KEY = value") == "KEY=value"


def test_format_line_strips_redundant_double_quotes():
    assert _format_line('KEY="simple"') == "KEY=simple"


def test_format_line_strips_redundant_single_quotes():
    assert _format_line("KEY='simple'") == "KEY=simple"


def test_format_line_keeps_quotes_when_value_has_spaces():
    result = _format_line("KEY=hello world")
    assert result == 'KEY="hello world"'


def test_format_line_already_quoted_with_spaces_unchanged():
    result = _format_line('KEY="hello world"')
    assert result == 'KEY="hello world"'


def test_format_line_no_equals_returned_as_is():
    assert _format_line("JUST_A_KEY") == "JUST_A_KEY"


# --- format_env_file ---

def test_format_env_file_no_changes(env_file):
    p = env_file("KEY=value\n# comment\n\n")
    report = format_env_file(p)
    assert not report.has_changes
    assert report.change_count == 0
    assert report.summary() == "Already formatted — no changes needed."


def test_format_env_file_detects_spacing_issue(env_file):
    p = env_file("KEY = value\n")
    report = format_env_file(p)
    assert report.has_changes
    assert report.change_count == 1
    assert report.changes[0].line_number == 1
    assert "1 line(s) reformatted" in report.summary()


def test_format_env_file_multiple_issues(env_file):
    p = env_file("A = 1\nB='hello'\nC=ok\n")
    report = format_env_file(p)
    assert report.change_count == 2  # A and B need changes; C is fine


# --- apply_format ---

def test_apply_format_rewrites_file(env_file):
    p = env_file("KEY = value\n")
    report = apply_format(p)
    assert report.has_changes
    assert p.read_text(encoding="utf-8").strip() == "KEY=value"


def test_apply_format_no_write_when_clean(env_file, monkeypatch):
    p = env_file("KEY=value\n")
    write_calls = []
    monkeypatch.setattr(Path, "write_text", lambda self, *a, **kw: write_calls.append(1))
    apply_format(p)
    assert write_calls == [], "write_text should not be called for already-formatted file"


def test_apply_format_accepts_precomputed_report(env_file):
    p = env_file("KEY = value\n")
    report = format_env_file(p)
    apply_format(p, report=report)
    assert p.read_text(encoding="utf-8").strip() == "KEY=value"

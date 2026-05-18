"""Tests for envguard.duplicates and envguard.cli_duplicates."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envguard.duplicates import DuplicateEntry, DuplicateReport, find_duplicates
from envguard.cli_duplicates import build_duplicates_parser, run_duplicates


@pytest.fixture()
def env_file(tmp_path: Path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content)
        return p

    return _write


# ---------------------------------------------------------------------------
# Unit tests – find_duplicates
# ---------------------------------------------------------------------------

def test_no_duplicates_clean_file(env_file):
    p = env_file("FOO=bar\nBAZ=qux\n")
    report = find_duplicates(p)
    assert not report.has_duplicates
    assert report.duplicate_count == 0


def test_single_duplicate_detected(env_file):
    p = env_file("FOO=first\nBAR=ok\nFOO=second\n")
    report = find_duplicates(p)
    assert report.has_duplicates
    assert report.duplicate_count == 1
    assert report.duplicates[0].key == "FOO"
    assert report.duplicates[0].lines == [1, 3]


def test_multiple_duplicates(env_file):
    p = env_file("A=1\nB=2\nA=3\nB=4\nC=5\n")
    report = find_duplicates(p)
    assert report.duplicate_count == 2
    keys = {d.key for d in report.duplicates}
    assert keys == {"A", "B"}


def test_comments_and_blanks_ignored(env_file):
    p = env_file("# comment\n\nFOO=bar\n# FOO=ignored\nFOO=baz\n")
    report = find_duplicates(p)
    assert report.duplicate_count == 1
    assert report.duplicates[0].lines == [3, 5]


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        find_duplicates("/nonexistent/.env")


def test_duplicate_entry_str():
    entry = DuplicateEntry(key="SECRET", lines=[2, 7, 11])
    assert "SECRET" in str(entry)
    assert "3x" in str(entry)


def test_report_summary_no_duplicates(env_file):
    p = env_file("X=1\n")
    report = find_duplicates(p)
    assert "no duplicate" in report.summary()


def test_report_summary_with_duplicates(env_file):
    p = env_file("KEY=a\nKEY=b\n")
    report = find_duplicates(p)
    assert "KEY" in report.summary()
    assert "1 duplicate" in report.summary()


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def _args(env_file_path: str, strict: bool = False) -> argparse.Namespace:
    return argparse.Namespace(env_file=env_file_path, strict=strict)


def test_cli_exits_zero_clean(env_file):
    p = env_file("A=1\nB=2\n")
    assert run_duplicates(_args(str(p))) == 0


def test_cli_exits_one_on_duplicate(env_file):
    p = env_file("A=1\nA=2\n")
    assert run_duplicates(_args(str(p))) == 1


def test_cli_exits_two_on_missing_file(tmp_path):
    assert run_duplicates(_args(str(tmp_path / "ghost.env"))) == 2


def test_build_parser_returns_parser():
    parser = build_duplicates_parser()
    ns = parser.parse_args(["some.env"])
    assert ns.env_file == "some.env"
    assert not ns.strict

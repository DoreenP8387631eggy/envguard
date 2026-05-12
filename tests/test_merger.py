"""Tests for envguard.merger."""

from __future__ import annotations

import pytest

from envguard.merger import MergeConflict, MergeStrategy, merge_env_files
from envguard.loader import EnvFileNotFoundError


def write_env(tmp_path, name: str, content: str):
    p = tmp_path / name
    p.write_text(content)
    return str(p)


def test_merge_single_file(tmp_path):
    f = write_env(tmp_path, "a.env", "FOO=bar\nBAZ=qux\n")
    report = merge_env_files([f])
    assert report.merged == {"FOO": "bar", "BAZ": "qux"}
    assert not report.has_conflicts


def test_merge_no_conflicts(tmp_path):
    f1 = write_env(tmp_path, "a.env", "FOO=1\n")
    f2 = write_env(tmp_path, "b.env", "BAR=2\n")
    report = merge_env_files([f1, f2])
    assert report.merged == {"FOO": "1", "BAR": "2"}
    assert not report.has_conflicts


def test_merge_last_wins(tmp_path):
    f1 = write_env(tmp_path, "a.env", "FOO=from_a\n")
    f2 = write_env(tmp_path, "b.env", "FOO=from_b\n")
    report = merge_env_files([f1, f2], strategy=MergeStrategy.LAST_WINS)
    assert report.merged["FOO"] == "from_b"
    assert report.has_conflicts
    assert report.conflicts[0].resolved_from == str(f2)


def test_merge_first_wins(tmp_path):
    f1 = write_env(tmp_path, "a.env", "FOO=from_a\n")
    f2 = write_env(tmp_path, "b.env", "FOO=from_b\n")
    report = merge_env_files([f1, f2], strategy=MergeStrategy.FIRST_WINS)
    assert report.merged["FOO"] == "from_a"
    assert report.conflicts[0].resolved_from == str(f1)


def test_conflict_str(tmp_path):
    f1 = write_env(tmp_path, "a.env", "KEY=alpha\n")
    f2 = write_env(tmp_path, "b.env", "KEY=beta\n")
    report = merge_env_files([f1, f2])
    text = str(report.conflicts[0])
    assert "CONFLICT KEY" in text
    assert "alpha" in text
    assert "beta" in text


def test_summary_no_conflicts(tmp_path):
    f = write_env(tmp_path, "a.env", "X=1\n")
    report = merge_env_files([f])
    assert "conflict" not in report.summary.lower()


def test_summary_with_conflicts(tmp_path):
    f1 = write_env(tmp_path, "a.env", "X=1\n")
    f2 = write_env(tmp_path, "b.env", "X=2\n")
    report = merge_env_files([f1, f2])
    assert "conflict" in report.summary.lower()


def test_missing_file_raises(tmp_path):
    with pytest.raises((FileNotFoundError, EnvFileNotFoundError)):
        merge_env_files([str(tmp_path / "ghost.env")])


def test_ignore_missing(tmp_path):
    f = write_env(tmp_path, "real.env", "REAL=yes\n")
    report = merge_env_files(
        [str(tmp_path / "ghost.env"), str(f)],
        ignore_missing=True,
    )
    assert report.merged == {"REAL": "yes"}


def test_sources_recorded(tmp_path):
    f1 = write_env(tmp_path, "a.env", "A=1\n")
    f2 = write_env(tmp_path, "b.env", "B=2\n")
    report = merge_env_files([f1, f2])
    assert len(report.sources) == 2

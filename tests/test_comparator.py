"""Tests for envguard.comparator."""

from __future__ import annotations

import pytest

from envguard.comparator import (
    VarChange,
    CompareReport,
    compare_env_dicts,
    compare_env_files,
)


# ---------------------------------------------------------------------------
# VarChange
# ---------------------------------------------------------------------------

def test_var_change_added():
    vc = VarChange("FOO", None, "bar")
    assert vc.change_type == "added"
    assert str(vc).startswith("+")


def test_var_change_removed():
    vc = VarChange("FOO", "bar", None)
    assert vc.change_type == "removed"
    assert str(vc).startswith("-")


def test_var_change_modified():
    vc = VarChange("FOO", "old", "new")
    assert vc.change_type == "modified"
    assert str(vc).startswith("~")


# ---------------------------------------------------------------------------
# CompareReport
# ---------------------------------------------------------------------------

def test_compare_report_no_changes():
    report = CompareReport()
    assert not report.has_changes
    assert report.total_changes == 0
    assert report.summary() == "No changes detected."


def test_compare_report_summary_counts():
    report = CompareReport(
        added=[VarChange("A", None, "1")],
        removed=[VarChange("B", "2", None)],
        modified=[VarChange("C", "3", "4"), VarChange("D", "5", "6")],
    )
    assert report.total_changes == 4
    summary = report.summary()
    assert "1 added" in summary
    assert "1 removed" in summary
    assert "2 modified" in summary
    assert "(4 total)" in summary


def test_compare_report_all_changes_order():
    added = VarChange("A", None, "1")
    removed = VarChange("B", "2", None)
    modified = VarChange("C", "3", "4")
    report = CompareReport(added=[added], removed=[removed], modified=[modified])
    assert report.all_changes() == [added, removed, modified]


# ---------------------------------------------------------------------------
# compare_env_dicts
# ---------------------------------------------------------------------------

def test_compare_dicts_identical():
    env = {"FOO": "1", "BAR": "2"}
    report = compare_env_dicts(env, env.copy())
    assert not report.has_changes


def test_compare_dicts_added_key():
    old = {"FOO": "1"}
    new = {"FOO": "1", "BAR": "2"}
    report = compare_env_dicts(old, new)
    assert len(report.added) == 1
    assert report.added[0].key == "BAR"
    assert report.added[0].new_value == "2"


def test_compare_dicts_removed_key():
    old = {"FOO": "1", "BAR": "2"}
    new = {"FOO": "1"}
    report = compare_env_dicts(old, new)
    assert len(report.removed) == 1
    assert report.removed[0].key == "BAR"


def test_compare_dicts_modified_value():
    old = {"FOO": "old"}
    new = {"FOO": "new"}
    report = compare_env_dicts(old, new)
    assert len(report.modified) == 1
    assert report.modified[0].old_value == "old"
    assert report.modified[0].new_value == "new"


def test_compare_dicts_keys_sorted():
    old = {"Z": "1", "A": "2"}
    new = {"Z": "1", "A": "changed", "M": "new"}
    report = compare_env_dicts(old, new)
    keys_added = [c.key for c in report.added]
    keys_modified = [c.key for c in report.modified]
    assert keys_added == sorted(keys_added)
    assert keys_modified == sorted(keys_modified)


# ---------------------------------------------------------------------------
# compare_env_files
# ---------------------------------------------------------------------------

def test_compare_env_files(tmp_path):
    old_file = tmp_path / ".env.old"
    new_file = tmp_path / ".env.new"
    old_file.write_text("FOO=1\nBAR=old\n")
    new_file.write_text("FOO=1\nBAR=new\nBAZ=added\n")

    report, warnings = compare_env_files(str(old_file), str(new_file))
    assert not warnings
    assert len(report.modified) == 1
    assert report.modified[0].key == "BAR"
    assert len(report.added) == 1
    assert report.added[0].key == "BAZ"


def test_compare_env_files_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        compare_env_files(str(tmp_path / "missing.env"), str(tmp_path / "also.env"))

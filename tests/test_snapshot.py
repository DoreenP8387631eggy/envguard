"""Tests for envguard.snapshot module."""

import json
import pytest
from pathlib import Path

from envguard.snapshot import save_snapshot, load_snapshot, compare_snapshots
from envguard.auditor import AuditReport, AuditIssue


def _make_report(issues=None):
    report = AuditReport()
    for issue in (issues or []):
        report.issues.append(issue)
    return report


def test_save_and_load_snapshot(tmp_path):
    report = _make_report([
        AuditIssue(level="error", var_name="DB_URL", message="Missing required variable"),
    ])
    snap_path = str(tmp_path / "snap.json")
    save_snapshot(report, snap_path)

    data = load_snapshot(snap_path)
    assert data["version"] == 1
    assert "timestamp" in data
    assert data["passed"] is False
    assert len(data["issues"]) == 1
    assert data["issues"][0]["var"] == "DB_URL"


def test_save_snapshot_creates_parent_dirs(tmp_path):
    snap_path = str(tmp_path / "nested" / "dir" / "snap.json")
    save_snapshot(_make_report(), snap_path)
    assert Path(snap_path).exists()


def test_compare_snapshots_introduced():
    old = {"passed": True, "issues": []}
    new = {"passed": False, "issues": [{"level": "error", "var": "SECRET", "message": "Missing"}]}
    diff = compare_snapshots(old, new)
    assert len(diff["introduced"]) == 1
    assert diff["introduced"][0]["var"] == "SECRET"
    assert diff["resolved"] == []
    assert diff["status_changed"] is True


def test_compare_snapshots_resolved():
    old = {"passed": False, "issues": [{"level": "error", "var": "SECRET", "message": "Missing"}]}
    new = {"passed": True, "issues": []}
    diff = compare_snapshots(old, new)
    assert len(diff["resolved"]) == 1
    assert diff["resolved"][0]["var"] == "SECRET"
    assert diff["introduced"] == []


def test_compare_snapshots_unchanged():
    issue = {"level": "warning", "var": "LOG_LEVEL", "message": "Deprecated"}
    old = {"passed": False, "issues": [issue]}
    new = {"passed": False, "issues": [issue]}
    diff = compare_snapshots(old, new)
    assert diff["unchanged_count"] == 1
    assert diff["introduced"] == []
    assert diff["resolved"] == []
    assert diff["status_changed"] is False

"""Snapshot utility: save and compare .env audit states over time."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from envguard.auditor import AuditReport, AuditIssue


SNAPSHOT_VERSION = 1


def _report_to_dict(report: AuditReport) -> dict:
    return {
        "version": SNAPSHOT_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "passed": report.passed,
        "issues": [
            {"level": i.level, "var": i.var_name, "message": i.message}
            for i in report.issues
        ],
    }


def save_snapshot(report: AuditReport, path: str) -> None:
    """Persist an audit report as a JSON snapshot file."""
    data = _report_to_dict(report)
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def load_snapshot(path: str) -> dict:
    """Load a previously saved snapshot from disk."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def compare_snapshots(old: dict, new: dict) -> dict:
    """Return a diff summary between two snapshot dicts."""
    old_issues = {(i["level"], i["var"]): i["message"] for i in old.get("issues", [])}
    new_issues = {(i["level"], i["var"]): i["message"] for i in new.get("issues", [])}

    resolved = [k for k in old_issues if k not in new_issues]
    introduced = [k for k in new_issues if k not in old_issues]
    unchanged = [k for k in old_issues if k in new_issues]

    return {
        "resolved": [{"level": k[0], "var": k[1]} for k in resolved],
        "introduced": [{"level": k[0], "var": k[1], "message": new_issues[k]} for k in introduced],
        "unchanged_count": len(unchanged),
        "status_changed": old.get("passed") != new.get("passed"),
    }

"""Formats and outputs AuditReport results in various formats."""

from __future__ import annotations

import json
from enum import Enum
from typing import TextIO
import sys

from envguard.auditor import AuditReport, AuditIssue


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    GITHUB = "github"  # GitHub Actions annotation format


def _issue_to_dict(issue: AuditIssue) -> dict:
    return {
        "level": issue.level,
        "variable": issue.variable,
        "message": issue.message,
    }


def format_text(report: AuditReport) -> str:
    lines = []
    if report.passed:
        lines.append("✅  envguard: all checks passed.")
        return "\n".join(lines)

    lines.append("❌  envguard audit failed:\n")
    if report.errors():
        lines.append("  ERRORS:")
        for issue in report.errors():
            lines.append(f"    [{issue.variable}] {issue.message}")
    if report.warnings():
        lines.append("  WARNINGS:")
        for issue in report.warnings():
            lines.append(f"    [{issue.variable}] {issue.message}")
    lines.append(f"\n  {len(report.errors())} error(s), {len(report.warnings())} warning(s).")
    return "\n".join(lines)


def format_json(report: AuditReport) -> str:
    data = {
        "passed": report.passed,
        "error_count": len(report.errors()),
        "warning_count": len(report.warnings()),
        "issues": [_issue_to_dict(i) for i in report.issues],
    }
    return json.dumps(data, indent=2)


def format_github(report: AuditReport) -> str:
    lines = []
    for issue in report.errors():
        lines.append(f"::error title=envguard [{issue.variable}]::{issue.message}")
    for issue in report.warnings():
        lines.append(f"::warning title=envguard [{issue.variable}]::{issue.message}")
    if not lines:
        lines.append("::notice title=envguard::All checks passed.")
    return "\n".join(lines)


def print_report(
    report: AuditReport,
    fmt: OutputFormat = OutputFormat.TEXT,
    stream: TextIO = sys.stdout,
) -> None:
    """Render *report* in the requested format and write to *stream*."""
    formatters = {
        OutputFormat.TEXT: format_text,
        OutputFormat.JSON: format_json,
        OutputFormat.GITHUB: format_github,
    }
    output = formatters[fmt](report)
    print(output, file=stream)

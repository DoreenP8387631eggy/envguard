"""Output formatting for audit reports."""

import json
from enum import Enum
from typing import Dict, Any

from envguard.auditor import AuditReport, AuditIssue


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    GITHUB = "github"


def _issue_to_dict(issue: AuditIssue) -> Dict[str, Any]:
    return {
        "level": issue.level,
        "variable": issue.variable,
        "message": issue.message,
    }


def format_text(report: AuditReport) -> str:
    lines = []
    if report.passed:
        lines.append("envguard: PASSED — no issues found.")
        return "\n".join(lines)

    lines.append("envguard audit report")
    lines.append("=" * 40)

    if report.errors:
        lines.append(f"ERRORS ({len(report.errors)}):")
        for issue in report.errors:
            lines.append(f"  [ERROR] {issue.variable}: {issue.message}")

    if report.warnings:
        lines.append(f"WARNINGS ({len(report.warnings)}):")
        for issue in report.warnings:
            lines.append(f"  [WARN]  {issue.variable}: {issue.message}")

    lines.append("=" * 40)
    status = "FAILED" if report.errors else "PASSED with warnings"
    lines.append(f"Result: {status}")
    return "\n".join(lines)


def format_json(report: AuditReport) -> str:
    data: Dict[str, Any] = {
        "passed": report.passed,
        "errors": [_issue_to_dict(i) for i in report.errors],
        "warnings": [_issue_to_dict(i) for i in report.warnings],
    }
    return json.dumps(data, indent=2)


def format_github(report: AuditReport) -> str:
    """Emit GitHub Actions workflow command annotations."""
    lines = []
    for issue in report.errors:
        lines.append(f"::error title=envguard [{issue.variable}]::{issue.message}")
    for issue in report.warnings:
        lines.append(f"::warning title=envguard [{issue.variable}]::{issue.message}")
    if not lines:
        lines.append("::notice title=envguard::All environment variables passed validation.")
    return "\n".join(lines)


def format_report(report: AuditReport, fmt: OutputFormat = OutputFormat.TEXT) -> str:
    if fmt == OutputFormat.JSON:
        return format_json(report)
    if fmt == OutputFormat.GITHUB:
        return format_github(report)
    return format_text(report)

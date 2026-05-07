"""Tests for envguard.reporter formatting helpers."""

from __future__ import annotations

import json
from io import StringIO

import pytest

from envguard.auditor import AuditIssue, AuditReport
from envguard.reporter import OutputFormat, format_github, format_json, format_text, print_report


def _make_report(errors=(), warnings=()) -> AuditReport:
    issues = [
        AuditIssue(level="error", variable=v, message=m) for v, m in errors
    ] + [
        AuditIssue(level="warning", variable=v, message=m) for v, m in warnings
    ]
    report = AuditReport(issues=issues)
    return report


def test_format_text_passed():
    report = _make_report()
    output = format_text(report)
    assert "passed" in output
    assert "✅" in output


def test_format_text_with_errors():
    report = _make_report(errors=[("DB_URL", "missing required variable")])
    output = format_text(report)
    assert "DB_URL" in output
    assert "ERRORS" in output
    assert "1 error(s)" in output


def test_format_text_with_warnings():
    report = _make_report(warnings=[("DEBUG", "unexpected value 'maybe'")])
    output = format_text(report)
    assert "DEBUG" in output
    assert "WARNINGS" in output
    assert "1 warning(s)" in output


def test_format_json_passed():
    report = _make_report()
    data = json.loads(format_json(report))
    assert data["passed"] is True
    assert data["error_count"] == 0
    assert data["issues"] == []


def test_format_json_with_issues():
    report = _make_report(
        errors=[("SECRET_KEY", "missing required variable")],
        warnings=[("LOG_LEVEL", "unknown value")],
    )
    data = json.loads(format_json(report))
    assert data["passed"] is False
    assert data["error_count"] == 1
    assert data["warning_count"] == 1
    levels = {i["level"] for i in data["issues"]}
    assert levels == {"error", "warning"}


def test_format_github_passed():
    report = _make_report()
    output = format_github(report)
    assert "::notice" in output
    assert "passed" in output.lower()


def test_format_github_annotations():
    report = _make_report(
        errors=[("API_KEY", "missing")],
        warnings=[("TIMEOUT", "non-integer value")],
    )
    output = format_github(report)
    assert "::error" in output
    assert "API_KEY" in output
    assert "::warning" in output
    assert "TIMEOUT" in output


def test_print_report_writes_to_stream():
    report = _make_report(errors=[("PORT", "must be integer")])
    stream = StringIO()
    print_report(report, fmt=OutputFormat.JSON, stream=stream)
    stream.seek(0)
    data = json.loads(stream.read())
    assert data["error_count"] == 1

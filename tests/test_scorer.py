"""Unit tests for envguard.scorer."""
from __future__ import annotations

from envguard.auditor import AuditIssue, AuditReport
from envguard.linter import LintIssue, LintResult
from envguard.profiler import ProfileIssue, ProfileReport
from envguard.scorer import HealthScore, ScoreBreakdown, _grade, compute_score


# ---------------------------------------------------------------------------
# _grade helper
# ---------------------------------------------------------------------------

def test_grade_a():
    assert _grade(95) == "A"
    assert _grade(90) == "A"


def test_grade_b():
    assert _grade(85) == "B"


def test_grade_c():
    assert _grade(72) == "C"


def test_grade_d():
    assert _grade(65) == "D"


def test_grade_f():
    assert _grade(50) == "F"
    assert _grade(0) == "F"


# ---------------------------------------------------------------------------
# Perfect score
# ---------------------------------------------------------------------------

def test_perfect_score_no_reports():
    h = compute_score()
    assert h.score == 100
    assert h.grade == "A"
    assert h.passed is True


def test_perfect_score_clean_reports(simple_audit, simple_lint, simple_profile):
    h = compute_score(audit=simple_audit, lint=simple_lint, profile=simple_profile)
    assert h.score == 100
    assert h.breakdown.audit_penalty == 0.0
    assert h.breakdown.lint_penalty == 0.0
    assert h.breakdown.profile_penalty == 0.0


# ---------------------------------------------------------------------------
# Penalty accumulation
# ---------------------------------------------------------------------------

def test_audit_error_penalty():
    report = _audit_with(errors=2, warnings=0)
    h = compute_score(audit=report)
    assert h.breakdown.audit_penalty == 20.0
    assert h.score == 80


def test_audit_warning_penalty():
    report = _audit_with(errors=0, warnings=3)
    h = compute_score(audit=report)
    assert h.breakdown.audit_penalty == 9.0
    assert h.score == 91


def test_audit_penalty_capped():
    report = _audit_with(errors=10, warnings=10)
    h = compute_score(audit=report)
    assert h.breakdown.audit_penalty == 55.0  # 40 + 15


def test_lint_penalty():
    result = _lint_with(errors=3)
    h = compute_score(lint=result)
    assert h.breakdown.lint_penalty == 15.0
    assert h.score == 85


def test_lint_penalty_capped():
    result = _lint_with(errors=10)
    h = compute_score(lint=result)
    assert h.breakdown.lint_penalty == 20.0


def test_profile_penalty():
    report = _profile_with(errors=2)
    h = compute_score(profile=report)
    assert h.breakdown.profile_penalty == 10.0
    assert h.score == 90


def test_combined_penalties_floored_at_zero():
    h = compute_score(
        audit=_audit_with(errors=5, warnings=5),
        lint=_lint_with(errors=5),
        profile=_profile_with(errors=5),
    )
    assert h.score >= 0


def test_passed_below_threshold():
    h = compute_score(audit=_audit_with(errors=4, warnings=0))
    assert h.passed is False


def test_str_contains_score():
    h = compute_score()
    assert "100/100" in str(h)


def test_notes_populated():
    h = compute_score(audit=_audit_with(errors=1, warnings=2))
    combined = " ".join(h.breakdown.notes)
    assert "audit error" in combined
    assert "audit warning" in combined


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

import pytest


@pytest.fixture
def simple_audit():
    return _audit_with(errors=0, warnings=0)


@pytest.fixture
def simple_lint():
    return _lint_with(errors=0)


@pytest.fixture
def simple_profile():
    return _profile_with(errors=0)


def _audit_with(errors: int, warnings: int) -> AuditReport:
    err_issues = [AuditIssue("ERROR", f"VAR{i}", "missing") for i in range(errors)]
    warn_issues = [AuditIssue("WARNING", f"WVAR{i}", "bad value") for i in range(warnings)]
    return AuditReport(issues=err_issues + warn_issues)


def _lint_with(errors: int) -> LintResult:
    issues = [LintIssue(line_no=i + 1, message="bad line", raw_line=f"line{i}") for i in range(errors)]
    return LintResult(issues=issues)


def _profile_with(errors: int) -> ProfileReport:
    issues = [ProfileIssue(key=f"KEY{i}", message="weak") for i in range(errors)]
    return ProfileReport(issues=issues)

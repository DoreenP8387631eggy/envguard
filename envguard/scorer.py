"""Env file health scorer — produces a 0-100 score based on audit, lint,
profile, and interpolation results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envguard.auditor import AuditReport
from envguard.linter import LintResult
from envguard.profiler import ProfileReport


@dataclass
class ScoreBreakdown:
    """Per-category penalty details."""
    audit_penalty: float = 0.0
    lint_penalty: float = 0.0
    profile_penalty: float = 0.0
    notes: List[str] = field(default_factory=list)


@dataclass
class HealthScore:
    score: int  # 0-100
    grade: str  # A-F
    breakdown: ScoreBreakdown

    @property
    def passed(self) -> bool:
        return self.score >= 70

    def __str__(self) -> str:
        lines = [
            f"Health Score: {self.score}/100  (Grade {self.grade})",
            f"  Audit penalty  : -{self.breakdown.audit_penalty:.1f}",
            f"  Lint penalty   : -{self.breakdown.lint_penalty:.1f}",
            f"  Profile penalty: -{self.breakdown.profile_penalty:.1f}",
        ]
        for note in self.breakdown.notes:
            lines.append(f"  • {note}")
        return "\n".join(lines)


_GRADE_THRESHOLDS = [(90, "A"), (80, "B"), (70, "C"), (60, "D")]


def _grade(score: int) -> str:
    for threshold, letter in _GRADE_THRESHOLDS:
        if score >= threshold:
            return letter
    return "F"


def compute_score(
    audit: Optional[AuditReport] = None,
    lint: Optional[LintResult] = None,
    profile: Optional[ProfileReport] = None,
) -> HealthScore:
    """Compute a health score from available report objects.

    Penalties:
      - Each audit error   : -10 pts  (max -40)
      - Each audit warning :  -3 pts  (max -15)
      - Each lint error    :  -5 pts  (max -20)
      - Each profile error :  -5 pts  (max -25)
    """
    breakdown = ScoreBreakdown()
    total_penalty = 0.0

    if audit is not None:
        p = min(len(audit.errors) * 10.0, 40.0) + min(len(audit.warnings) * 3.0, 15.0)
        breakdown.audit_penalty = p
        total_penalty += p
        if audit.errors:
            breakdown.notes.append(f"{len(audit.errors)} audit error(s)")
        if audit.warnings:
            breakdown.notes.append(f"{len(audit.warnings)} audit warning(s)")

    if lint is not None:
        p = min(lint.error_count * 5.0, 20.0)
        breakdown.lint_penalty = p
        total_penalty += p
        if lint.error_count:
            breakdown.notes.append(f"{lint.error_count} lint issue(s)")

    if profile is not None:
        p = min(len(profile.errors) * 5.0, 25.0)
        breakdown.profile_penalty = p
        total_penalty += p
        if profile.errors:
            breakdown.notes.append(f"{len(profile.errors)} profile issue(s)")

    raw = 100.0 - total_penalty
    score = max(0, min(100, int(round(raw))))
    return HealthScore(score=score, grade=_grade(score), breakdown=breakdown)

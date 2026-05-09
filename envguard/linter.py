"""Lint .env files for style and best-practice issues."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class LintIssue:
    line_no: int
    code: str
    message: str
    severity: str = "warning"  # 'warning' | 'error'

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] Line {self.line_no} ({self.code}): {self.message}"


@dataclass
class LintResult:
    path: str
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")


_KEY_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')
_ASSIGN_RE = re.compile(r'^([^=]+)=(.*)$')


def lint_env_file(path: str | Path) -> LintResult:
    """Run all lint checks against a .env file and return a LintResult."""
    path = Path(path)
    result = LintResult(path=str(path))

    if not path.exists():
        result.issues.append(LintIssue(0, "E001", f"File not found: {path}", "error"))
        return result

    lines = path.read_text(encoding="utf-8").splitlines()
    seen_keys: dict[str, int] = {}

    for lineno, raw in enumerate(lines, start=1):
        line = raw.strip()

        # Skip blanks and comments
        if not line or line.startswith("#"):
            continue

        m = _ASSIGN_RE.match(line)
        if not m:
            result.issues.append(LintIssue(lineno, "E002", f"Line is not a valid KEY=VALUE assignment", "error"))
            continue

        key, value = m.group(1).strip(), m.group(2).strip()

        # W001: key not uppercase
        if not _KEY_RE.match(key):
            result.issues.append(LintIssue(lineno, "W001", f"Key '{key}' should be UPPER_SNAKE_CASE", "warning"))

        # W002: duplicate key
        if key in seen_keys:
            result.issues.append(LintIssue(lineno, "W002",
                f"Duplicate key '{key}' (first seen on line {seen_keys[key]})", "warning"))
        else:
            seen_keys[key] = lineno

        # W003: value contains unquoted whitespace
        if value and not (value.startswith('"') or value.startswith("'")):
            if re.search(r'\s', value):
                result.issues.append(LintIssue(lineno, "W003",
                    f"Value for '{key}' contains whitespace but is not quoted", "warning"))

        # W004: trailing whitespace on the raw line
        if raw != raw.rstrip():
            result.issues.append(LintIssue(lineno, "W004", f"Trailing whitespace on line", "warning"))

    return result

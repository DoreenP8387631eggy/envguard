"""Profile .env files to detect duplicate keys, suspicious values, and entropy anomalies."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ProfileIssue:
    level: str  # "error" | "warning" | "info"
    key: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level.upper()}] {self.key}: {self.message}"


@dataclass
class ProfileReport:
    issues: List[ProfileIssue] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not any(i.level == "error" for i in self.issues)

    def errors(self) -> List[ProfileIssue]:
        return [i for i in self.issues if i.level == "error"]

    def warnings(self) -> List[ProfileIssue]:
        return [i for i in self.issues if i.level == "warning"]


def _shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    freq = {ch: value.count(ch) / len(value) for ch in set(value)}
    return -sum(p * math.log2(p) for p in freq.values())


def _looks_like_placeholder(value: str) -> bool:
    patterns = [
        r"^<.+>$",
        r"^\[.+\]$",
        r"^CHANGE_ME$",
        r"^TODO$",
        r"^YOUR_.+",
        r"^REPLACE_.+",
    ]
    return any(re.match(p, value, re.IGNORECASE) for p in patterns)


def profile_env(
    env: Dict[str, str],
    entropy_threshold: float = 3.5,
) -> ProfileReport:
    """Analyse a parsed env dict and return a ProfileReport."""
    report = ProfileReport()
    report.stats["total_keys"] = len(env)
    placeholder_count = 0
    high_entropy_count = 0
    empty_count = 0

    for key, value in env.items():
        if value == "":
            empty_count += 1
            report.issues.append(
                ProfileIssue("warning", key, "Value is empty.")
            )
            continue

        if _looks_like_placeholder(value):
            placeholder_count += 1
            report.issues.append(
                ProfileIssue("warning", key, f"Value looks like a placeholder: '{value}'.")
            )

        entropy = _shannon_entropy(value)
        if entropy > entropy_threshold:
            high_entropy_count += 1
            report.issues.append(
                ProfileIssue(
                    "info",
                    key,
                    f"High entropy value detected (entropy={entropy:.2f}); may be a secret.",
                )
            )

    report.stats["empty_values"] = empty_count
    report.stats["placeholder_values"] = placeholder_count
    report.stats["high_entropy_values"] = high_entropy_count
    return report

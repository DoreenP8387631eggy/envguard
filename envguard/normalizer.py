"""Normalize .env file values: trim whitespace, unify quote styles, and
standardise boolean/numeric representations."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Canonical truthy/falsy spellings accepted as booleans
_TRUE_VALUES = {"true", "yes", "1", "on"}
_FALSE_VALUES = {"false", "no", "0", "off"}


@dataclass
class NormalizeChange:
    """Records a single value normalisation that was applied."""

    key: str
    original: str
    normalized: str
    reason: str

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.key}: {self.original!r} -> {self.normalized!r} ({self.reason})"


@dataclass
class NormalizeReport:
    """Aggregated result of normalising an env mapping."""

    changes: List[NormalizeChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)

    @property
    def change_count(self) -> int:
        return len(self.changes)

    def summary(self) -> str:
        if not self.has_changes:
            return "No normalization changes."
        lines = [f"{self.change_count} normalization change(s):"]
        for c in self.changes:
            lines.append(f"  {c}")
        return "\n".join(lines)


def _strip_outer_quotes(value: str) -> Tuple[str, Optional[str]]:
    """Remove surrounding single or double quotes; return (stripped, reason)."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1], f"removed {value[0]!r} quotes"
    return value, None


def _normalize_bool(value: str) -> Tuple[str, Optional[str]]:
    """Canonicalise boolean-like values to 'true' or 'false'."""
    lower = value.lower()
    if lower in _TRUE_VALUES and value != "true":
        return "true", f"normalised boolean {value!r} -> 'true'"
    if lower in _FALSE_VALUES and value != "false":
        return "false", f"normalised boolean {value!r} -> 'false'"
    return value, None


def _normalize_whitespace(value: str) -> Tuple[str, Optional[str]]:
    """Strip leading/trailing whitespace."""
    stripped = value.strip()
    if stripped != value:
        return stripped, "stripped surrounding whitespace"
    return value, None


def normalize_value(key: str, value: str) -> Tuple[str, List[NormalizeChange]]:
    """Apply all normalization passes to *value* and return (result, changes)."""
    changes: List[NormalizeChange] = []

    for transform in (_strip_outer_quotes, _normalize_whitespace, _normalize_bool):
        new_value, reason = transform(value)
        if reason is not None:
            changes.append(NormalizeChange(key=key, original=value, normalized=new_value, reason=reason))
            value = new_value

    return value, changes


def normalize_env(env: Dict[str, str]) -> Tuple[Dict[str, str], NormalizeReport]:
    """Normalise every value in *env*; return updated mapping and a report."""
    report = NormalizeReport()
    result: Dict[str, str] = {}

    for key, raw_value in env.items():
        normalized, changes = normalize_value(key, raw_value)
        result[key] = normalized
        report.changes.extend(changes)

    return result, report

"""Compare two .env files or snapshots and produce a structured change report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class VarChange:
    key: str
    old_value: Optional[str]
    new_value: Optional[str]

    @property
    def change_type(self) -> str:
        if self.old_value is None:
            return "added"
        if self.new_value is None:
            return "removed"
        return "modified"

    def __str__(self) -> str:
        if self.change_type == "added":
            return f"+ {self.key}={self.new_value!r}"
        if self.change_type == "removed":
            return f"- {self.key}={self.old_value!r}"
        return f"~ {self.key}: {self.old_value!r} -> {self.new_value!r}"


@dataclass
class CompareReport:
    added: List[VarChange] = field(default_factory=list)
    removed: List[VarChange] = field(default_factory=list)
    modified: List[VarChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.modified)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.modified)

    def all_changes(self) -> List[VarChange]:
        return self.added + self.removed + self.modified

    def summary(self) -> str:
        if not self.has_changes:
            return "No changes detected."
        parts = []
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.removed:
            parts.append(f"{len(self.removed)} removed")
        if self.modified:
            parts.append(f"{len(self.modified)} modified")
        return ", ".join(parts) + f" ({self.total_changes} total)"


def compare_env_dicts(
    old: Dict[str, str],
    new: Dict[str, str],
) -> CompareReport:
    """Compare two env dicts and return a CompareReport."""
    report = CompareReport()
    all_keys = set(old) | set(new)

    for key in sorted(all_keys):
        old_val = old.get(key)
        new_val = new.get(key)

        if old_val is None and new_val is not None:
            report.added.append(VarChange(key, None, new_val))
        elif old_val is not None and new_val is None:
            report.removed.append(VarChange(key, old_val, None))
        elif old_val != new_val:
            report.modified.append(VarChange(key, old_val, new_val))

    return report


def compare_env_files(
    old_path: str,
    new_path: str,
) -> Tuple[CompareReport, List[str]]:
    """Load two .env files and compare them. Returns (report, warnings)."""
    from envguard.loader import load_env_file

    warnings: List[str] = []
    old_env = load_env_file(old_path)
    new_env = load_env_file(new_path)
    report = compare_env_dicts(old_env, new_env)
    return report, warnings

"""Sort and group .env file variables by prefix or alphabetically."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class SortReport:
    """Result of a sort operation on an env file."""

    original_order: List[Tuple[str, str]] = field(default_factory=list)
    sorted_order: List[Tuple[str, str]] = field(default_factory=list)
    groups: Dict[str, List[Tuple[str, str]]] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return self.original_order != self.sorted_order

    @property
    def change_count(self) -> int:
        orig_keys = [k for k, _ in self.original_order]
        sorted_keys = [k for k, _ in self.sorted_order]
        return sum(1 for i, (o, s) in enumerate(zip(orig_keys, sorted_keys)) if o != s)

    def summary(self) -> str:
        if not self.has_changes:
            return "Already sorted — no changes needed."
        return (
            f"{self.change_count} variable(s) would be reordered across "
            f"{len(self.groups)} group(s)."
        )


def _get_prefix(key: str) -> str:
    """Return the prefix of a key (part before the first underscore)."""
    return key.split("_")[0].upper() if "_" in key else key.upper()


def sort_env(
    env: Dict[str, str],
    group_by_prefix: bool = False,
) -> SortReport:
    """Sort environment variables alphabetically or grouped by prefix.

    Args:
        env: Mapping of key -> value pairs.
        group_by_prefix: When True, group keys by their prefix before sorting
                         within each group.

    Returns:
        A SortReport describing the original and sorted orders.
    """
    original: List[Tuple[str, str]] = list(env.items())

    if group_by_prefix:
        groups: Dict[str, List[Tuple[str, str]]] = {}
        for key, value in original:
            prefix = _get_prefix(key)
            groups.setdefault(prefix, []).append((key, value))

        sorted_groups: Dict[str, List[Tuple[str, str]]] = {
            prefix: sorted(pairs, key=lambda p: p[0])
            for prefix, pairs in sorted(groups.items())
        }
        sorted_pairs: List[Tuple[str, str]] = [
            pair for pairs in sorted_groups.values() for pair in pairs
        ]
        return SortReport(
            original_order=original,
            sorted_order=sorted_pairs,
            groups=sorted_groups,
        )

    sorted_pairs = sorted(original, key=lambda p: p[0])
    single_group = {"ALL": sorted_pairs}
    return SortReport(
        original_order=original,
        sorted_order=sorted_pairs,
        groups=single_group,
    )


def render_sorted_env(report: SortReport, group_by_prefix: bool = False) -> str:
    """Render the sorted env variables as a .env-formatted string."""
    if not group_by_prefix or len(report.groups) <= 1:
        return "\n".join(f"{k}={v}" for k, v in report.sorted_order)

    sections: List[str] = []
    for prefix, pairs in report.groups.items():
        header = f"# --- {prefix} ---"
        body = "\n".join(f"{k}={v}" for k, v in pairs)
        sections.append(f"{header}\n{body}")
    return "\n\n".join(sections)

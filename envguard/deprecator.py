"""Detect deprecated or renamed environment variables in a .env file."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DeprecationEntry:
    """Describes a single deprecated variable."""

    key: str
    replacement: Optional[str] = None
    reason: Optional[str] = None

    def __str__(self) -> str:
        parts = [f"{self.key} is deprecated"]
        if self.replacement:
            parts.append(f"use '{self.replacement}' instead")
        if self.reason:
            parts.append(f"({self.reason})")
        return "; ".join(parts)


@dataclass
class DeprecationReport:
    """Result of scanning an env dict against a deprecation registry."""

    hits: List[DeprecationEntry] = field(default_factory=list)

    @property
    def has_hits(self) -> bool:
        return bool(self.hits)

    @property
    def hit_count(self) -> int:
        return len(self.hits)

    def summary(self) -> str:
        if not self.has_hits:
            return "No deprecated variables found."
        lines = [f"Found {self.hit_count} deprecated variable(s):"]
        for h in self.hits:
            lines.append(f"  - {h}")
        return "\n".join(lines)


# Registry type: mapping of deprecated key -> DeprecationEntry
DeprecationRegistry = Dict[str, DeprecationEntry]


def build_registry(entries: List[Dict]) -> DeprecationRegistry:
    """Build a registry from a list of dicts with keys: key, replacement, reason."""
    registry: DeprecationRegistry = {}
    for item in entries:
        key = item["key"]
        registry[key] = DeprecationEntry(
            key=key,
            replacement=item.get("replacement"),
            reason=item.get("reason"),
        )
    return registry


def scan_for_deprecated(
    env: Dict[str, str],
    registry: DeprecationRegistry,
) -> DeprecationReport:
    """Return a DeprecationReport listing any keys present in env that are deprecated."""
    hits: List[DeprecationEntry] = [
        registry[key] for key in env if key in registry
    ]
    return DeprecationReport(hits=hits)

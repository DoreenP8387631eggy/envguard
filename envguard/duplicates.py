"""Detect duplicate keys within a .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class DuplicateEntry:
    key: str
    lines: List[int]  # 1-based line numbers where the key appears

    def __str__(self) -> str:
        locs = ", ".join(str(ln) for ln in self.lines)
        return f"{self.key} defined {len(self.lines)}x (lines {locs})"


@dataclass
class DuplicateReport:
    source: str
    duplicates: List[DuplicateEntry] = field(default_factory=list)

    @property
    def has_duplicates(self) -> bool:
        return bool(self.duplicates)

    @property
    def duplicate_count(self) -> int:
        return len(self.duplicates)

    def summary(self) -> str:
        if not self.has_duplicates:
            return f"{self.source}: no duplicate keys found."
        keys = ", ".join(d.key for d in self.duplicates)
        return (
            f"{self.source}: {self.duplicate_count} duplicate key(s) found: {keys}"
        )


def find_duplicates(path: str | Path) -> DuplicateReport:
    """Parse *path* and return a report of any keys defined more than once."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f".env file not found: {path}")

    seen: Dict[str, List[int]] = {}
    with path.open(encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key = line.split("=", 1)[0].strip()
            if not key:
                continue
            seen.setdefault(key, []).append(lineno)

    duplicates = [
        DuplicateEntry(key=k, lines=v) for k, v in seen.items() if len(v) > 1
    ]
    return DuplicateReport(source=str(path), duplicates=duplicates)

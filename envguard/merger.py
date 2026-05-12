"""Merge multiple .env files with configurable precedence and conflict reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from envguard.loader import load_env_file


class MergeStrategy(str, Enum):
    FIRST_WINS = "first_wins"   # earliest file in the list takes precedence
    LAST_WINS = "last_wins"     # latest file in the list takes precedence


@dataclass
class MergeConflict:
    key: str
    values: List[Tuple[str, str]]  # list of (source_file, value)
    resolved_value: str
    resolved_from: str

    def __str__(self) -> str:
        sources = ", ".join(f"{f}={v!r}" for f, v in self.values)
        return (
            f"CONFLICT {self.key}: [{sources}] "
            f"-> resolved to {self.resolved_value!r} from {self.resolved_from}"
        )


@dataclass
class MergeReport:
    merged: Dict[str, str] = field(default_factory=dict)
    conflicts: List[MergeConflict] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    @property
    def summary(self) -> str:
        lines = [f"Merged {len(self.sources)} file(s), {len(self.merged)} variable(s)"]
        if self.conflicts:
            lines.append(f"{len(self.conflicts)} conflict(s) detected")
        return "; ".join(lines)


def merge_env_files(
    paths: List[str],
    strategy: MergeStrategy = MergeStrategy.LAST_WINS,
    ignore_missing: bool = False,
) -> MergeReport:
    """Merge multiple .env files according to *strategy*.

    Parameters
    ----------
    paths:
        Ordered list of .env file paths to merge.
    strategy:
        Conflict resolution strategy.
    ignore_missing:
        When True, silently skip files that do not exist.
    """
    report = MergeReport(sources=list(paths))
    # key -> list of (source, value)
    seen: Dict[str, List[Tuple[str, str]]] = {}

    for path in paths:
        try:
            env = load_env_file(path)
        except FileNotFoundError:
            if ignore_missing:
                continue
            raise

        for key, value in env.items():
            seen.setdefault(key, []).append((path, value))

    for key, occurrences in seen.items():
        if len(occurrences) == 1:
            report.merged[key] = occurrences[0][1]
        else:
            if strategy == MergeStrategy.FIRST_WINS:
                winner_path, winner_value = occurrences[0]
            else:  # LAST_WINS
                winner_path, winner_value = occurrences[-1]

            report.merged[key] = winner_value
            report.conflicts.append(
                MergeConflict(
                    key=key,
                    values=occurrences,
                    resolved_value=winner_value,
                    resolved_from=winner_path,
                )
            )

    return report

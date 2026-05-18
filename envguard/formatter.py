"""Formatter: canonically re-format a .env file for consistent style."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envguard.loader import load_env_file


@dataclass
class FormatChange:
    line_number: int
    original: str
    formatted: str

    def __str__(self) -> str:
        return f"line {self.line_number}: {self.original!r} -> {self.formatted!r}"


@dataclass
class FormatReport:
    changes: List[FormatChange] = field(default_factory=list)
    output_lines: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)

    @property
    def change_count(self) -> int:
        return len(self.changes)

    def summary(self) -> str:
        if not self.has_changes:
            return "Already formatted — no changes needed."
        return f"{self.change_count} line(s) reformatted."


def _format_line(line: str) -> str:
    """Return the canonical form of a single .env line."""
    stripped = line.rstrip("\n")
    # Preserve blank lines and comments as-is (strip trailing spaces only)
    if not stripped.strip() or stripped.lstrip().startswith("#"):
        return stripped.rstrip()
    if "=" not in stripped:
        return stripped.rstrip()
    key, _, value = stripped.partition("=")
    key = key.strip()
    value = value.strip()
    # Normalise: no spaces around '=', value unquoted unless it contains spaces
    if " " in value and not (value.startswith('"') and value.endswith('"')):
        value = f'"{value}"'
    # Strip redundant surrounding quotes for simple values
    elif len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        inner = value[1:-1]
        if " " not in inner and "#" not in inner:
            value = inner
    return f"{key}={value}"


def format_env_file(path: Path) -> FormatReport:
    """Read *path*, compute canonical formatting, return a FormatReport."""
    raw_lines = Path(path).read_text(encoding="utf-8").splitlines()
    report = FormatReport()
    for i, raw in enumerate(raw_lines, start=1):
        formatted = _format_line(raw)
        report.output_lines.append(formatted)
        if formatted != raw.rstrip("\n"):
            report.changes.append(FormatChange(i, raw.rstrip("\n"), formatted))
    return report


def apply_format(path: Path, report: Optional[FormatReport] = None) -> FormatReport:
    """Rewrite *path* with canonical formatting; compute report if not given."""
    if report is None:
        report = format_env_file(path)
    if report.has_changes:
        Path(path).write_text("\n".join(report.output_lines) + "\n", encoding="utf-8")
    return report

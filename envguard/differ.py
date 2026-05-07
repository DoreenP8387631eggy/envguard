"""Diff two .env files or a .env file against a schema to surface drift."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .loader import load_env_file
from .schema import EnvSchema


@dataclass
class DiffResult:
    """Result of comparing two sets of environment variables."""

    only_in_left: Set[str] = field(default_factory=set)
    only_in_right: Set[str] = field(default_factory=set)
    value_changed: Dict[str, tuple] = field(default_factory=dict)  # key -> (left, right)
    common: Set[str] = field(default_factory=set)

    @property
    def has_diff(self) -> bool:
        return bool(self.only_in_left or self.only_in_right or self.value_changed)

    def summary(self) -> str:
        lines: List[str] = []
        for key in sorted(self.only_in_left):
            lines.append(f"- {key}  (removed)")
        for key in sorted(self.only_in_right):
            lines.append(f"+ {key}  (added)")
        for key, (lv, rv) in sorted(self.value_changed.items()):
            lines.append(f"~ {key}  '{lv}' -> '{rv}'")
        if not lines:
            lines.append("No differences found.")
        return "\n".join(lines)


def diff_env_files(
    left_path: str,
    right_path: str,
    *,
    mask_values: bool = True,
) -> DiffResult:
    """Compare two .env files and return a DiffResult."""
    left = load_env_file(left_path)
    right = load_env_file(right_path)
    return _diff_dicts(left, right, mask_values=mask_values)


def diff_env_against_schema(
    env_path: str,
    schema: EnvSchema,
) -> DiffResult:
    """Compare a .env file against declared schema keys (values ignored for schema side)."""
    env = load_env_file(env_path)
    schema_keys: Dict[str, Optional[str]] = {k: None for k in schema._vars}
    return _diff_dicts(env, schema_keys, mask_values=False)


def _diff_dicts(
    left: Dict[str, Optional[str]],
    right: Dict[str, Optional[str]],
    *,
    mask_values: bool,
) -> DiffResult:
    left_keys = set(left)
    right_keys = set(right)
    result = DiffResult(
        only_in_left=left_keys - right_keys,
        only_in_right=right_keys - left_keys,
        common=left_keys & right_keys,
    )
    for key in result.common:
        lv = left[key]
        rv = right[key]
        if lv != rv:
            if mask_values:
                lv = "***" if lv else lv
                rv = "***" if rv else rv
            result.value_changed[key] = (lv, rv)
    return result

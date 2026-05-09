"""Utilities for masking sensitive environment variable values in output."""

from __future__ import annotations

import re
from typing import Dict, Iterable, Optional

# Patterns that suggest a variable holds a sensitive value
_SENSITIVE_PATTERNS: list[re.Pattern] = [
    re.compile(r"(password|passwd|pwd)", re.IGNORECASE),
    re.compile(r"(secret|token|api[_-]?key|auth[_-]?key)", re.IGNORECASE),
    re.compile(r"(private[_-]?key|signing[_-]?key)", re.IGNORECASE),
    re.compile(r"(credential|access[_-]?key|client[_-]?secret)", re.IGNORECASE),
]

_MASK_PLACEHOLDER = "***"
_PARTIAL_VISIBLE = 4  # characters shown at start when partial masking is used


def is_sensitive(var_name: str) -> bool:
    """Return True if *var_name* looks like it holds a sensitive value."""
    return any(pattern.search(var_name) for pattern in _SENSITIVE_PATTERNS)


def mask_value(
    value: str,
    *,
    partial: bool = False,
    placeholder: str = _MASK_PLACEHOLDER,
) -> str:
    """Return a masked representation of *value*.

    Args:
        value: The raw secret value.
        partial: When True, reveal the first few characters followed by the
                 placeholder so reviewers can distinguish between secrets.
        placeholder: The string used to replace (or append to) the value.
    """
    if not value:
        return placeholder
    if partial and len(value) > _PARTIAL_VISIBLE:
        return value[:_PARTIAL_VISIBLE] + placeholder
    return placeholder


def mask_env(
    env: Dict[str, str],
    sensitive_keys: Optional[Iterable[str]] = None,
    *,
    partial: bool = False,
    extra_patterns: Optional[Iterable[re.Pattern]] = None,
) -> Dict[str, str]:
    """Return a copy of *env* with sensitive values masked.

    Args:
        env: Mapping of variable names to values.
        sensitive_keys: Explicit set of keys to always mask.  If None, keys
                        are classified automatically via :func:`is_sensitive`.
        partial: Passed through to :func:`mask_value`.
        extra_patterns: Additional compiled regex patterns used to detect
                        sensitive variable names.
    """
    explicit: set[str] = set(sensitive_keys) if sensitive_keys is not None else set()
    patterns = list(_SENSITIVE_PATTERNS)
    if extra_patterns:
        patterns.extend(extra_patterns)

    def _should_mask(key: str) -> bool:
        if key in explicit:
            return True
        return any(p.search(key) for p in patterns)

    return {
        key: (mask_value(val, partial=partial) if _should_mask(key) else val)
        for key, val in env.items()
    }

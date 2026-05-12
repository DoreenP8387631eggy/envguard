"""Redactor: produce a sanitized copy of a .env file with sensitive values replaced."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from envguard.masker import is_sensitive, mask_value

# Matches KEY=VALUE (with optional export prefix and quoted values)
_ASSIGNMENT_RE = re.compile(
    r'^(?P<prefix>export\s+)?(?P<key>[A-Za-z_][A-Za-z0-9_]*)(?P<sep>\s*=\s*)(?P<value>.*)$'
)


def redact_line(
    line: str,
    placeholder: str = "***",
    extra_sensitive: Optional[List[str]] = None,
) -> str:
    """Return a single .env line with the value replaced if the key is sensitive.

    Non-assignment lines (comments, blanks) are returned unchanged.
    """
    stripped = line.rstrip("\n")
    m = _ASSIGNMENT_RE.match(stripped)
    if not m:
        return line

    key = m.group("key")
    sensitive_keys = set(extra_sensitive or [])
    if is_sensitive(key) or key in sensitive_keys:
        prefix = m.group("prefix") or ""
        sep = m.group("sep")
        redacted = f"{prefix}{key}{sep}{placeholder}"
        # Preserve trailing newline if present
        return redacted + ("\n" if line.endswith("\n") else "")
    return line


def redact_env_dict(
    env: Dict[str, str],
    placeholder: str = "***",
    extra_sensitive: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Return a new dict with sensitive values masked."""
    sensitive_keys = set(extra_sensitive or [])
    return {
        k: (mask_value(v, placeholder) if (is_sensitive(k) or k in sensitive_keys) else v)
        for k, v in env.items()
    }


def redact_env_file(
    source: Path,
    destination: Optional[Path] = None,
    placeholder: str = "***",
    extra_sensitive: Optional[List[str]] = None,
) -> Tuple[str, int]:
    """Read *source*, redact sensitive lines, write to *destination* (or return only).

    Returns ``(redacted_content, redacted_count)``.
    """
    if not source.exists():
        raise FileNotFoundError(f"Env file not found: {source}")

    lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
    redacted_lines: List[str] = []
    count = 0

    for line in lines:
        new_line = redact_line(line, placeholder=placeholder, extra_sensitive=extra_sensitive)
        if new_line != line:
            count += 1
        redacted_lines.append(new_line)

    content = "".join(redacted_lines)

    if destination is not None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    return content, count

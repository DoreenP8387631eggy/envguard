"""Loads and parses .env files into a dictionary of key-value pairs."""

import os
import re
from pathlib import Path
from typing import Dict, Optional


class EnvFileNotFoundError(FileNotFoundError):
    """Raised when the specified .env file does not exist."""


class EnvParseError(ValueError):
    """Raised when a line in the .env file cannot be parsed."""


_LINE_RE = re.compile(
    r"^\s*(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)\s*$"
)


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    for quote in ('"', "'"):
        if value.startswith(quote) and value.endswith(quote) and len(value) >= 2:
            return value[1:-1]
    return value


def load_env_file(path: str = ".env") -> Dict[str, str]:
    """Parse a .env file and return its contents as a plain dict.

    Args:
        path: Path to the .env file (default: ".env").

    Returns:
        A dictionary mapping variable names to their string values.

    Raises:
        EnvFileNotFoundError: If the file does not exist.
        EnvParseError: If a non-comment, non-blank line cannot be parsed.
    """
    env_path = Path(path)
    if not env_path.exists():
        raise EnvFileNotFoundError(f".env file not found: {path}")

    result: Dict[str, str] = {}

    with env_path.open(encoding="utf-8") as fh:
        for lineno, raw_line in enumerate(fh, start=1):
            line = raw_line.strip()
            # Skip blank lines and comments
            if not line or line.startswith("#"):
                continue
            match = _LINE_RE.match(line)
            if not match:
                raise EnvParseError(
                    f"Invalid syntax on line {lineno}: {raw_line.rstrip()!r}"
                )
            key = match.group("key")
            value = _strip_quotes(match.group("value").strip())
            result[key] = value

    return result


def load_env_with_os_override(
    path: str = ".env", override: bool = False
) -> Dict[str, str]:
    """Load a .env file and optionally merge with actual OS environment variables.

    Args:
        path: Path to the .env file.
        override: If True, OS env vars take precedence over .env values.

    Returns:
        Merged dictionary of environment variables.
    """
    file_vars = load_env_file(path)
    if not override:
        return file_vars
    merged = dict(file_vars)
    merged.update({k: v for k, v in os.environ.items() if k in file_vars})
    return merged

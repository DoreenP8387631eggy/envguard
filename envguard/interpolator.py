"""Variable interpolation for .env files.

Supports ${VAR} and $VAR syntax, resolving references within the same
env dict or falling back to os.environ.
"""

import os
import re
from typing import Dict, Optional

_INTERPOLATION_RE = re.compile(r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)')


class InterpolationError(Exception):
    """Raised when a variable reference cannot be resolved."""


def interpolate_value(
    value: str,
    env: Dict[str, str],
    *,
    allow_os_fallback: bool = True,
    strict: bool = False,
) -> str:
    """Resolve variable references inside *value*.

    Args:
        value: Raw string that may contain ``${VAR}`` or ``$VAR`` tokens.
        env: The current env mapping (e.g. loaded from a .env file).
        allow_os_fallback: When True, missing keys are looked up in
            ``os.environ`` before raising or leaving unresolved.
        strict: When True, raise :class:`InterpolationError` for any
            reference that cannot be resolved.  When False, leave the
            original token intact.

    Returns:
        The string with all resolvable references expanded.
    """

    def _resolve(match: re.Match) -> str:  # type: ignore[type-arg]
        var_name = match.group(1) or match.group(2)
        if var_name in env:
            return env[var_name]
        if allow_os_fallback and var_name in os.environ:
            return os.environ[var_name]
        if strict:
            raise InterpolationError(
                f"Cannot resolve variable reference: '{var_name}'"
            )
        return match.group(0)  # leave token as-is

    return _INTERPOLATION_RE.sub(_resolve, value)


def interpolate_env(
    env: Dict[str, str],
    *,
    allow_os_fallback: bool = True,
    strict: bool = False,
) -> Dict[str, str]:
    """Apply :func:`interpolate_value` to every value in *env*.

    Returns a new dict; the original is not mutated.
    """
    return {
        key: interpolate_value(
            value,
            env,
            allow_os_fallback=allow_os_fallback,
            strict=strict,
        )
        for key, value in env.items()
    }

"""Tests for envguard.interpolator."""

import os
import pytest

from envguard.interpolator import (
    InterpolationError,
    interpolate_value,
    interpolate_env,
)


# ---------------------------------------------------------------------------
# interpolate_value
# ---------------------------------------------------------------------------

def test_no_references_returns_unchanged():
    assert interpolate_value("hello world", {}) == "hello world"


def test_braced_syntax_resolved_from_env():
    env = {"HOST": "localhost"}
    assert interpolate_value("${HOST}:5432", env) == "localhost:5432"


def test_bare_dollar_syntax_resolved_from_env():
    env = {"PORT": "5432"}
    assert interpolate_value("$PORT", env) == "5432"


def test_multiple_references_in_one_value():
    env = {"SCHEME": "https", "HOST": "example.com", "PORT": "443"}
    result = interpolate_value("${SCHEME}://${HOST}:${PORT}", env)
    assert result == "https://example.com:443"


def test_os_fallback_used_when_key_missing_from_env(monkeypatch):
    monkeypatch.setenv("OS_VAR", "from_os")
    assert interpolate_value("${OS_VAR}", {}, allow_os_fallback=True) == "from_os"


def test_os_fallback_disabled_leaves_token_intact(monkeypatch):
    monkeypatch.setenv("OS_VAR", "from_os")
    result = interpolate_value("${OS_VAR}", {}, allow_os_fallback=False)
    assert result == "${OS_VAR}"


def test_unresolved_token_left_intact_when_not_strict():
    result = interpolate_value("${MISSING}", {}, allow_os_fallback=False, strict=False)
    assert result == "${MISSING}"


def test_strict_mode_raises_on_missing_var():
    with pytest.raises(InterpolationError, match="MISSING"):
        interpolate_value("${MISSING}", {}, allow_os_fallback=False, strict=True)


def test_strict_mode_raises_even_with_partial_resolution():
    env = {"PRESENT": "ok"}
    with pytest.raises(InterpolationError):
        interpolate_value("${PRESENT}-${GONE}", env, allow_os_fallback=False, strict=True)


# ---------------------------------------------------------------------------
# interpolate_env
# ---------------------------------------------------------------------------

def test_interpolate_env_resolves_cross_references():
    env = {
        "BASE_URL": "http://localhost",
        "API_URL": "${BASE_URL}/api",
    }
    result = interpolate_env(env, allow_os_fallback=False)
    assert result["API_URL"] == "http://localhost/api"
    # original dict must not be mutated
    assert env["API_URL"] == "${BASE_URL}/api"


def test_interpolate_env_returns_new_dict():
    env = {"A": "1"}
    result = interpolate_env(env)
    assert result is not env


def test_interpolate_env_strict_raises():
    env = {"URL": "${UNDEFINED}/path"}
    with pytest.raises(InterpolationError):
        interpolate_env(env, allow_os_fallback=False, strict=True)

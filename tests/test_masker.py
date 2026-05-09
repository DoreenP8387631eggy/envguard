"""Tests for envguard.masker."""

import re

import pytest

from envguard.masker import is_sensitive, mask_value, mask_env


# ---------------------------------------------------------------------------
# is_sensitive
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", [
    "DB_PASSWORD",
    "API_KEY",
    "AUTH_TOKEN",
    "CLIENT_SECRET",
    "PRIVATE_KEY",
    "AWS_ACCESS_KEY",
    "SIGNING_KEY",
    "db_passwd",
    "user_credential",
])
def test_is_sensitive_true(name: str) -> None:
    assert is_sensitive(name) is True


@pytest.mark.parametrize("name", [
    "APP_ENV",
    "PORT",
    "DEBUG",
    "LOG_LEVEL",
    "DATABASE_HOST",
])
def test_is_sensitive_false(name: str) -> None:
    assert is_sensitive(name) is False


# ---------------------------------------------------------------------------
# mask_value
# ---------------------------------------------------------------------------

def test_mask_value_default() -> None:
    assert mask_value("supersecret") == "***"


def test_mask_value_empty_string() -> None:
    assert mask_value("") == "***"


def test_mask_value_custom_placeholder() -> None:
    assert mask_value("abc", placeholder="[REDACTED]") == "[REDACTED]"


def test_mask_value_partial_long_value() -> None:
    result = mask_value("abcdefgh", partial=True)
    assert result.startswith("abcd")
    assert "***" in result


def test_mask_value_partial_short_value() -> None:
    # Value shorter than _PARTIAL_VISIBLE — should be fully masked
    result = mask_value("ab", partial=True)
    assert result == "***"


# ---------------------------------------------------------------------------
# mask_env
# ---------------------------------------------------------------------------

def test_mask_env_auto_detection() -> None:
    env = {"DB_PASSWORD": "s3cr3t", "PORT": "5432", "API_KEY": "key123"}
    masked = mask_env(env)
    assert masked["DB_PASSWORD"] == "***"
    assert masked["API_KEY"] == "***"
    assert masked["PORT"] == "5432"


def test_mask_env_explicit_keys() -> None:
    env = {"MY_CUSTOM_VAR": "value", "PORT": "8080"}
    masked = mask_env(env, sensitive_keys=["MY_CUSTOM_VAR"])
    assert masked["MY_CUSTOM_VAR"] == "***"
    assert masked["PORT"] == "8080"


def test_mask_env_does_not_mutate_original() -> None:
    env = {"DB_PASSWORD": "original"}
    mask_env(env)
    assert env["DB_PASSWORD"] == "original"


def test_mask_env_extra_patterns() -> None:
    env = {"INTERNAL_PASSPHRASE": "hidden", "NORMAL_VAR": "visible"}
    extra = [re.compile(r"passphrase", re.IGNORECASE)]
    masked = mask_env(env, extra_patterns=extra)
    assert masked["INTERNAL_PASSPHRASE"] == "***"
    assert masked["NORMAL_VAR"] == "visible"


def test_mask_env_partial_mode() -> None:
    env = {"API_KEY": "abcdefgh"}
    masked = mask_env(env, partial=True)
    assert masked["API_KEY"].startswith("abcd")

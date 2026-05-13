"""Tests for envguard.normalizer."""

from __future__ import annotations

import pytest

from envguard.normalizer import (
    NormalizeChange,
    NormalizeReport,
    normalize_env,
    normalize_value,
)


# ---------------------------------------------------------------------------
# normalize_value
# ---------------------------------------------------------------------------

def test_no_change_for_clean_value():
    result, changes = normalize_value("KEY", "hello")
    assert result == "hello"
    assert changes == []


def test_strips_double_quotes():
    result, changes = normalize_value("KEY", '"hello"')
    assert result == "hello"
    assert len(changes) == 1
    assert "removed" in changes[0].reason


def test_strips_single_quotes():
    result, changes = normalize_value("KEY", "'world'")
    assert result == "world"
    assert len(changes) == 1


def test_strips_surrounding_whitespace():
    result, changes = normalize_value("KEY", "  value  ")
    assert result == "value"
    assert any("whitespace" in c.reason for c in changes)


def test_normalises_yes_to_true():
    result, changes = normalize_value("FEATURE_FLAG", "yes")
    assert result == "true"
    assert any("boolean" in c.reason for c in changes)


def test_normalises_no_to_false():
    result, changes = normalize_value("FEATURE_FLAG", "no")
    assert result == "false"


def test_normalises_1_to_true():
    result, changes = normalize_value("ENABLED", "1")
    assert result == "true"


def test_normalises_0_to_false():
    result, changes = normalize_value("ENABLED", "0")
    assert result == "false"


def test_already_canonical_true_no_change():
    result, changes = normalize_value("FLAG", "true")
    assert result == "true"
    assert changes == []


def test_already_canonical_false_no_change():
    result, changes = normalize_value("FLAG", "false")
    assert result == "false"
    assert changes == []


def test_quoted_whitespace_stripped_then_unquoted():
    # quotes removed first, then whitespace stripped
    result, changes = normalize_value("KEY", '"  spaced  "')
    assert result == "spaced"
    assert len(changes) >= 2


# ---------------------------------------------------------------------------
# normalize_env
# ---------------------------------------------------------------------------

def test_normalize_env_clean_mapping():
    env = {"HOST": "localhost", "PORT": "5432"}
    result, report = normalize_env(env)
    assert result == env
    assert not report.has_changes
    assert report.change_count == 0


def test_normalize_env_multiple_changes():
    env = {"FLAG": "YES", "NAME": '"alice"', "EXTRA": "  42  "}
    result, report = normalize_env(env)
    assert result["FLAG"] == "true"
    assert result["NAME"] == "alice"
    assert result["EXTRA"] == "42"
    assert report.has_changes


def test_normalize_report_summary_no_changes():
    _, report = normalize_env({"KEY": "value"})
    assert report.summary() == "No normalization changes."


def test_normalize_report_summary_with_changes():
    _, report = normalize_env({"FLAG": "ON"})
    summary = report.summary()
    assert "1 normalization change(s)" in summary
    assert "FLAG" in summary


def test_normalize_change_str():
    change = NormalizeChange(key="K", original="YES", normalized="true", reason="test")
    text = str(change)
    assert "K" in text
    assert "YES" in text
    assert "true" in text

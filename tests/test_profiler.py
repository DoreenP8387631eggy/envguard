"""Tests for envguard.profiler."""
import pytest

from envguard.profiler import (
    ProfileIssue,
    ProfileReport,
    _looks_like_placeholder,
    _shannon_entropy,
    profile_env,
)


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------

def test_shannon_entropy_empty_string():
    assert _shannon_entropy("") == 0.0


def test_shannon_entropy_uniform():
    # All same chars => entropy 0
    assert _shannon_entropy("aaaa") == 0.0


def test_shannon_entropy_high():
    # Random-looking base64 string should have high entropy
    val = "aB3$xZ9!qW2@mN7#"
    assert _shannon_entropy(val) > 3.0


def test_looks_like_placeholder_angle_brackets():
    assert _looks_like_placeholder("<your-secret>")


def test_looks_like_placeholder_square_brackets():
    assert _looks_like_placeholder("[REPLACE_ME]")


def test_looks_like_placeholder_change_me():
    assert _looks_like_placeholder("CHANGE_ME")


def test_looks_like_placeholder_normal_value():
    assert not _looks_like_placeholder("postgres://localhost/mydb")


# ---------------------------------------------------------------------------
# profile_env
# ---------------------------------------------------------------------------

def test_profile_clean_env_passes():
    env = {"HOST": "localhost", "PORT": "5432", "DEBUG": "false"}
    report = profile_env(env)
    assert report.passed
    assert report.stats["total_keys"] == 3
    assert report.stats["empty_values"] == 0
    assert report.stats["placeholder_values"] == 0


def test_profile_detects_empty_value():
    env = {"SECRET_KEY": ""}
    report = profile_env(env)
    assert any(i.key == "SECRET_KEY" and i.level == "warning" for i in report.issues)
    assert report.stats["empty_values"] == 1


def test_profile_detects_placeholder():
    env = {"API_KEY": "<your-api-key>"}
    report = profile_env(env)
    assert any(i.key == "API_KEY" and i.level == "warning" for i in report.issues)
    assert report.stats["placeholder_values"] == 1


def test_profile_detects_high_entropy():
    # A long random-looking string
    env = {"SECRET": "aB3$xZ9!qW2@mN7#pL4%vR6^"}
    report = profile_env(env, entropy_threshold=3.0)
    assert any(i.key == "SECRET" and i.level == "info" for i in report.issues)
    assert report.stats["high_entropy_values"] >= 1


def test_profile_report_passed_no_errors():
    report = ProfileReport(issues=[ProfileIssue("warning", "X", "msg")])
    assert report.passed  # warnings don't fail


def test_profile_report_failed_on_error():
    report = ProfileReport(issues=[ProfileIssue("error", "X", "msg")])
    assert not report.passed


def test_issue_str():
    issue = ProfileIssue("warning", "MY_VAR", "test message")
    assert "WARNING" in str(issue)
    assert "MY_VAR" in str(issue)
    assert "test message" in str(issue)

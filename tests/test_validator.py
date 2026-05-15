"""Tests for envguard.validator."""
from __future__ import annotations

import pytest

from envguard.validator import EnvValidator, ValidationRule, ValidationResult


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------

def test_result_passes_when_no_violations():
    r = ValidationResult()
    assert r.passed is True


def test_result_fails_when_violations_present():
    r = ValidationResult(violations=["oops"])
    assert r.passed is False


# ---------------------------------------------------------------------------
# ValidationRule
# ---------------------------------------------------------------------------

def test_rule_returns_none_on_success():
    rule = ValidationRule(name="ok", check=lambda env: None)
    assert rule.evaluate({}) is None


def test_rule_returns_message_on_failure():
    rule = ValidationRule(name="bad", check=lambda env: "something wrong")
    assert rule.evaluate({}) == "something wrong"


# ---------------------------------------------------------------------------
# EnvValidator
# ---------------------------------------------------------------------------

def _make_validator() -> EnvValidator:
    v = EnvValidator()
    v.add_rule(ValidationRule(
        name="db_together",
        description="DB_HOST and DB_PORT must both be set or both absent.",
        check=lambda env: (
            None
            if ("DB_HOST" in env) == ("DB_PORT" in env)
            else "DB_HOST and DB_PORT must both be present or both absent"
        ),
    ))
    return v


def test_validate_passes_when_both_present():
    v = _make_validator()
    result = v.validate({"DB_HOST": "localhost", "DB_PORT": "5432"})
    assert result.passed


def test_validate_passes_when_both_absent():
    v = _make_validator()
    result = v.validate({})
    assert result.passed


def test_validate_fails_when_only_host_present():
    v = _make_validator()
    result = v.validate({"DB_HOST": "localhost"})
    assert not result.passed
    assert len(result.violations) == 1
    assert "db_together" in result.violations[0]


def test_multiple_rules_all_fail():
    v = EnvValidator()
    v.add_rule(ValidationRule("r1", check=lambda e: "fail1"))
    v.add_rule(ValidationRule("r2", check=lambda e: "fail2"))
    result = v.validate({})
    assert len(result.violations) == 2


def test_decorator_registers_rule():
    v = EnvValidator()

    @v.rule("must_have_port", description="PORT must be set")
    def _(env):
        return None if "PORT" in env else "PORT is missing"

    assert len(v.rules) == 1
    assert v.rules[0].name == "must_have_port"


def test_decorator_rule_evaluated():
    v = EnvValidator()

    @v.rule("needs_secret")
    def _(env):
        return None if env.get("SECRET") else "SECRET must not be empty"

    result = v.validate({"SECRET": ""})
    assert not result.passed

    result2 = v.validate({"SECRET": "abc"})
    assert result2.passed

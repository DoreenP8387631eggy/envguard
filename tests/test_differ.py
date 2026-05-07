"""Tests for envguard.differ module."""

from __future__ import annotations

import os
import pytest

from envguard.differ import diff_env_files, diff_env_against_schema, DiffResult
from envguard.schema import EnvSchema, VarSchema, VarType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_env(tmp_path, filename: str, content: str) -> str:
    p = tmp_path / filename
    p.write_text(content)
    return str(p)


# ---------------------------------------------------------------------------
# DiffResult.summary
# ---------------------------------------------------------------------------

def test_diff_result_no_diff():
    r = DiffResult()
    assert not r.has_diff
    assert "No differences" in r.summary()


def test_diff_result_summary_formatting():
    r = DiffResult(
        only_in_left={"OLD_KEY"},
        only_in_right={"NEW_KEY"},
        value_changed={"CHANGED": ("a", "b")},
    )
    summary = r.summary()
    assert "- OLD_KEY" in summary
    assert "+ NEW_KEY" in summary
    assert "~ CHANGED" in summary


# ---------------------------------------------------------------------------
# diff_env_files
# ---------------------------------------------------------------------------

def test_diff_env_files_identical(tmp_path):
    content = "FOO=bar\nBAZ=qux\n"
    left = write_env(tmp_path, ".env.left", content)
    right = write_env(tmp_path, ".env.right", content)
    result = diff_env_files(left, right)
    assert not result.has_diff


def test_diff_env_files_added_key(tmp_path):
    left = write_env(tmp_path, ".env.left", "FOO=bar\n")
    right = write_env(tmp_path, ".env.right", "FOO=bar\nNEW_KEY=value\n")
    result = diff_env_files(left, right)
    assert "NEW_KEY" in result.only_in_right
    assert not result.only_in_left


def test_diff_env_files_removed_key(tmp_path):
    left = write_env(tmp_path, ".env.left", "FOO=bar\nOLD=gone\n")
    right = write_env(tmp_path, ".env.right", "FOO=bar\n")
    result = diff_env_files(left, right)
    assert "OLD" in result.only_in_left


def test_diff_env_files_value_changed_masked(tmp_path):
    left = write_env(tmp_path, ".env.left", "SECRET=hunter2\n")
    right = write_env(tmp_path, ".env.right", "SECRET=newpass\n")
    result = diff_env_files(left, right, mask_values=True)
    assert "SECRET" in result.value_changed
    lv, rv = result.value_changed["SECRET"]
    assert lv == "***"
    assert rv == "***"


def test_diff_env_files_value_changed_unmasked(tmp_path):
    left = write_env(tmp_path, ".env.left", "PORT=8080\n")
    right = write_env(tmp_path, ".env.right", "PORT=9090\n")
    result = diff_env_files(left, right, mask_values=False)
    assert result.value_changed["PORT"] == ("8080", "9090")


# ---------------------------------------------------------------------------
# diff_env_against_schema
# ---------------------------------------------------------------------------

def _make_schema(*keys: str) -> EnvSchema:
    schema = EnvSchema()
    for k in keys:
        schema.add(k, VarSchema(var_type=VarType.STRING, required=True))
    return schema


def test_diff_env_against_schema_no_diff(tmp_path):
    env = write_env(tmp_path, ".env", "FOO=bar\nBAZ=qux\n")
    schema = _make_schema("FOO", "BAZ")
    result = diff_env_against_schema(env, schema)
    assert not result.has_diff


def test_diff_env_against_schema_extra_in_env(tmp_path):
    env = write_env(tmp_path, ".env", "FOO=bar\nUNDOCUMENTED=oops\n")
    schema = _make_schema("FOO")
    result = diff_env_against_schema(env, schema)
    assert "UNDOCUMENTED" in result.only_in_left


def test_diff_env_against_schema_missing_from_env(tmp_path):
    env = write_env(tmp_path, ".env", "FOO=bar\n")
    schema = _make_schema("FOO", "REQUIRED_MISSING")
    result = diff_env_against_schema(env, schema)
    assert "REQUIRED_MISSING" in result.only_in_right

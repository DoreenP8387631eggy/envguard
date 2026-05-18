"""Tests for envguard.deprecator and envguard.cli_deprecate."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from envguard.deprecator import (
    DeprecationEntry,
    DeprecationReport,
    build_registry,
    scan_for_deprecated,
)
from envguard.cli_deprecate import build_deprecate_parser, run_deprecate


# ---------------------------------------------------------------------------
# Unit tests – deprecator module
# ---------------------------------------------------------------------------

def test_deprecation_entry_str_with_replacement():
    entry = DeprecationEntry(key="OLD_KEY", replacement="NEW_KEY")
    assert "OLD_KEY" in str(entry)
    assert "NEW_KEY" in str(entry)


def test_deprecation_entry_str_with_reason():
    entry = DeprecationEntry(key="OLD_KEY", reason="removed in v2")
    assert "removed in v2" in str(entry)


def test_deprecation_entry_str_minimal():
    entry = DeprecationEntry(key="OLD_KEY")
    assert "OLD_KEY is deprecated" in str(entry)


def test_build_registry_creates_entries():
    raw = [{"key": "OLD_DB_URL", "replacement": "DATABASE_URL", "reason": "renamed"}]
    registry = build_registry(raw)
    assert "OLD_DB_URL" in registry
    assert registry["OLD_DB_URL"].replacement == "DATABASE_URL"


def test_scan_no_hits():
    registry = build_registry([{"key": "OLD_KEY"}])
    report = scan_for_deprecated({"NEW_KEY": "value"}, registry)
    assert not report.has_hits
    assert report.hit_count == 0
    assert "No deprecated" in report.summary()


def test_scan_detects_deprecated_key():
    registry = build_registry([{"key": "OLD_KEY", "replacement": "NEW_KEY"}])
    report = scan_for_deprecated({"OLD_KEY": "value", "OTHER": "x"}, registry)
    assert report.has_hits
    assert report.hit_count == 1
    assert report.hits[0].key == "OLD_KEY"


def test_scan_multiple_deprecated_keys():
    registry = build_registry([{"key": "A"}, {"key": "B"}])
    report = scan_for_deprecated({"A": "1", "B": "2", "C": "3"}, registry)
    assert report.hit_count == 2


def test_report_summary_lists_all_hits():
    registry = build_registry([{"key": "OLD", "replacement": "NEW"}])
    report = scan_for_deprecated({"OLD": "v"}, registry)
    summary = report.summary()
    assert "OLD" in summary
    assert "NEW" in summary


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(textwrap.dedent(content))
        return p
    return _write


@pytest.fixture()
def registry_file(tmp_path: Path):
    def _write(entries) -> Path:
        p = tmp_path / "registry.json"
        p.write_text(json.dumps(entries))
        return p
    return _write


def _args(env_path, registry_path, strict=False):
    parser = build_deprecate_parser()
    argv = [str(env_path), "--registry", str(registry_path)]
    if strict:
        argv.append("--strict")
    return parser.parse_args(argv)


def test_clean_env_exits_zero(env_file, registry_file):
    ef = env_file("NEW_KEY=value\n")
    rf = registry_file([{"key": "OLD_KEY"}])
    assert run_deprecate(_args(ef, rf)) == 0


def test_deprecated_key_exits_zero_without_strict(env_file, registry_file):
    ef = env_file("OLD_KEY=value\n")
    rf = registry_file([{"key": "OLD_KEY"}])
    assert run_deprecate(_args(ef, rf)) == 0


def test_deprecated_key_exits_one_with_strict(env_file, registry_file):
    ef = env_file("OLD_KEY=value\n")
    rf = registry_file([{"key": "OLD_KEY"}])
    assert run_deprecate(_args(ef, rf, strict=True)) == 1


def test_missing_env_file_exits_two(tmp_path, registry_file):
    rf = registry_file([])
    args = _args(tmp_path / "nonexistent.env", rf)
    assert run_deprecate(args) == 2


def test_invalid_registry_exits_two(env_file, tmp_path):
    ef = env_file("KEY=val\n")
    bad_rf = tmp_path / "bad.json"
    bad_rf.write_text("{\"not\": \"a list\"}")
    args = _args(ef, bad_rf)
    assert run_deprecate(args) == 2

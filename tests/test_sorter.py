"""Tests for envguard.sorter and envguard.cli_sort."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envguard.sorter import SortReport, render_sorted_env, sort_env
from envguard.cli_sort import build_sort_parser, run_sort


# ---------------------------------------------------------------------------
# sorter unit tests
# ---------------------------------------------------------------------------


def test_sort_already_sorted_has_no_changes():
    env = {"ALPHA": "1", "BETA": "2", "GAMMA": "3"}
    report = sort_env(env)
    assert not report.has_changes
    assert report.change_count == 0
    assert "no changes" in report.summary()


def test_sort_unordered_detects_changes():
    env = {"ZEBRA": "z", "ALPHA": "a", "MANGO": "m"}
    report = sort_env(env)
    assert report.has_changes
    keys = [k for k, _ in report.sorted_order]
    assert keys == sorted(keys)


def test_sort_summary_mentions_reorder_count():
    env = {"Z": "1", "A": "2"}
    report = sort_env(env)
    assert report.has_changes
    summary = report.summary()
    assert "reordered" in summary


def test_sort_group_by_prefix_creates_groups():
    env = {
        "DB_HOST": "localhost",
        "APP_NAME": "envguard",
        "DB_PORT": "5432",
        "APP_ENV": "prod",
    }
    report = sort_env(env, group_by_prefix=True)
    assert "APP" in report.groups
    assert "DB" in report.groups
    app_keys = [k for k, _ in report.groups["APP"]]
    assert app_keys == sorted(app_keys)


def test_render_sorted_env_plain():
    env = {"Z": "26", "A": "1"}
    report = sort_env(env)
    rendered = render_sorted_env(report)
    lines = rendered.splitlines()
    assert lines[0].startswith("A=")
    assert lines[1].startswith("Z=")


def test_render_sorted_env_with_prefix_headers():
    env = {"DB_HOST": "h", "APP_NAME": "n"}
    report = sort_env(env, group_by_prefix=True)
    rendered = render_sorted_env(report, group_by_prefix=True)
    assert "# --- APP ---" in rendered
    assert "# --- DB ---" in rendered


# ---------------------------------------------------------------------------
# cli_sort integration tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def env_file(tmp_path: Path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content, encoding="utf-8")
        return p

    return _write


def _args(env_path: str, **kwargs) -> argparse.Namespace:
    defaults = {"env_file": env_path, "group_by_prefix": False, "in_place": False, "check": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cli_sort_already_sorted_check_exits_zero(env_file):
    p = env_file("ALPHA=1\nBETA=2\n")
    assert run_sort(_args(str(p), check=True)) == 0


def test_cli_sort_unsorted_check_exits_one(env_file):
    p = env_file("ZEBRA=z\nALPHA=a\n")
    assert run_sort(_args(str(p), check=True)) == 1


def test_cli_sort_in_place_writes_file(env_file):
    p = env_file("Z=26\nA=1\n")
    assert run_sort(_args(str(p), in_place=True)) == 0
    content = p.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if l]
    assert lines[0].startswith("A=")


def test_cli_sort_missing_file_exits_two(tmp_path: Path):
    missing = str(tmp_path / "nope.env")
    assert run_sort(_args(missing)) == 2


def test_cli_sort_stdout_output(env_file, capsys):
    p = env_file("Z=26\nA=1\n")
    rc = run_sort(_args(str(p)))
    assert rc == 0
    captured = capsys.readouterr().out
    lines = [l for l in captured.splitlines() if l]
    assert lines[0].startswith("A=")

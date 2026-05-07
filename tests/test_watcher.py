"""Tests for envguard.watcher module."""

import time
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from envguard.watcher import EnvFileWatcher
from envguard.schema import EnvSchema, VarSchema, VarType
from envguard.auditor import AuditReport


@pytest.fixture
def simple_schema() -> EnvSchema:
    s = EnvSchema()
    s.add(VarSchema(name="APP_NAME", var_type=VarType.STRING, required=True))
    return s


@pytest.fixture
def env_file(tmp_path) -> Path:
    p = tmp_path / ".env"
    p.write_text("APP_NAME=envguard\n")
    return p


def test_watcher_detects_initial_file(env_file, simple_schema):
    reports = []
    watcher = EnvFileWatcher(
        str(env_file), simple_schema,
        on_change=lambda r: reports.append(r),
        poll_interval=0.0,
    )
    watcher.start(max_iterations=1)
    assert len(reports) == 1
    assert reports[0].passed


def test_watcher_triggers_on_modification(env_file, simple_schema):
    reports = []
    watcher = EnvFileWatcher(
        str(env_file), simple_schema,
        on_change=lambda r: reports.append(r),
        poll_interval=0.0,
    )
    watcher._last_mtime = None
    watcher._check_and_audit()
    original_mtime = watcher._last_mtime

    time.sleep(0.05)
    env_file.write_text("APP_NAME=updated\n")
    watcher._check_and_audit()

    assert len(reports) == 2


def test_watcher_no_trigger_when_unchanged(env_file, simple_schema):
    reports = []
    watcher = EnvFileWatcher(
        str(env_file), simple_schema,
        on_change=lambda r: reports.append(r),
        poll_interval=0.0,
    )
    watcher._check_and_audit()
    count_after_first = len(reports)
    watcher._check_and_audit()
    assert len(reports) == count_after_first  # no new trigger


def test_watcher_stop_sets_flag(env_file, simple_schema):
    watcher = EnvFileWatcher(str(env_file), simple_schema, poll_interval=0.0)
    watcher._running = True
    watcher.stop()
    assert not watcher._running


def test_default_handler_prints(env_file, simple_schema, capsys):
    watcher = EnvFileWatcher(str(env_file), simple_schema, poll_interval=0.0)
    watcher.start(max_iterations=1)
    captured = capsys.readouterr()
    assert "envguard" in captured.out

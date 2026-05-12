"""Tests for envguard.cli_merge."""

from __future__ import annotations

import argparse

import pytest

from envguard.cli_merge import build_merge_parser, run_merge


def write_env(tmp_path, name: str, content: str) -> str:
    p = tmp_path / name
    p.write_text(content)
    return str(p)


def _args(tmp_path, files, **kwargs):
    defaults = dict(
        files=files,
        strategy="last_wins",
        output=None,
        ignore_missing=False,
        show_conflicts=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_no_conflicts_exits_zero(tmp_path):
    f1 = write_env(tmp_path, "a.env", "FOO=1\n")
    f2 = write_env(tmp_path, "b.env", "BAR=2\n")
    code = run_merge(_args(tmp_path, [f1, f2]))
    assert code == 0


def test_conflicts_exits_one(tmp_path):
    f1 = write_env(tmp_path, "a.env", "FOO=1\n")
    f2 = write_env(tmp_path, "b.env", "FOO=2\n")
    code = run_merge(_args(tmp_path, [f1, f2]))
    assert code == 1


def test_missing_file_exits_two(tmp_path):
    code = run_merge(_args(tmp_path, [str(tmp_path / "ghost.env")]))
    assert code == 2


def test_ignore_missing_exits_zero(tmp_path):
    f = write_env(tmp_path, "real.env", "X=1\n")
    code = run_merge(_args(tmp_path, [str(tmp_path / "ghost.env"), f], ignore_missing=True))
    assert code == 0


def test_output_written_to_file(tmp_path, capsys):
    f1 = write_env(tmp_path, "a.env", "FOO=1\n")
    out_file = str(tmp_path / "merged.env")
    run_merge(_args(tmp_path, [f1], output=out_file))
    content = open(out_file).read()
    assert "FOO=1" in content


def test_merged_keys_in_stdout(tmp_path, capsys):
    f1 = write_env(tmp_path, "a.env", "ALPHA=x\n")
    f2 = write_env(tmp_path, "b.env", "BETA=y\n")
    run_merge(_args(tmp_path, [f1, f2]))
    captured = capsys.readouterr()
    assert "ALPHA=x" in captured.out
    assert "BETA=y" in captured.out


def test_show_conflicts_prints_to_stderr(tmp_path, capsys):
    f1 = write_env(tmp_path, "a.env", "KEY=old\n")
    f2 = write_env(tmp_path, "b.env", "KEY=new\n")
    run_merge(_args(tmp_path, [f1, f2], show_conflicts=True))
    captured = capsys.readouterr()
    assert "CONFLICT KEY" in captured.err


def test_parser_defaults():
    parser = build_merge_parser()
    args = parser.parse_args(["a.env", "b.env"])
    assert args.strategy == "last_wins"
    assert args.ignore_missing is False
    assert args.output is None

"""CLI entry-point for the envguard health scorer."""
from __future__ import annotations

import argparse
import sys

from envguard.auditor import audit
from envguard.cli import load_schema_from_file
from envguard.linter import lint_env_file
from envguard.loader import load_env_file
from envguard.profiler import profile_env
from envguard.scorer import compute_score


def build_score_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(description="Compute an overall health score for a .env file.")
    if parent is not None:
        parser = parent.add_parser("score", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envguard-score", **kwargs)
    parser.add_argument("env_file", help="Path to the .env file")
    parser.add_argument("--schema", metavar="FILE", help="Optional schema file (.py)")
    parser.add_argument("--min-score", type=int, default=70, metavar="N",
                        help="Exit non-zero when score is below N (default: 70)")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="Emit result as JSON")
    return parser


def run_score(args: argparse.Namespace) -> int:
    """Execute the score command; returns an exit code."""
    # Lint
    lint_result = lint_env_file(args.env_file)

    # Load env
    try:
        env = load_env_file(args.env_file)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 2

    # Audit (optional, requires schema)
    audit_report = None
    if args.schema:
        schema = load_schema_from_file(args.schema)
        audit_report = audit(env, schema)

    # Profile
    profile_report = profile_env(env)

    health = compute_score(audit=audit_report, lint=lint_result, profile=profile_report)

    if args.as_json:
        import json
        payload = {
            "score": health.score,
            "grade": health.grade,
            "passed": health.passed,
            "penalties": {
                "audit": health.breakdown.audit_penalty,
                "lint": health.breakdown.lint_penalty,
                "profile": health.breakdown.profile_penalty,
            },
            "notes": health.breakdown.notes,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(health)

    return 0 if health.score >= args.min_score else 1


def main() -> None:  # pragma: no cover
    parser = build_score_parser()
    args = parser.parse_args()
    sys.exit(run_score(args))


if __name__ == "__main__":  # pragma: no cover
    main()

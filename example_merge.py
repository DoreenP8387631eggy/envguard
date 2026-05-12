"""Example: merge two .env files and inspect the result."""

from __future__ import annotations

import tempfile
import os

from envguard.merger import MergeStrategy, merge_env_files

# ---------------------------------------------------------------------------
# Create two temporary .env files
# ---------------------------------------------------------------------------
tmp = tempfile.mkdtemp()

base_env = os.path.join(tmp, "base.env")
override_env = os.path.join(tmp, "override.env")

with open(base_env, "w") as f:
    f.write("DATABASE_URL=postgres://localhost/dev\n")
    f.write("DEBUG=false\n")
    f.write("LOG_LEVEL=info\n")

with open(override_env, "w") as f:
    f.write("DEBUG=true\n")          # conflict — override wins
    f.write("SECRET_KEY=s3cr3t\n")   # new key only in override

# ---------------------------------------------------------------------------
# Merge with LAST_WINS strategy (default)
# ---------------------------------------------------------------------------
report = merge_env_files(
    paths=[base_env, override_env],
    strategy=MergeStrategy.LAST_WINS,
)

print("=== Merged Variables ===")
for key, value in sorted(report.merged.items()):
    print(f"  {key}={value}")

print(f"\n{report.summary}")

if report.has_conflicts:
    print("\n=== Conflicts ===")
    for conflict in report.conflicts:
        print(f"  {conflict}")

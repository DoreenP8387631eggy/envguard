"""Example: compute an env health score programmatically.

Run::

    python example_score.py
"""
from envguard.auditor import audit
from envguard.linter import lint_env_file
from envguard.loader import load_env_file
from envguard.profiler import profile_env
from envguard.schema import EnvSchema, VarSchema, VarType
from envguard.scorer import compute_score

# ── Build a schema ──────────────────────────────────────────────────────────
schema = EnvSchema()
schema.add(VarSchema(name="DATABASE_URL", required=True))
schema.add(VarSchema(name="SECRET_KEY", required=True))
schema.add(VarSchema(name="DEBUG", required=False, var_type=VarType.BOOL, default="false"))
schema.add(VarSchema(name="PORT", required=False, var_type=VarType.INT, default="8080"))

# ── Simulate an env dict (normally loaded from a file) ──────────────────────
env = {
    "DATABASE_URL": "postgres://localhost/mydb",
    "SECRET_KEY": "s3cr3t!",
    "DEBUG": "false",
    "PORT": "8080",
}

# ── Run individual checks ───────────────────────────────────────────────────
audit_report = audit(env, schema)
profile_report = profile_env(env)

# ── Compute combined score ──────────────────────────────────────────────────
health = compute_score(audit=audit_report, profile=profile_report)

print(health)
print()
print(f"Passed threshold (>=70): {health.passed}")

"""Example: cross-field validation rules for envguard.

Run with:
    python -m envguard.cli_validate .env --rules example_validate.py

This file also serves as the ``rules`` module itself — it exposes a
top-level ``validator`` instance that ``cli_validate`` will import.
"""
from __future__ import annotations

from envguard.validator import EnvValidator, ValidationRule

validator = EnvValidator()

# Rule 1 – DB_HOST and DB_PORT must both be present or both absent.
validator.add_rule(ValidationRule(
    name="db_host_port_together",
    description="DB_HOST and DB_PORT must both be set or both absent.",
    check=lambda env: (
        None
        if ("DB_HOST" in env) == ("DB_PORT" in env)
        else "DB_HOST and DB_PORT must both be present or both absent"
    ),
))

# Rule 2 – When APP_ENV=production, DEBUG must not be 'true'.
@validator.rule(
    "no_debug_in_production",
    description="DEBUG must not be 'true' when APP_ENV is 'production'.",
)
def _(env):  # type: ignore[return]
    if env.get("APP_ENV") == "production" and env.get("DEBUG", "").lower() == "true":
        return "DEBUG=true is not allowed in production"
    return None

# Rule 3 – SECRET_KEY must be at least 32 characters long.
validator.add_rule(ValidationRule(
    name="secret_key_length",
    description="SECRET_KEY must be at least 32 characters.",
    check=lambda env: (
        None
        if len(env.get("SECRET_KEY", "")) >= 32
        else "SECRET_KEY must be at least 32 characters long"
    ),
))

if __name__ == "__main__":  # pragma: no cover
    import sys
    from envguard.loader import load_env_file

    env_path = sys.argv[1] if len(sys.argv) > 1 else ".env"
    env = load_env_file(env_path)
    result = validator.validate(env)
    print(result)
    sys.exit(0 if result.passed else 1)

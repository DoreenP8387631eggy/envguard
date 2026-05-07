# envguard

A lightweight utility that validates and audits `.env` files against a schema to catch missing or misconfigured environment variables before deployment.

---

## Installation

```bash
pip install envguard
```

Or with Poetry:

```bash
poetry add envguard
```

---

## Usage

Define a schema file (`.env.schema`) listing required variables and optional rules:

```ini
DATABASE_URL=required
SECRET_KEY=required, min_length=32
DEBUG=optional, allowed=true,false
PORT=optional, type=int
```

Then validate your `.env` file against it:

```python
from envguard import EnvGuard

guard = EnvGuard(schema=".env.schema", env_file=".env")
report = guard.validate()

if not report.is_valid:
    print(report.errors)
else:
    print("All environment variables are valid.")
```

Or use the CLI directly:

```bash
envguard validate --schema .env.schema --env .env
```

To list all variables defined in your schema along with their rules:

```bash
envguard audit --schema .env.schema
```

---

## Why envguard?

- ✅ Catch missing variables before they cause runtime failures
- 🔍 Audit `.env` files for type mismatches and invalid values
- ⚡ Lightweight with zero required dependencies
- 🔧 Works seamlessly in CI/CD pipelines

---

## License

This project is licensed under the [MIT License](LICENSE).

"""Example schema file for use with the envguard CLI.

Run with:
    envguard .env example_schema.py
    envguard .env example_schema.py --format json
    envguard .env example_schema.py --format github
    envguard .env example_schema.py --strict
"""

from envguard.schema import EnvSchema, VarSchema, VarType

schema = EnvSchema()

# Required variables
schema.add(VarSchema("APP_HOST", var_type=VarType.STRING, required=True))
schema.add(VarSchema("APP_PORT", var_type=VarType.INTEGER, required=True))
schema.add(VarSchema("DATABASE_URL", var_type=VarType.STRING, required=True))
schema.add(VarSchema("SECRET_KEY", var_type=VarType.STRING, required=True))

# Optional variables
schema.add(VarSchema("DEBUG", var_type=VarType.BOOLEAN, required=False, default="false"))
schema.add(VarSchema("LOG_LEVEL", var_type=VarType.STRING, required=False, default="INFO"))
schema.add(VarSchema("ALLOWED_HOSTS", var_type=VarType.STRING, required=False))
schema.add(VarSchema("MAX_CONNECTIONS", var_type=VarType.INTEGER, required=False, default="10"))

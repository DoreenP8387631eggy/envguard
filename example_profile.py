"""Runnable example demonstrating the envguard profiler API."""
from envguard.profiler import profile_env

# Simulate a parsed .env dictionary
sample_env = {
    "DATABASE_URL": "postgres://user:password@localhost/mydb",
    "SECRET_KEY": "aB3$xZ9!qW2@mN7#pL4%vR6^",  # high entropy
    "API_KEY": "<your-api-key>",               # placeholder
    "DEBUG": "true",
    "EMPTY_VAR": "",                            # empty value
    "PORT": "8080",
}

report = profile_env(sample_env, entropy_threshold=3.5)

print("=== EnvGuard Profile Report ===")
print(f"Status : {'PASSED' if report.passed else 'FAILED'}")
print(f"Stats  : {report.stats}")
print()

if report.issues:
    print("Issues found:")
    for issue in report.issues:
        print(f"  {issue}")
else:
    print("No issues found.")

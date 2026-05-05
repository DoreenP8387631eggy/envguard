"""Audits a loaded env dictionary against an EnvSchema and produces a report."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envguard.loader import load_env_file
from envguard.schema import EnvSchema, validate_value


@dataclass
class AuditIssue:
    """Represents a single problem found during an audit."""

    key: str
    severity: str  # "error" | "warning"
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class AuditReport:
    """Aggregated result of auditing an env dict against a schema."""

    issues: List[AuditIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[AuditIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[AuditIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        status = "PASSED" if self.passed else "FAILED"
        return (
            f"Audit {status} — "
            f"{len(self.errors)} error(s), {len(self.warnings)} warning(s)."
        )


def audit(env_vars: Dict[str, str], schema: EnvSchema) -> AuditReport:
    """Validate *env_vars* against *schema* and return an AuditReport.

    Args:
        env_vars: Dictionary of variable names to string values.
        schema: EnvSchema instance describing expected variables.

    Returns:
        An AuditReport containing all discovered issues.
    """
    report = AuditReport()

    for key, var_schema in schema.vars.items():
        if key not in env_vars:
            if var_schema.required:
                report.issues.append(
                    AuditIssue(key, "error", "Required variable is missing.")
                )
            elif var_schema.default is None:
                report.issues.append(
                    AuditIssue(key, "warning", "Optional variable not set and has no default.")
                )
            continue

        raw_value = env_vars[key]
        ok, error_msg = validate_value(raw_value, var_schema)
        if not ok:
            report.issues.append(AuditIssue(key, "error", error_msg or "Validation failed."))

    return report


def audit_file(path: str, schema: EnvSchema) -> AuditReport:
    """Convenience wrapper: load a .env file then audit it.

    Args:
        path: Path to the .env file.
        schema: EnvSchema instance to validate against.

    Returns:
        An AuditReport for the loaded file.
    """
    env_vars = load_env_file(path)
    return audit(env_vars, schema)

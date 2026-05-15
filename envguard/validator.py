"""Cross-field and conditional validation rules for .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class ValidationRule:
    """A single conditional/cross-field rule."""

    name: str
    check: Callable[[Dict[str, str]], Optional[str]]
    description: str = ""

    def evaluate(self, env: Dict[str, str]) -> Optional[str]:
        """Return an error message string if the rule fails, else None."""
        return self.check(env)


@dataclass
class ValidationResult:
    """Aggregated result of running all rules against an env dict."""

    violations: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0

    def __str__(self) -> str:  # pragma: no cover
        if self.passed:
            return "Validation passed."
        lines = ["Validation failed:"]
        for v in self.violations:
            lines.append(f"  - {v}")
        return "\n".join(lines)


class EnvValidator:
    """Runs a collection of ValidationRule objects against an env dict."""

    def __init__(self) -> None:
        self._rules: List[ValidationRule] = []

    def add_rule(self, rule: ValidationRule) -> "EnvValidator":
        self._rules.append(rule)
        return self

    def rule(
        self,
        name: str,
        description: str = "",
    ) -> Callable[[Callable[[Dict[str, str]], Optional[str]]], ValidationRule]:
        """Decorator that registers a function as a ValidationRule."""

        def decorator(fn: Callable[[Dict[str, str]], Optional[str]]) -> ValidationRule:
            r = ValidationRule(name=name, check=fn, description=description)
            self._rules.append(r)
            return r

        return decorator

    def validate(self, env: Dict[str, str]) -> ValidationResult:
        result = ValidationResult()
        for rule in self._rules:
            msg = rule.evaluate(env)
            if msg is not None:
                result.violations.append(f"[{rule.name}] {msg}")
        return result

    @property
    def rules(self) -> List[ValidationRule]:
        return list(self._rules)

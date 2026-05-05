"""Schema definition and parsing for envguard.

This module provides the core data structures and logic for defining
what environment variables are expected, their types, and validation rules.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import re


class VarType(str, Enum):
    """Supported types for environment variable values."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    URL = "url"
    EMAIL = "email"


@dataclass
class VarSchema:
    """Describes the expected shape and constraints of a single env variable."""

    name: str
    required: bool = True
    type: VarType = VarType.STRING
    default: Optional[str] = None
    description: str = ""
    pattern: Optional[str] = None  # regex pattern the value must match
    allowed_values: list[str] = field(default_factory=list)

    def validate_value(self, value: str) -> tuple[bool, Optional[str]]:
        """Validate a string value against this schema.

        Returns:
            A tuple of (is_valid, error_message). error_message is None on success.
        """
        if not value and self.required:
            return False, f"'{self.name}' is required but has an empty value."

        if self.type == VarType.INTEGER:
            try:
                int(value)
            except ValueError:
                return False, f"'{self.name}' must be an integer, got: '{value}'"

        elif self.type == VarType.FLOAT:
            try:
                float(value)
            except ValueError:
                return False, f"'{self.name}' must be a float, got: '{value}'"

        elif self.type == VarType.BOOLEAN:
            if value.lower() not in ("true", "false", "1", "0", "yes", "no"):
                return False, (
                    f"'{self.name}' must be a boolean (true/false/1/0/yes/no), "
                    f"got: '{value}'"
                )

        elif self.type == VarType.URL:
            url_re = re.compile(
                r"^(https?|ftp)://[^\s/$.?#].[^\s]*$", re.IGNORECASE
            )
            if not url_re.match(value):
                return False, f"'{self.name}' must be a valid URL, got: '{value}'"

        elif self.type == VarType.EMAIL:
            email_re = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
            if not email_re.match(value):
                return False, f"'{self.name}' must be a valid email, got: '{value}'"

        if self.pattern and not re.fullmatch(self.pattern, value):
            return False, (
                f"'{self.name}' does not match required pattern '{self.pattern}', "
                f"got: '{value}'"
            )

        if self.allowed_values and value not in self.allowed_values:
            return False, (
                f"'{self.name}' must be one of {self.allowed_values}, got: '{value}'"
            )

        return True, None


@dataclass
class EnvSchema:
    """A collection of variable schemas representing a full .env specification."""

    variables: dict[str, VarSchema] = field(default_factory=dict)

    def add(self, var: VarSchema) -> None:
        """Register a variable schema."""
        self.variables[var.name] = var

    def get(self, name: str) -> Optional[VarSchema]:
        """Retrieve a variable schema by name."""
        return self.variables.get(name)

    def required_names(self) -> list[str]:
        """Return names of all required variables."""
        return [name for name, v in self.variables.items() if v.required]

    def __len__(self) -> int:
        return len(self.variables)

"""Export EnvSchema definitions to various formats (dotenv template, JSON Schema, Markdown docs)."""

from __future__ import annotations

import json
from enum import Enum
from typing import IO

from envguard.schema import EnvSchema, VarType


class ExportFormat(str, Enum):
    DOTENV = "dotenv"
    JSON_SCHEMA = "json_schema"
    MARKDOWN = "markdown"


def export_dotenv_template(schema: EnvSchema, stream: IO[str]) -> None:
    """Write a commented .env template based on the schema."""
    stream.write("# Auto-generated .env template by envguard\n")
    for name, var in schema._vars.items():
        if var.description:
            stream.write(f"# {var.description}\n")
        required_tag = "required" if var.required else "optional"
        stream.write(f"# type={var.var_type.value}, {required_tag}\n")
        if var.default is not None:
            stream.write(f"{name}={var.default}\n")
        else:
            stream.write(f"{name}=\n")
        stream.write("\n")


def export_json_schema(schema: EnvSchema, stream: IO[str]) -> None:
    """Write a JSON Schema document describing the environment variables."""
    _TYPE_MAP = {
        VarType.STRING: {"type": "string"},
        VarType.INTEGER: {"type": "integer"},
        VarType.FLOAT: {"type": "number"},
        VarType.BOOLEAN: {"type": "boolean"},
        VarType.URL: {"type": "string", "format": "uri"},
    }
    properties: dict = {}
    required_fields: list[str] = []

    for name, var in schema._vars.items():
        prop = dict(_TYPE_MAP.get(var.var_type, {"type": "string"}))
        if var.description:
            prop["description"] = var.description
        if var.default is not None:
            prop["default"] = var.default
        if var.allowed_values:
            prop["enum"] = list(var.allowed_values)
        properties[name] = prop
        if var.required:
            required_fields.append(name)

    doc = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": properties,
        "required": required_fields,
    }
    json.dump(doc, stream, indent=2)


def export_markdown(schema: EnvSchema, stream: IO[str]) -> None:
    """Write a Markdown reference table for the environment variables."""
    stream.write("# Environment Variables Reference\n\n")
    stream.write("| Variable | Type | Required | Default | Description |\n")
    stream.write("|----------|------|----------|---------|-------------|\n")
    for name, var in schema._vars.items():
        req = "✅" if var.required else "—"
        default = str(var.default) if var.default is not None else "—"
        desc = var.description or "—"
        stream.write(
            f"| `{name}` | {var.var_type.value} | {req} | `{default}` | {desc} |\n"
        )


def export_schema(schema: EnvSchema, fmt: ExportFormat, stream: IO[str]) -> None:
    """Dispatch to the correct exporter based on *fmt*."""
    dispatch = {
        ExportFormat.DOTENV: export_dotenv_template,
        ExportFormat.JSON_SCHEMA: export_json_schema,
        ExportFormat.MARKDOWN: export_markdown,
    }
    dispatch[fmt](schema, stream)

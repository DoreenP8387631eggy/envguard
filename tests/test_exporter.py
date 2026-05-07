"""Tests for envguard.exporter."""

from __future__ import annotations

import io
import json

import pytest

from envguard.exporter import ExportFormat, export_schema
from envguard.schema import EnvSchema, VarType


@pytest.fixture()
def sample_schema() -> EnvSchema:
    s = EnvSchema()
    s.add("DATABASE_URL", var_type=VarType.URL, required=True, description="Primary DB connection string")
    s.add("PORT", var_type=VarType.INTEGER, required=False, default="8080", description="HTTP port")
    s.add("DEBUG", var_type=VarType.BOOLEAN, required=False, default="false")
    s.add("ENV", var_type=VarType.STRING, required=True, allowed_values=["dev", "staging", "prod"])
    return s


def _capture(schema: EnvSchema, fmt: ExportFormat) -> str:
    buf = io.StringIO()
    export_schema(schema, fmt, buf)
    return buf.getvalue()


# --- dotenv template ---

def test_dotenv_template_contains_all_vars(sample_schema):
    out = _capture(sample_schema, ExportFormat.DOTENV)
    for name in ("DATABASE_URL", "PORT", "DEBUG", "ENV"):
        assert name in out


def test_dotenv_template_marks_required(sample_schema):
    out = _capture(sample_schema, ExportFormat.DOTENV)
    assert "required" in out
    assert "optional" in out


def test_dotenv_template_shows_default(sample_schema):
    out = _capture(sample_schema, ExportFormat.DOTENV)
    assert "PORT=8080" in out


def test_dotenv_template_empty_value_for_no_default(sample_schema):
    out = _capture(sample_schema, ExportFormat.DOTENV)
    assert "DATABASE_URL=\n" in out


# --- JSON Schema ---

def test_json_schema_is_valid_json(sample_schema):
    out = _capture(sample_schema, ExportFormat.JSON_SCHEMA)
    doc = json.loads(out)
    assert doc["type"] == "object"


def test_json_schema_required_list(sample_schema):
    doc = json.loads(_capture(sample_schema, ExportFormat.JSON_SCHEMA))
    assert "DATABASE_URL" in doc["required"]
    assert "ENV" in doc["required"]
    assert "PORT" not in doc["required"]


def test_json_schema_enum_for_allowed_values(sample_schema):
    doc = json.loads(_capture(sample_schema, ExportFormat.JSON_SCHEMA))
    assert doc["properties"]["ENV"]["enum"] == ["dev", "staging", "prod"]


def test_json_schema_url_format(sample_schema):
    doc = json.loads(_capture(sample_schema, ExportFormat.JSON_SCHEMA))
    assert doc["properties"]["DATABASE_URL"]["format"] == "uri"


# --- Markdown ---

def test_markdown_contains_header(sample_schema):
    out = _capture(sample_schema, ExportFormat.MARKDOWN)
    assert "# Environment Variables Reference" in out


def test_markdown_table_rows(sample_schema):
    out = _capture(sample_schema, ExportFormat.MARKDOWN)
    assert "`DATABASE_URL`" in out
    assert "`PORT`" in out


def test_markdown_required_checkmark(sample_schema):
    out = _capture(sample_schema, ExportFormat.MARKDOWN)
    assert "✅" in out

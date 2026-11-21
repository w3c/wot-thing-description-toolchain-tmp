"""A standalone module context declares exactly the prefixes its own CURIEs reference."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.postprocessors.jsonld_context_postprocessor import build_module_context

SENSOR_SCHEMA = Path(__file__).resolve().parent / "fixtures" / "mini-project" / "schemas" / "sensor.yaml"


@pytest.fixture(scope="module")
def sensor_context() -> dict[str, Any]:
    schema_view = SchemaView(str(SENSOR_SCHEMA), merge_imports=True)
    generator = ContextGenerator(schema_view.schema, mergeimports=True, fix_multivalue_containers=True)
    return build_module_context(schema_view, generator, "sen")


def test_module_context_declares_referenced_prefix(sensor_context: dict[str, Any]) -> None:
    assert sensor_context["Sensor"] == {"@id": "sen:Sensor"}
    assert sensor_context["sen"] == "https://example.org/sensor#"


def test_module_context_omits_unreferenced_prefix(sensor_context: dict[str, Any]) -> None:
    assert "linkml" not in sensor_context

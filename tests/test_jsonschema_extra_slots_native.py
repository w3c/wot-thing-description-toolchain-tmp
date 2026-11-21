"""Upstream gen-jsonschema already maps ``extra_slots`` to ``additionalProperties`` for the TD schema."""

import json
from pathlib import Path

import pytest
from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.config import load_project
from wot_toolchain.schema_utils import load_schema_view

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def td_schema_view() -> SchemaView:
    """The TD schema view, loaded as the pipeline loads it."""
    project = load_project(REPO_ROOT / "wot-toolchain.yaml")
    return load_schema_view(project.main_schema, merge_imports=True)


@pytest.fixture(scope="module")
def raw_td_jsonschema(td_schema_view: SchemaView) -> dict:
    """Raw upstream JSON Schema, generated with the pipeline's generator arguments."""
    project = load_project(REPO_ROOT / "wot-toolchain.yaml")
    gen = JsonSchemaGenerator(
        td_schema_view.schema,
        mergeimports=True,
        top_class=project.top_class,
        not_closed=True,
        include_null=False,
        preserve_names=True,
    )
    return json.loads(gen.serialize())


def test_extra_slots_allowed_emitted_natively(td_schema_view: SchemaView, raw_td_jsonschema: dict) -> None:
    """Every class with ``extra_slots.allowed`` carries ``additionalProperties: true`` in raw output."""
    defs = raw_td_jsonschema["$defs"]
    # Upstream get_additional_properties implements extra_slots (linkml 1.12.0 jsonschemagen.py:1043-1059).
    classes = [
        name
        for name, cls in td_schema_view.all_classes().items()
        if cls.extra_slots and cls.extra_slots.allowed and isinstance(defs.get(name), dict)
    ]
    assert classes, "TD schema has no emitted class with extra_slots.allowed; the check would be vacuous"
    missing = [name for name in classes if defs[name].get("additionalProperties") is not True]
    assert not missing, f"Raw upstream output lacks additionalProperties: true for {missing}"

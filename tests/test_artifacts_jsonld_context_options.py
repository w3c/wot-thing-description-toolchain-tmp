import dataclasses
import json
import warnings
from pathlib import Path
from typing import Any

import pytest
from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.artifacts.jsonld_context.generator import WotContextGenerator
from wot_toolchain.artifacts.jsonld_context.options import JsonLdContextOptions
from wot_toolchain.config import load_project
from wot_toolchain.schema_utils import load_schema_view

REPO_ROOT = Path(__file__).resolve().parent.parent

CONSTRUCTOR_STATE = ("mergeimports", "fix_multivalue_containers")

# Captured from postprocessors.jsonld_context_postprocessor._native_slot_context before it moved;
# key order is part of the expectation because it reaches the generated files.
TODAYS_SLOT_TERMS: dict[str, Any] = {
    "name": "@id",
    "forms": {"@type": "@id", "@container": "@set", "@id": "hasForm"},
    "actions": {"@type": "@id", "@container": "@index", "@id": "hasActionAffordance"},
    "security": {"@id": "hasSecurityConfiguration"},
    "op": {
        "@context": {"text": "skos:notation", "description": "skos:prefLabel", "meaning": "@id"},
        "@id": "hctl:hasOperationType",
    },
    "created": {"@type": "xsd:dateTime", "@id": "dcterms:created"},
    "href": {"@type": "xsd:anyURI", "@id": "hctl:hasTarget"},
}


@pytest.fixture(scope="module")
def td_schema_view() -> SchemaView:
    project = load_project(REPO_ROOT / "wot-toolchain.yaml")
    return load_schema_view(project.main_schema, merge_imports=True)


def _inline_kwargs_generator(schema_view: SchemaView) -> ContextGenerator:
    """The generator exactly as the pipeline and the postprocessor built it before typed options."""
    return ContextGenerator(schema_view.schema, mergeimports=True, fix_multivalue_containers=True)


def _serialize(generator: ContextGenerator) -> str:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        serialized: str = generator.serialize()
        return serialized


def test_options_defaults() -> None:
    assert JsonLdContextOptions() == JsonLdContextOptions(multivalue_containers=True)


def test_options_are_frozen_with_exactly_one_field() -> None:
    options = JsonLdContextOptions()
    assert [f.name for f in dataclasses.fields(JsonLdContextOptions)] == ["multivalue_containers"]
    with pytest.raises(dataclasses.FrozenInstanceError):
        options.multivalue_containers = False  # type: ignore[misc]


def test_from_options_returns_wot_generator(td_schema_view: SchemaView) -> None:
    generator = WotContextGenerator.from_options(td_schema_view.schema, JsonLdContextOptions())
    assert isinstance(generator, WotContextGenerator)


def test_from_options_matches_todays_inline_constructor_state(td_schema_view: SchemaView) -> None:
    wot = WotContextGenerator.from_options(td_schema_view.schema, JsonLdContextOptions())
    upstream = _inline_kwargs_generator(td_schema_view)
    assert {name: getattr(wot, name) for name in CONSTRUCTOR_STATE} == {
        name: getattr(upstream, name) for name in CONSTRUCTOR_STATE
    }


def test_non_default_options_map_to_upstream_arguments(td_schema_view: SchemaView) -> None:
    wot = WotContextGenerator.from_options(td_schema_view.schema, JsonLdContextOptions(multivalue_containers=False))
    assert wot.fix_multivalue_containers is False


def test_default_options_serialize_equals_todays_inline_generator(td_schema_view: SchemaView) -> None:
    wot = WotContextGenerator.from_options(td_schema_view.schema, JsonLdContextOptions())
    assert _serialize(wot) == _serialize(_inline_kwargs_generator(td_schema_view))


@pytest.mark.parametrize("slot_name", list(TODAYS_SLOT_TERMS))
def test_slot_term_definition_equals_todays_native_slot_context(td_schema_view: SchemaView, slot_name: str) -> None:
    generator = WotContextGenerator.from_options(td_schema_view.schema, JsonLdContextOptions())
    term = generator.slot_term_definition(td_schema_view.all_slots()[slot_name])
    assert json.dumps(term) == json.dumps(TODAYS_SLOT_TERMS[slot_name])


def test_slot_term_definition_is_independent_of_earlier_calls(td_schema_view: SchemaView) -> None:
    generator = WotContextGenerator.from_options(td_schema_view.schema, JsonLdContextOptions())
    slots = td_schema_view.all_slots()
    terms = {name: generator.slot_term_definition(slots[name]) for name in TODAYS_SLOT_TERMS}
    assert json.dumps(terms) == json.dumps(TODAYS_SLOT_TERMS)


def test_slot_term_definition_without_multivalue_containers(td_schema_view: SchemaView) -> None:
    options = JsonLdContextOptions(multivalue_containers=False)
    generator = WotContextGenerator.from_options(td_schema_view.schema, options)
    term = generator.slot_term_definition(td_schema_view.all_slots()["forms"])
    assert json.dumps(term) == json.dumps({"@type": "@id", "@id": "hasForm"})

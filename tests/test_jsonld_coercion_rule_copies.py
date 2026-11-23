"""The inline coercion rules in ``_module_terms`` match the merged context's coercion functions, bar pinned cases."""

from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml_runtime.linkml_model.meta import SlotDefinition
from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.artifacts.jsonld_context import coercions as coercion_rules
from wot_toolchain.artifacts.jsonld_context import module_context as jsonld
from wot_toolchain.config import load_project
from wot_toolchain.schema_utils import load_schema_view

CONFIG = Path(__file__).resolve().parent.parent / "wot-toolchain.yaml"

type Coercion = tuple[Any, bool]
type InlineAndChain = tuple[Coercion, Coercion]

EXPECTED_DIFFERENCES: dict[tuple[str, str], InlineAndChain] = {
    ("hctl", "type"): ((None, False), ("@vocab", False)),
    ("jsonschema", "title"): (("rdfs:Literal", False), (None, False)),
    ("jsonschema", "description"): (("rdfs:Literal", False), (None, False)),
    ("td", "title"): (("rdfs:Literal", False), (None, False)),
    ("td", "description"): (("rdfs:Literal", False), (None, False)),
    ("wotsec", "description"): (("rdfs:Literal", False), (None, False)),
}


def _coercion(entry: Any) -> Coercion:
    if isinstance(entry, dict):
        return entry.get("@type"), "@context" in entry
    return entry, False


def _apply_function_chain(context: dict[str, Any], schema_view: SchemaView) -> None:
    """Run the merged context's coercion passes in the order ``post_process_jsonld_context`` uses."""
    coercion_rules.remove_literal_type_coercion(context)
    coercion_rules.strip_skos_enum_contexts(context)
    coercion_rules.strip_datatype_property_id_coercion(context, schema_view)
    coercion_rules.strip_inlined_class_id_coercion(context, schema_view)
    coercion_rules.fix_vocab_type_coercion(context, schema_view)
    coercion_rules.fix_enum_vocab_type_coercion(context, schema_view)
    coercion_rules.fix_object_property_id_coercion(context, schema_view)


def _record_module_terms(
    schema_view: SchemaView, generator: ContextGenerator, prefix: str
) -> list[tuple[SlotDefinition, dict[str, Any], Any]]:
    """Run ``_module_terms`` and return each slot with its native entry before and after the inline rules."""
    native_slot_context: Callable[[ContextGenerator, SlotDefinition], Any] = jsonld.native_slot_context
    recorded: list[tuple[SlotDefinition, dict[str, Any], Any]] = []

    def recording(gen: ContextGenerator, slot: SlotDefinition) -> Any:
        entry = native_slot_context(gen, slot)
        recorded.append((slot, deepcopy(entry), entry))
        return entry

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(jsonld, "native_slot_context", recording)
        jsonld._module_terms(schema_view, generator, prefix)
    return recorded


def _compare_module(schema_view: SchemaView, generator: ContextGenerator, prefix: str) -> dict[str, InlineAndChain]:
    """Map each slot term of one module to its (inline, function-chain) coercion."""
    recorded = _record_module_terms(schema_view, generator, prefix)
    # Same native entry into both rule sets, chain on a flat context: keeps scoping and non-root removal out.
    # The rules touch only @type and @context; @language handling runs before them in both routes, so replay it.
    chain_context: dict[str, Any] = {}
    for slot, native, _ in recorded:
        entry = deepcopy(native)
        if isinstance(entry, dict) and jsonld._annotation_value(slot, "jsonld_container") == "@language":
            entry.pop("@type", None)
        chain_context[jsonld._slot_key(slot)] = entry
    _apply_function_chain(chain_context, schema_view)
    return {
        jsonld._slot_key(slot): (_coercion(inline), _coercion(chain_context[jsonld._slot_key(slot)]))
        for slot, _, inline in recorded
    }


@pytest.fixture(scope="module")
def module_prefixes() -> set[str]:
    project = load_project(CONFIG)
    return {vocabulary.prefix for vocabulary in project.vocabularies if vocabulary.context is not None}


@pytest.fixture(scope="module")
def coercions(module_prefixes: set[str]) -> dict[tuple[str, str], InlineAndChain]:
    project = load_project(CONFIG)
    schema_view = load_schema_view(project.root_schema, merge_imports=True)
    generator = ContextGenerator(schema_view.schema, mergeimports=True, fix_multivalue_containers=True)
    scopes = {
        scope for slot in jsonld._context_slots(schema_view) if (scope := jsonld._context_scope(schema_view, slot))
    }
    return {
        (prefix, term): pair
        for prefix in sorted(module_prefixes | scopes)
        for term, pair in _compare_module(schema_view, generator, prefix).items()
    }


def test_comparison_covers_every_module_and_scope(
    coercions: dict[tuple[str, str], InlineAndChain], module_prefixes: set[str]
) -> None:
    covered = {prefix for prefix, _ in coercions}
    assert module_prefixes <= covered
    assert len(coercions) > len(EXPECTED_DIFFERENCES)


def test_inline_copy_matches_function_chain_except_pinned_differences(
    coercions: dict[tuple[str, str], InlineAndChain],
) -> None:
    differences = {key: pair for key, pair in coercions.items() if pair[0] != pair[1]}
    assert differences == EXPECTED_DIFFERENCES

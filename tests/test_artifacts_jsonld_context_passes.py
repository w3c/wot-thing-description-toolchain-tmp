from typing import Any

from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.artifacts.jsonld_context.passes import POST_SCOPING_PASSES, PRE_SCOPING_PASSES
from wot_toolchain.artifacts.passes import Pass, run_passes

SCHEMA = """
id: https://example.org/probe
name: probe
prefixes:
  linkml: https://w3id.org/linkml/
  owl: http://www.w3.org/2002/07/owl#
  ex: https://example.org/ex#
  other: https://example.org/other#
default_prefix: ex
imports: [linkml:types]
slots:
  rel:
    slot_uri: ex:rel
    range: uriorcurie
    implements: [owl:ObjectProperty]
  kind:
    slot_uri: ex:kind
    range: Kind
classes:
  Holder:
    slots: [rel, kind]
enums:
  Kind:
    permissible_values:
      thing:
        meaning: other:Thing
"""

PRE_SCOPING_ORDER_BEFORE_THE_MOVE = [
    "remove_reserved_jsonld_slots",
    "apply_fixed_jsonld_term_mappings",
    "fix_keyed_map_identifier_slots",
]

POST_SCOPING_ORDER_BEFORE_THE_MOVE = [
    "remove_uninduced_slots",
    "remove_literal_type_coercion",
    "strip_skos_enum_contexts",
    "strip_datatype_property_id_coercion",
    "strip_inlined_class_id_coercion",
    "fix_vocab_type_coercion",
    "fix_enum_vocab_type_coercion",
    "fix_object_property_id_coercion",
    "fix_type_designator_mapping",
    "add_enum_value_aliases",
    "remove_linkml_internals",
    "remove_non_root_terms",
]

VOCAB = "fix_vocab_type_coercion"
OBJECT_PROPERTY = "fix_object_property_id_coercion"
ALIASES = "add_enum_value_aliases"
NON_ROOT = "remove_non_root_terms"


def _run(passes: list[Pass]) -> dict[str, Any]:
    context: dict[str, Any] = {"rel": {"@id": "ex:rel", "@type": "xsd:anyURI"}, "kind": {"@id": "ex:kind"}}
    run_passes(passes, context, SchemaView(SCHEMA), ())
    return context


def _swapped(first: str, second: str) -> list[Pass]:
    passes = list(POST_SCOPING_PASSES)
    i, j = (next(n for n, p in enumerate(passes) if p.name == name) for name in (first, second))
    passes[i], passes[j] = passes[j], passes[i]
    return passes


def test_passes_run_in_the_order_of_the_legacy_postprocessor() -> None:
    assert [p.name for p in PRE_SCOPING_PASSES] == PRE_SCOPING_ORDER_BEFORE_THE_MOVE
    assert [p.name for p in POST_SCOPING_PASSES] == POST_SCOPING_ORDER_BEFORE_THE_MOVE


def test_every_pass_has_a_reason() -> None:
    assert all(p.reason.strip() for p in (*PRE_SCOPING_PASSES, *POST_SCOPING_PASSES))


def test_uriorcurie_object_property_is_coerced_to_vocab_and_foreign_enum_alias_leaves_the_root() -> None:
    context = _run(list(POST_SCOPING_PASSES))

    assert context["rel"]["@type"] == "@vocab"
    assert "thing" not in context


def test_object_property_coercion_before_vocab_coercion_would_coerce_a_uriorcurie_slot_to_id() -> None:
    assert _run(_swapped(VOCAB, OBJECT_PROPERTY))["rel"]["@type"] == "@id"


def test_removing_non_root_terms_before_adding_enum_aliases_would_keep_a_foreign_alias_at_the_root() -> None:
    assert _run(_swapped(ALIASES, NON_ROOT))["thing"] == "other:Thing"

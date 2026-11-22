"""Legacy import path of the JSON-LD context transforms in ``wot_toolchain.artifacts.jsonld_context``.

The per-module context builder and the merged-context entry point still live here: a test replaces
``_native_slot_context`` on this module, which only reaches ``_module_terms`` while it is defined here.
"""

from __future__ import annotations

import json
from collections.abc import Collection
from typing import Any

from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml_runtime.linkml_model.meta import SlotDefinition
from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.artifacts.jsonld_context.coercions import SKOS_ENUM_KEYS as _SKOS_ENUM_KEYS
from wot_toolchain.artifacts.jsonld_context.coercions import (
    fix_enum_vocab_type_coercion as _fix_enum_vocab_type_coercion,
)
from wot_toolchain.artifacts.jsonld_context.coercions import (
    fix_object_property_id_coercion as _fix_object_property_id_coercion,
)
from wot_toolchain.artifacts.jsonld_context.coercions import fix_vocab_type_coercion as _fix_vocab_type_coercion
from wot_toolchain.artifacts.jsonld_context.coercions import (
    remove_literal_type_coercion as _remove_literal_type_coercion,
)
from wot_toolchain.artifacts.jsonld_context.coercions import (
    strip_datatype_property_id_coercion as _strip_datatype_property_id_coercion,
)
from wot_toolchain.artifacts.jsonld_context.coercions import (
    strip_inlined_class_id_coercion as _strip_inlined_class_id_coercion,
)
from wot_toolchain.artifacts.jsonld_context.coercions import strip_skos_enum_contexts as _strip_skos_enum_contexts
from wot_toolchain.artifacts.jsonld_context.generator import WotContextGenerator
from wot_toolchain.artifacts.jsonld_context.identifiers import (
    fix_keyed_map_identifier_slots as _fix_keyed_map_identifier_slots,
)
from wot_toolchain.artifacts.jsonld_context.options import JsonLdContextOptions
from wot_toolchain.artifacts.jsonld_context.passes import POST_SCOPING_PASSES, PRE_SCOPING_PASSES
from wot_toolchain.artifacts.jsonld_context.scoped_contexts import apply_class_mappings as _apply_class_mappings
from wot_toolchain.artifacts.jsonld_context.scoped_contexts import apply_root_mapping as _apply_root_mapping
from wot_toolchain.artifacts.jsonld_context.scopes import context_scope as _context_scope
from wot_toolchain.artifacts.jsonld_context.terms import context_slots as _context_slots
from wot_toolchain.artifacts.jsonld_context.terms import curie_term_name as _curie_term_name
from wot_toolchain.artifacts.jsonld_context.terms import prefix_declarations as _prefix_declarations
from wot_toolchain.artifacts.jsonld_context.terms import slot_key as _slot_key
from wot_toolchain.artifacts.passes import run_passes
from wot_toolchain.schema_utils import annotation_str_value as _annotation_value
from wot_toolchain.schema_utils import curie_prefix, resolve_prefix_namespace

__all__ = [
    "_fix_enum_vocab_type_coercion",
    "_fix_object_property_id_coercion",
    "_fix_vocab_type_coercion",
    "_remove_literal_type_coercion",
    "_strip_datatype_property_id_coercion",
    "_strip_inlined_class_id_coercion",
    "_strip_skos_enum_contexts",
    "build_module_context",
    "post_process_jsonld_context",
]


def _native_slot_context(generator: ContextGenerator, slot: SlotDefinition) -> Any:
    # Called unbound because build_module_context also accepts plain upstream generators.
    return WotContextGenerator.slot_term_definition(generator, slot)


def _cross_module_slot_keys(schema_view: SchemaView, prefix: str) -> set[str]:
    """Slot keys used by classes in this module but defined in other modules."""
    keys: set[str] = set()
    for cls in schema_view.all_classes().values():
        cls_prefix = curie_prefix(str(cls.class_uri) if cls.class_uri else None)
        if cls_prefix != prefix:
            continue
        for slot in schema_view.class_induced_slots(cls.name):
            slot_prefix = curie_prefix(str(slot.slot_uri) if slot.slot_uri else None)
            key = _slot_key(slot)
            if slot_prefix and slot_prefix != prefix and not key.startswith("@"):
                keys.add(key)
    return keys


def build_module_context(
    schema_view: SchemaView,
    generator: ContextGenerator,
    prefix: str,
) -> dict[str, Any]:
    """Build a standalone JSON-LD context dict for one vocabulary module.

    The context declares every schema prefix its CURIEs reference, so it expands on its own.
    A term whose name equals a prefix keeps its term definition.
    """
    terms = _module_terms(schema_view, generator, prefix)
    referenced = _referenced_prefixes(terms)
    prefixes = {name: ns for name, ns in _prefix_declarations(schema_view).items() if name in referenced}
    return {"@vocab": terms["@vocab"], **prefixes, **terms}


def _referenced_prefixes(node: Any) -> set[str]:
    """Collect the prefix part of every CURIE-shaped string value in a context node."""
    if isinstance(node, str):
        prefix = curie_prefix(node)
        return {prefix} if prefix else set()
    if isinstance(node, dict):
        return set().union(*(_referenced_prefixes(value) for value in node.values()))
    if isinstance(node, list):
        return set().union(*(_referenced_prefixes(item) for item in node))
    return set()


def _module_terms(
    schema_view: SchemaView,
    generator: ContextGenerator,
    prefix: str,
) -> dict[str, Any]:
    """Build the ``@vocab`` and term definitions of one vocabulary module, without prefix declarations."""
    ns = resolve_prefix_namespace(schema_view, prefix)
    context: dict[str, Any] = {"@vocab": ns}
    slots = _context_slots(schema_view)
    all_classes = schema_view.all_classes()
    seen_keys: set[str] = set()
    cross_module = _cross_module_slot_keys(schema_view, prefix)
    designator_slots = {
        _slot_key(slot)
        for slot in schema_view.all_slots().values()
        if slot.designates_type
        and any(
            curie_prefix(str(c.class_uri) if c.class_uri else None) == prefix
            for c in schema_view.all_classes().values()
            if slot.name in [s.name for s in schema_view.class_induced_slots(c.name)]
        )
    }
    for slot in slots:
        key = _slot_key(slot)
        slot_prefix = curie_prefix(str(slot.slot_uri) if slot.slot_uri else None)
        if slot_prefix != prefix and key not in cross_module and key not in designator_slots:
            continue
        if key in designator_slots:
            context[key] = {"@id": "@type"}
            seen_keys.add(key)
            continue
        if key in seen_keys:
            continue
        seen_keys.add(key)
        entry = _native_slot_context(generator, slot)
        if key in cross_module and isinstance(entry, dict):
            bare_id = entry.get("@id", key)
            if ":" not in bare_id:
                entry["@id"] = f"{slot_prefix}:{bare_id}"
        if container := _annotation_value(slot, "jsonld_container"):
            entry["@container"] = container
            if container == "@language":
                entry.pop("@index", None)
                entry.pop("@type", None)
        elif index := _annotation_value(slot, "jsonld_index"):
            entry["@index"] = _curie_term_name(index)
        if isinstance(entry, dict):
            inner = entry.get("@context")
            if isinstance(inner, dict) and _SKOS_ENUM_KEYS.issubset(inner):
                del entry["@context"]
            if entry.get("@type") == "@id" and "owl:DatatypeProperty" in (slot.implements or []):
                entry.pop("@type")
            if entry.get("@type") == "xsd:anyURI" and slot.range == "uriorcurie":
                entry["@type"] = "@vocab"
            if entry.get("@type") == "xsd:anyURI" and "owl:ObjectProperty" in (slot.implements or []):
                entry["@type"] = "@id"
            if (
                "@type" not in entry
                and slot.range == "string"
                and "owl:ObjectProperty" in (slot.implements or [])
                and slot.domain
                and slot.domain in all_classes
                and not any(s.designates_type for s in schema_view.class_induced_slots(slot.domain))
            ):
                entry["@type"] = "@id"
            if (
                entry.get("@type") == "@id"
                and schema_view.is_inlined(slot)
                and slot.range in all_classes
                and "owl:ObjectProperty" not in (slot.implements or [])
                and not any(s.identifier for s in schema_view.class_induced_slots(slot.range))
            ):
                del entry["@type"]
            if "@type" not in entry and not slot.designates_type:
                enum_def = schema_view.get_enum(slot.range) if slot.range else None
                if enum_def and any(pv.meaning for pv in enum_def.permissible_values.values()):
                    entry["@type"] = "@vocab"
        context[key] = entry
    for cls in schema_view.all_classes().values():
        cls_prefix = curie_prefix(str(cls.class_uri) if cls.class_uri else None)
        if cls_prefix == prefix:
            context[cls.name] = {"@id": str(cls.class_uri)}
    for enum_def in schema_view.all_enums().values():
        for pv_name, pv in enum_def.permissible_values.items():
            if pv.meaning and curie_prefix(str(pv.meaning)) == prefix:
                key = str(pv_name)
                if key not in context:
                    context[key] = str(pv.meaning)
    _fix_keyed_map_identifier_slots(context, schema_view)
    return context


def _module_contexts(schema_view: SchemaView, generator: ContextGenerator) -> dict[str, dict[str, Any]]:
    scopes = {scope for slot in _context_slots(schema_view) if (scope := _context_scope(schema_view, slot))}
    # Scoped blocks inherit prefixes from _apply_root_mapping, so they take the terms alone.
    return {scope: _module_terms(schema_view, generator, scope) for scope in scopes}


def post_process_jsonld_context(
    schema_view: SchemaView, serialized_schema: str, *, extra_root_terms: Collection[str]
) -> str:
    """Add schema-declared scoped contexts and index predicates to LinkML output.

    LinkML natively emits container mappings when
    ``fix_multivalue_containers`` is enabled. It does not currently emit the
    RDF predicate represented by a keyed map, or scoped vocabulary contexts.

    Args:
        schema_view: SchemaView of the main schema.
        serialized_schema: JSON-LD context serialized by LinkML's ``ContextGenerator``.
        extra_root_terms: Terms outside the schema's default prefix that stay in the root context.

    Returns:
        The post-processed JSON-LD context document, serialized as JSON.

    Raises:
        SchemaError: Schema content cannot be composed into a JSON-LD context (the message names the
            offending element), or an extra root term is not in the generated root context.
    """
    document = json.loads(serialized_schema)
    context = document["@context"]
    run_passes(PRE_SCOPING_PASSES, context, schema_view, extra_root_terms)
    generator = WotContextGenerator.from_options(schema_view.schema, JsonLdContextOptions())
    module_contexts = _module_contexts(schema_view, generator)
    for slot in schema_view.all_slots().values():
        _apply_root_mapping(context, schema_view, slot, module_contexts)
    _apply_class_mappings(schema_view, context, module_contexts)
    run_passes(POST_SCOPING_PASSES, context, schema_view, extra_root_terms)
    context["@version"] = 1.1
    return json.dumps(document, indent=2)

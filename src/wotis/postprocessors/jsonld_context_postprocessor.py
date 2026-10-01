"""Compose the WoT JSON-LD context from LinkML-declared mappings."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml_runtime.linkml_model.meta import SlotDefinition
from linkml_runtime.utils.formatutils import underscore
from linkml_runtime.utils.schemaview import SchemaView

JSONLD_RESERVED_SLOT_NAMES = frozenset({"@context", "@type"})
JSONLD_FIXED_TERM_MAPPINGS = {"id": "@id"}


def _annotation_value(annotatable: Any, key: str) -> str | None:
    annotations = getattr(annotatable, "annotations", None) or {}
    annotation = (
        annotations.get(key)
        if isinstance(annotations, dict)
        else getattr(annotations, key, None)
    )
    return str(annotation.value) if annotation else None


def _context_slots(schema_view: SchemaView) -> list[SlotDefinition]:
    slots = list(schema_view.all_slots().values())
    for class_name in schema_view.all_classes():
        slots.extend(schema_view.class_induced_slots(class_name))
    return slots


def _slot_key(slot: SlotDefinition) -> str:
    return underscore(slot.alias or slot.name)


def _uri_prefix(uri: str | None) -> str | None:
    if uri is None or ":" not in uri:
        return None
    return uri.partition(":")[0]


def _owned_vocabulary_prefix(schema_view: SchemaView, class_name: str) -> str | None:
    class_definition = schema_view.get_class(class_name)
    prefix = _uri_prefix(str(class_definition.class_uri) if class_definition.class_uri else None)
    if prefix is None:
        return None
    if any(
        _uri_prefix(str(induced_slot.slot_uri) if induced_slot.slot_uri else None) == prefix
        for induced_slot in schema_view.class_induced_slots(class_name)
    ):
        return prefix
    return None


def _native_slot_context(generator: ContextGenerator, slot: SlotDefinition) -> dict[str, Any]:
    generator.context_body.clear()
    generator.visit_schema()
    if slot.range is None:
        entry: dict[str, Any] = {}
        generator._build_element_id(entry, slot.slot_uri)
        return entry
    generator.visit_slot(slot.alias or slot.name, slot)
    native_key = underscore(slot.alias or slot.name)
    return deepcopy(generator.context_body[native_key])


def _remove_reserved_jsonld_slots(context: dict[str, Any]) -> None:
    for keyword in JSONLD_RESERVED_SLOT_NAMES:
        context.pop(keyword, None)


def _apply_fixed_jsonld_term_mappings(context: dict[str, Any]) -> None:
    context.update(JSONLD_FIXED_TERM_MAPPINGS)


def _remove_keyed_map_identifier_slots(context: dict[str, Any], schema_view: SchemaView) -> None:
    keyed_map_identifier_keys = {
        _slot_key(member_slot)
        for map_slot in _context_slots(schema_view)
        if _annotation_value(map_slot, "jsonld_index") and map_slot.range in schema_view.all_classes()
        for member_slot in schema_view.class_induced_slots(map_slot.range)
        if member_slot.identifier
    }
    for key in keyed_map_identifier_keys:
        context.pop(key, None)


def _context_scope(schema_view: SchemaView, slot: SlotDefinition) -> str | None:
    if explicit_scope := _annotation_value(slot, "jsonld_context"):
        if explicit_scope not in schema_view.schema.prefixes:
            raise ValueError(f"Unknown jsonld_context prefix: {explicit_scope}")
        return explicit_scope
    if slot.range not in schema_view.all_classes():
        return None

    prefixes = {
        prefix
        for class_name in schema_view.class_ancestors(
            slot.range, reflexive=True, mixins=True
        )
        if (prefix := _owned_vocabulary_prefix(schema_view, class_name))
    }
    prefixes.discard(_uri_prefix(str(slot.slot_uri) if slot.slot_uri else None))
    unknown_prefixes = prefixes - set(schema_view.schema.prefixes)
    if unknown_prefixes:
        raise ValueError(f"Unknown class URI prefix for {slot.range}: {sorted(unknown_prefixes)}")
    if len(prefixes) > 1:
        raise ValueError(
            f"Ambiguous JSON-LD context for {slot.name}: {sorted(prefixes)}. "
            "Declare jsonld_context explicitly."
        )
    return next(iter(prefixes), None)


def _module_contexts(schema_view: SchemaView, generator: ContextGenerator) -> dict[str, dict[str, Any]]:
    scopes = {
        scope
        for slot in _context_slots(schema_view)
        if (scope := _context_scope(schema_view, slot))
    }
    contexts: dict[str, dict[str, Any]] = {}
    for scope in scopes:
        prefix = schema_view.schema.prefixes.get(scope)
        if prefix is None:
            raise ValueError(f"Unknown jsonld_context prefix: {scope}")
        context: dict[str, Any] = {"@vocab": str(prefix.prefix_reference)}
        for slot in _context_slots(schema_view):
            if not slot.slot_uri or not str(slot.slot_uri).startswith(f"{scope}:"):
                continue
            entry = _native_slot_context(generator, slot)
            if index := _annotation_value(slot, "jsonld_index"):
                entry["@index"] = index
            context[_slot_key(slot)] = entry
        contexts[scope] = context
    return contexts


def _apply_root_mapping(
    context: dict[str, Any],
    schema_view: SchemaView,
    slot: SlotDefinition,
    module_contexts: dict[str, dict[str, Any]],
) -> None:
    key = _slot_key(slot)
    entry = context.get(key)
    if not isinstance(entry, dict):
        return
    if index := _annotation_value(slot, "jsonld_index"):
        entry["@index"] = index
    if scope := _context_scope(schema_view, slot):
        entry["@context"] = deepcopy(module_contexts[scope])


def _apply_class_mappings(
    schema_view: SchemaView,
    context: dict[str, Any],
    module_contexts: dict[str, dict[str, Any]],
) -> None:
    global_uris = {
        _slot_key(slot): str(slot.slot_uri)
        for slot in schema_view.all_slots().values()
        if slot.slot_uri
    }
    for class_name in schema_view.all_classes():
        for slot in schema_view.class_induced_slots(class_name):
            key = _slot_key(slot)
            if global_uris.get(key) not in {None, str(slot.slot_uri)}:
                continue
            _apply_root_mapping(context, schema_view, slot, module_contexts)


def post_process_jsonld_context(schema_view: SchemaView, serialized_schema: str) -> str:
    """Add schema-declared scoped contexts and index predicates to LinkML output.

    LinkML natively emits container mappings when
    ``fix_multivalue_containers`` is enabled. It does not currently emit the
    RDF predicate represented by a keyed map, or scoped vocabulary contexts.
    """
    document = json.loads(serialized_schema)
    context = document["@context"]
    _remove_reserved_jsonld_slots(context)
    _apply_fixed_jsonld_term_mappings(context)
    _remove_keyed_map_identifier_slots(context, schema_view)
    generator = ContextGenerator(
        schema_view.schema,
        mergeimports=True,
        fix_multivalue_containers=True,
    )
    module_contexts = _module_contexts(schema_view, generator)
    for slot in schema_view.all_slots().values():
        _apply_root_mapping(context, schema_view, slot, module_contexts)
    _apply_class_mappings(schema_view, context, module_contexts)
    return json.dumps(document, indent=2)

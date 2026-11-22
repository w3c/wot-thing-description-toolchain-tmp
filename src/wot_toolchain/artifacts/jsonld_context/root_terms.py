"""Transforms that decide which terms the root JSON-LD context declares."""

from collections.abc import Collection
from typing import Any

from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.artifacts.jsonld_context.terms import context_slots, curie_term_name, slot_key
from wot_toolchain.errors import SchemaError
from wot_toolchain.schema_utils import annotation_str_value, curie_prefix, default_prefix, get_schema

JSONLD_RESERVED_SLOT_NAMES = frozenset({"@context", "@type"})
JSONLD_FIXED_TERM_MAPPINGS = {"id": "@id"}


def remove_reserved_jsonld_slots(context: dict[str, Any]) -> None:
    """Remove the terms named after a JSON-LD keyword."""
    for keyword in JSONLD_RESERVED_SLOT_NAMES:
        context.pop(keyword, None)


def apply_fixed_jsonld_term_mappings(context: dict[str, Any]) -> None:
    """Set the terms whose mapping is fixed."""
    context.update(JSONLD_FIXED_TERM_MAPPINGS)


def uninduced_slot_keys(schema_view: SchemaView) -> frozenset[str]:
    """Slot keys that no class induces and that no @index annotation references."""
    induced: set[str] = set()
    for cls_name in schema_view.all_classes():
        for slot in schema_view.class_induced_slots(cls_name):
            induced.add(slot.name)
    index_terms: set[str] = set()
    for slot in context_slots(schema_view):
        if idx := annotation_str_value(slot, "jsonld_index"):
            index_terms.add(curie_term_name(idx))
    never_induced = set(schema_view.all_slots().keys()) - induced
    return frozenset(
        slot_key(schema_view.get_slot(s)) for s in never_induced if slot_key(schema_view.get_slot(s)) not in index_terms
    )


def remove_uninduced_slots(context: dict[str, Any], keys_to_remove: frozenset[str]) -> None:
    """Remove slots from root and all scoped contexts that are never induced by any class."""
    for key in keys_to_remove:
        context.pop(key, None)
    for val in context.values():
        if isinstance(val, dict) and "@context" in val:
            remove_uninduced_slots(val["@context"], keys_to_remove)


def add_enum_value_aliases(context: dict[str, Any], schema_view: SchemaView) -> None:
    """Add term aliases for enum permissible values that declare a ``meaning``.

    LinkML does not emit JSON-LD context entries for enum values.  When a
    permissible value carries a ``meaning`` CURIE the upstream W3C context
    maps the lowercase value text to the class IRI so that e.g.
    ``"type": "object"`` expands to ``jsonschema:ObjectSchema``.
    """
    for enum_def in schema_view.all_enums().values():
        for pv_name, pv in enum_def.permissible_values.items():
            if pv.meaning and str(pv_name) not in context:
                context[str(pv_name)] = str(pv.meaning)


def remove_linkml_internals(context: dict[str, Any]) -> None:
    """Strip LinkML-internal prefix and type declarations from a context dict."""
    context.pop("linkml", None)
    linkml_terms = [
        key for key, val in context.items() if isinstance(val, dict) and str(val.get("@id", "")).startswith("linkml:")
    ]
    for key in linkml_terms:
        del context[key]
    for val in context.values():
        if isinstance(val, dict) and "@context" in val:
            remove_linkml_internals(val["@context"])


def remove_non_root_terms(context: dict[str, Any], schema_view: SchemaView, extra_root_terms: Collection[str]) -> None:
    """Remove terms outside the main schema's default prefix from the root context.

    The LinkML context generator and enum-alias step emit all slots, class
    names, and enum value aliases at root level.  Only terms of the main
    vocabulary (the schema's ``default_prefix``) plus the project's extra root
    terms belong at root — all other module terms are already present inside
    scoped ``@context`` blocks built by ``_module_terms``.

    Args:
        context: Root ``@context`` dict, modified in place.
        schema_view: SchemaView of the main schema.
        extra_root_terms: Terms outside the default prefix that stay in the root context.

    Raises:
        SchemaError: The SchemaView has no schema loaded, its ``default_prefix``
            is unset or not declared in its ``prefixes``, or an extra root term
            is not in the generated root context.
    """
    missing = [term for term in extra_root_terms if term not in context]
    if missing:
        raise SchemaError(
            f"Extra root term(s) {', '.join(map(repr, missing))} are not in the JSON-LD context generated from "
            f"schema {get_schema(schema_view).name!r}. Remove them from 'jsonld.extra_root_terms' in the manifest "
            "or define them in the schema."
        )
    root_prefix = default_prefix(schema_view)
    root_slots: set[str] = set()
    non_root_slots: set[str] = set()
    for slot in schema_view.all_slots().values():
        key = slot_key(slot)
        prefix = curie_prefix(str(slot.slot_uri) if slot.slot_uri else None)
        if prefix is None or prefix == root_prefix:
            root_slots.add(key)
        else:
            non_root_slots.add(key)
    non_root_slots -= root_slots

    root_classes: set[str] = set()
    non_root_classes: set[str] = set()
    for cls in schema_view.all_classes().values():
        prefix = curie_prefix(str(cls.class_uri) if cls.class_uri else None)
        if prefix is None or prefix == root_prefix:
            root_classes.add(cls.name)
        else:
            non_root_classes.add(cls.name)
    non_root_classes -= root_classes

    non_root_enum_aliases: set[str] = set()
    for enum_def in schema_view.all_enums().values():
        for pv_name, pv in enum_def.permissible_values.items():
            if pv.meaning:
                meaning_prefix = curie_prefix(str(pv.meaning))
                if meaning_prefix and meaning_prefix != root_prefix:
                    non_root_enum_aliases.add(str(pv_name))

    remove = set()
    for key in context:
        if key.startswith("@"):
            continue
        if key in extra_root_terms:
            continue
        if key in non_root_slots or key in non_root_classes or key in non_root_enum_aliases:
            remove.add(key)

    for key in remove:
        del context[key]

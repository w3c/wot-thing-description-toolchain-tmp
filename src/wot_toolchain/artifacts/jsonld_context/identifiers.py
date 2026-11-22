"""Mapping of the identifier slots of keyed-map members to their declared predicate."""

from typing import Any

from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.artifacts.jsonld_context.terms import context_slots, slot_key
from wot_toolchain.schema_utils import annotation_str_value


def _resolve_identifier_slot_uri(
    schema_view: SchemaView,
    class_name: str,
    slot_name: str,
) -> str | None:
    """Walk the class hierarchy to find a slot_uri for an identifier slot."""
    for ancestor in schema_view.class_ancestors(class_name, reflexive=True, mixins=True):
        cls = schema_view.get_class(ancestor)
        attrs = getattr(cls, "attributes", None) or {}
        attr = attrs.get(slot_name)
        if attr and attr.slot_uri:
            return str(attr.slot_uri)
    return None


def fix_keyed_map_identifier_slots(context: dict[str, Any], schema_view: SchemaView) -> None:
    """Replace identifier slots' ``@id`` mapping with their ontology predicate.

    LinkML emits ``"name": "@id"`` for ``identifier: true`` slots, making the
    value the node identifier.  A keyed map carries that name as its key, so
    the slot maps to its declared ``slot_uri`` instead.  When no ``slot_uri``
    exists anywhere in the class hierarchy the slot is purely structural and
    is removed from the context.
    """
    identifier_fixes: dict[str, str | None] = {}
    for map_slot in context_slots(schema_view):
        if (
            not annotation_str_value(map_slot, "jsonld_index")
            and annotation_str_value(map_slot, "jsonld_container") != "@id"
        ):
            continue
        if map_slot.range not in schema_view.all_classes():
            continue
        for member_slot in schema_view.class_induced_slots(map_slot.range):
            if not member_slot.identifier:
                continue
            key = slot_key(member_slot)
            if key in identifier_fixes:
                continue
            uri = (
                str(member_slot.slot_uri)
                if member_slot.slot_uri
                else _resolve_identifier_slot_uri(schema_view, map_slot.range, member_slot.name)
            )
            identifier_fixes[key] = uri

    for key, uri in identifier_fixes.items():
        existing = context.get(key)
        is_identifier_mapping = existing == "@id" or (isinstance(existing, dict) and existing.get("@id") == "@id")
        if not is_identifier_mapping:
            continue
        if uri:
            context[key] = {"@id": uri}
        else:
            context.pop(key, None)

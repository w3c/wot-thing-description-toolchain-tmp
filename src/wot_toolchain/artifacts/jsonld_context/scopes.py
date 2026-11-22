"""Selection of the vocabulary whose scoped context a slot carries."""

from linkml_runtime.linkml_model.meta import SlotDefinition
from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.errors import SchemaError
from wot_toolchain.schema_utils import annotation_str_value, curie_prefix


def _owned_vocabulary_prefix(schema_view: SchemaView, class_name: str) -> str | None:
    class_definition = schema_view.get_class(class_name)
    prefix = curie_prefix(str(class_definition.class_uri) if class_definition.class_uri else None)
    if prefix is None:
        return None
    if any(
        curie_prefix(str(induced_slot.slot_uri) if induced_slot.slot_uri else None) == prefix
        for induced_slot in schema_view.class_induced_slots(class_name)
    ):
        return prefix
    return None


def _refers_by_name(schema_view: SchemaView, slot: SlotDefinition) -> bool:
    """Check whether a value of ``slot`` is the name of a node defined elsewhere, not the node itself."""
    if slot.range not in schema_view.all_classes() or not schema_view.get_identifier_slot(slot.range, use_key=True):
        return False
    holders = (slot, *slot.exactly_one_of, *slot.any_of)
    return not any(holder.inlined or holder.inlined_as_list for holder in holders)


def context_scope(schema_view: SchemaView, slot: SlotDefinition) -> str | None:
    """Return the prefix of the module context that scopes a slot, or None when it has no scoped context."""
    if explicit_scope := annotation_str_value(slot, "jsonld_context"):
        if explicit_scope == "none":
            return None
        if explicit_scope not in schema_view.schema.prefixes:
            raise SchemaError(
                f"slot {slot.name!r}: jsonld_context annotation names prefix {explicit_scope!r}, "
                "which the schema does not declare under 'prefixes'."
            )
        return explicit_scope
    if slot.range not in schema_view.all_classes() or _refers_by_name(schema_view, slot):
        return None

    prefixes = {
        prefix
        for class_name in schema_view.class_ancestors(slot.range, reflexive=True, mixins=True)
        if (prefix := _owned_vocabulary_prefix(schema_view, class_name))
    }
    prefixes.discard(curie_prefix(str(slot.slot_uri) if slot.slot_uri else None))
    unknown_prefixes = prefixes - set(schema_view.schema.prefixes)
    if unknown_prefixes:
        raise SchemaError(
            f"slot {slot.name!r}: range {slot.range!r} or its ancestors use class URI prefixes "
            f"{sorted(unknown_prefixes)}, which the schema does not declare under 'prefixes'."
        )
    if len(prefixes) > 1:
        raise SchemaError(
            f"slot {slot.name!r}: ambiguous JSON-LD context, its range {slot.range!r} belongs to vocabularies "
            f"{sorted(prefixes)}. Declare the jsonld_context annotation on the slot."
        )
    return next(iter(prefixes), None)

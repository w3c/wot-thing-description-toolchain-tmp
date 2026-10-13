"""In-memory schema preprocessing for OWL generation."""
from __future__ import annotations

import copy

from linkml_runtime.linkml_model.meta import SchemaDefinition
from linkml_runtime.utils.schemaview import SchemaView

_CONSTRAINT_FIELDS = (
    "exactly_one_of", "any_of", "all_of",
    "minimum_value", "maximum_value",
    "minimum_cardinality", "maximum_cardinality", "exact_cardinality",
)


def preprocess_for_gen_owl(schema: SchemaDefinition, namespace: str, view: SchemaView) -> SchemaDefinition:
    """Return a deep-copy of *schema* prepared for gen-owl consumption.

    Two transformations applied in-memory (schemas on disk unchanged):

    1. Slot rename — slot_uri local name within namespace → slot.name, slot_uri cleared.
       Makes gen-owl emit correct OWL property IRIs (e.g. td:hasForm not td:forms).

    2. Constraint clearing — exactly_one_of, any_of, all_of, minimum_value, maximum_value,
       minimum_cardinality, maximum_cardinality, exact_cardinality cleared on all slots and
       class attributes. Gen-owl converts these to blank-node owl:Restriction axioms absent
       from the upstream WoT TD ontology.

    Integration hook for incrementally replacing the custom OWL generator as gen-owl matures.
    Not on the active generation path.
    """
    s = copy.deepcopy(schema)
    s = _rename_slots(s, namespace, view)
    s = _clear_constraints(s)
    return s


def _rename_slots(s: SchemaDefinition, namespace: str, view: SchemaView) -> SchemaDefinition:
    renames: dict[str, str] = {}
    for slot_name, slot_def in list(s.slots.items()):
        if not slot_def.slot_uri:
            continue
        try:
            expanded = view.expand_curie(slot_def.slot_uri)
        except Exception:
            continue
        if expanded.startswith(namespace):
            new_name = expanded.split("#")[-1].split("/")[-1]
            if new_name != slot_name:
                renames[slot_name] = new_name

    for old_name, new_name in renames.items():
        slot_def = s.slots.pop(old_name)
        slot_def.name = new_name
        slot_def.slot_uri = None
        s.slots[new_name] = slot_def

    for class_def in s.classes.values():
        if class_def.slots:
            class_def.slots = [renames.get(sn, sn) for sn in class_def.slots]

    return s


def _clear_constraints(s: SchemaDefinition) -> SchemaDefinition:
    for slot_def in s.slots.values():
        for f in _CONSTRAINT_FIELDS:
            setattr(slot_def, f, [] if f.endswith("_of") else None)
    for class_def in s.classes.values():
        for attr_def in (class_def.attributes or {}).values():
            for f in _CONSTRAINT_FIELDS:
                setattr(attr_def, f, [] if f.endswith("_of") else None)
    return s

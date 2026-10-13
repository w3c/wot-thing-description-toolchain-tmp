"""In-memory schema transforms before passing to gen-owl. Schemas on disk unchanged."""
from __future__ import annotations

import copy

from linkml_runtime.linkml_model.meta import SchemaDefinition
from linkml_runtime.utils.schemaview import SchemaView

# gen-owl converts these to blank-node owl:Restriction axioms not present in the WoT TD ontology.
_CONSTRAINT_FIELDS = (
    "exactly_one_of", "any_of", "all_of",
    "minimum_value", "maximum_value",
    "minimum_cardinality", "maximum_cardinality", "exact_cardinality",
)


def preprocess_for_gen_owl(schema: SchemaDefinition, namespace: str, view: SchemaView) -> SchemaDefinition:
    """Prepare schema for gen-owl: rename slots to slot_uri local names, clear OWL restrictions."""
    s = copy.deepcopy(schema)
    s = _rename_slots(s, namespace, view)
    s = _clear_constraints(s)
    return s


def _rename_slots(s: SchemaDefinition, namespace: str, view: SchemaView) -> SchemaDefinition:
    # slot_uri local name → slot.name so gen-owl emits td:hasForm instead of td:forms
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

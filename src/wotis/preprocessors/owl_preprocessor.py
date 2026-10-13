"""In-memory schema transforms before passing to gen-owl. Schemas on disk unchanged."""
from __future__ import annotations

import copy

from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.linkml_model.meta import SchemaDefinition
from linkml_runtime.utils.schemaview import SchemaView

# gen-owl converts these to blank-node owl:Restriction axioms not present in the WoT TD ontology.
_CONSTRAINT_FIELDS = (
    "exactly_one_of", "any_of", "all_of",
    "minimum_value", "maximum_value",
    "minimum_cardinality", "maximum_cardinality", "exact_cardinality",
)


def preprocess_for_gen_owl(schema_path: str) -> str:
    """Return a YAML string of the schema ready for gen-owl.

    Loads with merge_imports=True so all slot references are materialized, renames
    top-level slots to their slot_uri local names (td:hasForm not td:forms), clears
    OWL restriction fields, then serializes back to YAML. Caller passes the string
    to OwlSchemaGenerator so it re-parses with its own runtime (avoids JsonObj
    mismatch between linkml and linkml-runtime git versions).
    """
    view = SchemaView(schema_path, merge_imports=True)
    namespace = _namespace(view)
    s = copy.deepcopy(view.schema)
    renames = _collect_renames(s, namespace, view)
    _apply_renames(s, renames)
    _clear_constraints(s)
    return yaml_dumper.dumps(s)


def _namespace(view: SchemaView) -> str:
    prefix = view.schema.prefixes[view.schema.default_prefix]
    return str(prefix.prefix_reference)


def _collect_renames(s: SchemaDefinition, namespace: str, view: SchemaView) -> dict[str, str]:
    # slot_uri local name → slot.name so gen-owl emits td:hasForm instead of td:forms
    renames: dict[str, str] = {}
    for slot_name, slot_def in s.slots.items():
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
    return renames


def _apply_renames(s: SchemaDefinition, renames: dict[str, str]) -> None:
    for old_name, new_name in renames.items():
        slot_def = s.slots.pop(old_name)
        slot_def.name = new_name
        slot_def.slot_uri = None
        s.slots[new_name] = slot_def

    for class_def in s.classes.values():
        if class_def.slots:
            class_def.slots = [renames.get(sn, sn) for sn in class_def.slots]
        if class_def.slot_usage:
            updated: dict = {}
            for k, v in class_def.slot_usage.items():
                new_key = renames.get(k, k)
                if new_key != k:
                    v.name = new_key
                updated[new_key] = v
            class_def.slot_usage = updated


def _clear_constraints(s: SchemaDefinition) -> None:
    for slot_def in s.slots.values():
        for f in _CONSTRAINT_FIELDS:
            setattr(slot_def, f, [] if f.endswith("_of") else None)
    for class_def in s.classes.values():
        for attr_def in (class_def.attributes or {}).values():
            for f in _CONSTRAINT_FIELDS:
                setattr(attr_def, f, [] if f.endswith("_of") else None)

"""In-memory schema transforms before passing to gen-owl. Schemas on disk unchanged."""
from __future__ import annotations

import copy

from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.linkml_model.meta import SchemaDefinition, SlotDefinition
from linkml_runtime.utils.schemaview import SchemaView

# Fields gen-owl converts to blank-node owl:Restriction axioms not present in the WoT TD ontology.
_LIST_CONSTRAINT_FIELDS = ("exactly_one_of", "any_of", "all_of", "none_of")
_SCALAR_CONSTRAINT_FIELDS = (
    "minimum_value", "maximum_value",
    "minimum_cardinality", "maximum_cardinality", "exact_cardinality",
    "pattern", "structured_pattern",
    "equals_string", "equals_number",
)
_LIST_CONSTRAINT_FIELDS_EXTRA = ("equals_string_in", "equals_number_in")


def preprocess_for_gen_owl(schema_path: str) -> str:
    """Return YAML string of schema ready for gen-owl.

    Merges imports for type resolution, then restricts output to vocabulary
    originating in this module only. JSON-LD artifacts and discriminator slots
    are stripped before gen-owl sees the schema.
    """
    view = SchemaView(schema_path, merge_imports=True)
    local_view = SchemaView(schema_path, merge_imports=False)
    local_schema_id = local_view.schema.id
    namespace = _namespace(view)

    # Collect original top-level slots with no slot_uri — pure implementation artifacts.
    original_no_uri_slots = {
        name for name, slot in local_view.schema.slots.items()
        if not slot.slot_uri
    }
    # Classes with no class_uri have no OWL semantics (e.g. MultiLanguage).
    no_uri_classes = {
        name for name, cls in local_view.schema.classes.items()
        if not cls.class_uri
    }

    s = copy.deepcopy(view.schema)
    _assign_enum_uris(s, schema_path, view)
    renames = _collect_renames(s, namespace, view)
    _apply_renames(s, renames)
    _strip_no_uri_classes(s, no_uri_classes)
    _promote_attributes(s, view)
    _strip_non_local(s, local_schema_id, view, namespace)
    _strip_jsonld_slots(s)
    _strip_no_uri_original_slots(s, original_no_uri_slots)
    _strip_discriminator_slots(s, view)
    _infer_ranges_from_branches(s)
    _clear_constraints(s)
    _strip_schema_metadata(s)
    return yaml_dumper.dumps(s)


def _namespace(view: SchemaView) -> str:
    prefix = view.schema.prefixes[view.schema.default_prefix]
    return str(prefix.prefix_reference)


def _assign_enum_uris(s: SchemaDefinition, schema_path: str, view: SchemaView) -> None:
    """Set enum_uri on enums that lack one, using the sub-schema they originate from.

    After merge_imports=True, view.schema.imports is empty (imports were flattened).
    We load the root schema unmerged to recover the original imports list, then
    walk each sub-schema to build an enum-name → namespace map.
    """
    import os
    from linkml_runtime.utils.formatutils import camelcase

    schema_dir = os.path.dirname(schema_path)

    root_view = SchemaView(schema_path, merge_imports=False)

    enum_to_ns: dict[str, str] = {}

    def _walk(imports: list, base_dir: str) -> None:
        for import_name in imports:
            if import_name.startswith("linkml:"):
                continue
            import_path = os.path.join(base_dir, import_name + ".yaml")
            if not os.path.exists(import_path):
                continue
            sub_view = SchemaView(import_path, merge_imports=False)
            dp = sub_view.schema.default_prefix
            if dp and dp in sub_view.schema.prefixes:
                sub_ns = str(sub_view.schema.prefixes[dp].prefix_reference)
                for ename in sub_view.schema.enums:
                    if ename not in enum_to_ns:
                        enum_to_ns[ename] = sub_ns
            _walk(sub_view.schema.imports or [], os.path.dirname(import_path))

    _walk(root_view.schema.imports or [], schema_dir)

    for ename, edef in s.enums.items():
        if edef.enum_uri:
            continue
        ns = enum_to_ns.get(ename)
        if ns is None:
            continue
        edef.enum_uri = f"{ns}{camelcase(ename)}"


def _collect_renames(s: SchemaDefinition, namespace: str, view: SchemaView) -> dict[str, str]:
    renames: dict[str, str] = {}
    for slot_name, slot_def in s.slots.items():
        if not slot_def.slot_uri:
            continue
        try:
            expanded = view.expand_curie(slot_def.slot_uri)
        except Exception:
            continue
        new_name = expanded.split("#")[-1].split("/")[-1]
        in_ns = expanded.startswith(namespace)
        needs_rename = new_name != slot_name
        has_at = slot_name.startswith("@")
        if (in_ns and needs_rename) or has_at:
            renames[slot_name] = new_name
    return renames


def _apply_renames(s: SchemaDefinition, renames: dict[str, str]) -> None:
    for old_name, new_name in renames.items():
        slot_def = s.slots.pop(old_name)
        slot_def.name = new_name
        s.slots[new_name] = slot_def

    for class_def in s.classes.values():
        if class_def.slots:
            class_def.slots = [renames.get(sn, sn) for sn in class_def.slots]
        if class_def.slot_usage:
            to_rename = {k: renames[k] for k in class_def.slot_usage if k in renames}
            for old_key, new_key in to_rename.items():
                v = class_def.slot_usage.pop(old_key)
                v.name = new_key
                class_def.slot_usage[new_key] = v


def _promote_attributes(s: SchemaDefinition, view: SchemaView) -> None:
    """Promote class attributes to top-level slots so gen-owl emits global rdfs:range."""
    for cls_name, cls_def in s.classes.items():
        if not cls_def.attributes:
            continue
        attr_to_slot: dict[str, str] = {}
        for attr_name, attr_def in list(cls_def.attributes.items()):
            if not attr_def.slot_uri:
                continue
            slot_name = _attr_slot_name(attr_name, attr_def, view)
            attr_to_slot[attr_name] = slot_name
            if slot_name not in s.slots or attr_def.slot_uri:
                promoted = copy.deepcopy(attr_def)
                promoted.name = slot_name
                s.slots[slot_name] = promoted
            cls_def.slots = list(cls_def.slots or []) + [slot_name]
        cls_def.attributes = {}
        if cls_def.slot_usage:
            for old_name in attr_to_slot:
                if old_name in cls_def.slot_usage:
                    cls_def.slot_usage.pop(old_name)


def _attr_slot_name(attr_name: str, attr_def: SlotDefinition, view: SchemaView) -> str:
    if not attr_def.slot_uri:
        return attr_name
    try:
        expanded = view.expand_curie(attr_def.slot_uri)
        return expanded.split("#")[-1].split("/")[-1]
    except Exception:
        return attr_name


def _strip_non_local(
    s: SchemaDefinition,
    local_schema_id: str,
    view: SchemaView,
    local_ns: str,
) -> None:
    """Remove top-level slots and enums not originating in this module.

    Classes from imported schemas are kept so gen-owl can resolve ranges.
    The postprocessor filters out non-local class triples by namespace.

    After merge_imports=True, every definition carries from_schema. Keep only
    slots/enums whose from_schema matches the module being processed — unless
    the enum's expanded enum_uri falls in the local namespace (cross-module
    enums like OperationType defined in hypermedia.yaml but with td: URI).
    """
    slots_to_remove = [
        name for name, slot in s.slots.items()
        if slot.from_schema != local_schema_id
    ]
    for name in slots_to_remove:
        del s.slots[name]

    enums_to_remove = []
    for name, enum in s.enums.items():
        if enum.from_schema == local_schema_id:
            continue
        if enum.enum_uri:
            try:
                expanded = view.expand_curie(enum.enum_uri)
                if expanded and str(expanded).startswith(local_ns):
                    continue
            except Exception:
                pass
        enums_to_remove.append(name)
    for name in enums_to_remove:
        del s.enums[name]

    # Remove slot references from classes that point to removed slots
    remaining_slots = set(s.slots)
    for cls_def in s.classes.values():
        if cls_def.slots:
            cls_def.slots = [sn for sn in cls_def.slots if sn in remaining_slots]
        if cls_def.slot_usage:
            dead_keys = [k for k in cls_def.slot_usage if k not in remaining_slots]
            for k in dead_keys:
                del cls_def.slot_usage[k]


def _strip_jsonld_slots(s: SchemaDefinition) -> None:
    """Remove slots that are JSON-LD keywords (alias starts with '@').

    These are serialization artifacts (@context, @type) with no OWL counterpart.
    """
    to_remove = [
        name for name, slot in s.slots.items()
        if (slot.alias or "").startswith("@") or name.startswith("@")
    ]
    for name in to_remove:
        del s.slots[name]

    removed = set(to_remove)
    for cls_def in s.classes.values():
        if cls_def.slots:
            cls_def.slots = [sn for sn in cls_def.slots if sn not in removed]
        if cls_def.slot_usage:
            dead_keys = [k for k in cls_def.slot_usage if k in removed]
            for k in dead_keys:
                del cls_def.slot_usage[k]


def _strip_discriminator_slots(s: SchemaDefinition, view: SchemaView) -> None:
    """Remove slots with no slot_uri whose range is an enum with no enum_uri.

    This pattern identifies JSON type discriminator fields (e.g. scheme: nosec/basic/...).
    They carry no OWL semantics and have no upstream ontology counterpart.
    """
    implicit_enum_names = {
        name for name, edef in s.enums.items() if not edef.enum_uri
    }
    to_remove = [
        name for name, slot in s.slots.items()
        if not slot.slot_uri and slot.range in implicit_enum_names
    ]
    for name in to_remove:
        del s.slots[name]

    removed = set(to_remove)
    for cls_def in s.classes.values():
        if cls_def.slots:
            cls_def.slots = [sn for sn in cls_def.slots if sn not in removed]
        if cls_def.slot_usage:
            dead_keys = [k for k in cls_def.slot_usage if k in removed]
            for k in dead_keys:
                del cls_def.slot_usage[k]


def _strip_no_uri_classes(s: SchemaDefinition, no_uri_classes: set[str]) -> None:
    """Remove classes with no class_uri and refs to them.

    Classes like MultiLanguage are pure JSON-LD serialization artifacts with no
    OWL counterpart. Their attributes must not be promoted. Slots that reference
    them as range get range cleared (gen-owl will emit DatatypeProperty).
    """
    for name in list(no_uri_classes):
        s.classes.pop(name, None)

    for cls_def in s.classes.values():
        if cls_def.is_a in no_uri_classes:
            cls_def.is_a = None
        if cls_def.mixins:
            cls_def.mixins = [m for m in cls_def.mixins if m not in no_uri_classes]

    for slot_def in s.slots.values():
        if slot_def.range in no_uri_classes:
            slot_def.range = None


def _strip_no_uri_original_slots(s: SchemaDefinition, original_no_uri_slots: set[str]) -> None:
    """Remove top-level slots that had no slot_uri in the original (unmerged) schema.

    After renames, slots that previously had slot_uri now have slot_uri=None but
    their name changed (e.g. id→hasVersionInfo). The original no-uri set identifies
    slots that never had an OWL mapping (e.g. 'id'). Strip those.
    """
    to_remove = [name for name in s.slots if name in original_no_uri_slots]
    for name in to_remove:
        del s.slots[name]

    removed = set(to_remove)
    for cls_def in s.classes.values():
        if cls_def.slots:
            cls_def.slots = [sn for sn in cls_def.slots if sn not in removed]
        if cls_def.slot_usage:
            dead_keys = [k for k in cls_def.slot_usage if k in removed]
            for k in dead_keys:
                del cls_def.slot_usage[k]



def _strip_schema_metadata(s: SchemaDefinition) -> None:
    """Remove schema-level metadata before gen-owl sees it.

    The postprocessor's _add_ontology_header reconstructs ontology metadata from
    the unmerged schema view with proper RDF serialization. Stripping here prevents
    gen-owl from emitting duplicates (title), LinkML metamodel predicates
    (pav:createdOn/lastUpdatedOn/version), and broken Python repr strings
    (JsonObj for publisher annotation).
    """
    s.title = None
    s.description = None
    s.created_by = None
    s.contributors = []
    s.license = None
    s.created_on = None
    s.last_updated_on = None
    s.version = None
    s.see_also = []
    s.annotations = {}


def _infer_ranges_from_branches(s: SchemaDefinition) -> None:
    """Set top-level range from union branches when all branches agree.

    gen-owl emits "Guessing type" warnings for slots with no top-level range
    but with any_of/exactly_one_of branches. If all branches share a single range,
    promote it to the top level so gen-owl can determine ObjectProperty vs DatatypeProperty.
    """
    for slot_def in s.slots.values():
        if slot_def.range:
            continue
        branches = list(slot_def.any_of or []) + list(slot_def.exactly_one_of or [])
        if not branches:
            continue
        ranges = {b.range for b in branches if b.range}
        if len(ranges) == 1:
            slot_def.range = next(iter(ranges))


def _clear_slot_restrictions(slot: SlotDefinition) -> None:
    for f in _LIST_CONSTRAINT_FIELDS + _LIST_CONSTRAINT_FIELDS_EXTRA:
        setattr(slot, f, [])
    for f in _SCALAR_CONSTRAINT_FIELDS:
        setattr(slot, f, None)
    slot.required = False
    slot.identifier = False
    slot.key = False
    slot.multivalued = True


def _keep_rdf_annotations(annotations: dict) -> dict:
    """Keep only annotations whose keys are CURIEs (contain ':')."""
    return {k: v for k, v in annotations.items() if ":" in k}


def _clear_constraints(s: SchemaDefinition) -> None:
    for slot_def in s.slots.values():
        _clear_slot_restrictions(slot_def)
        slot_def.annotations = _keep_rdf_annotations(slot_def.annotations or {})
    for class_def in s.classes.values():
        for attr_def in (class_def.attributes or {}).values():
            _clear_slot_restrictions(attr_def)
            attr_def.annotations = _keep_rdf_annotations(attr_def.annotations or {})
        class_def.slot_usage = {}
        class_def.rules = []
        class_def.annotations = _keep_rdf_annotations(class_def.annotations or {})
    for enum_def in s.enums.values():
        enum_def.annotations = _keep_rdf_annotations(enum_def.annotations or {})
    for type_def in s.types.values():
        type_def.pattern = None
        type_def.structured_pattern = None
        type_def.minimum_value = None
        type_def.maximum_value = None

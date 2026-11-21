"""In-memory schema transforms before gen-owl."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, cast

from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.linkml_model.meta import (
    ClassDefinition,
    EnumDefinition,
    Prefix,
    SchemaDefinition,
    SlotDefinition,
)
from linkml_runtime.utils.formatutils import camelcase
from linkml_runtime.utils.schemaview import SchemaView

from ..errors import SchemaError
from ..schema_utils import get_schema as _get_schema
from ..schema_utils import load_schema_view

# Fields gen-owl converts to blank-node owl:Restriction axioms not present in the WoT TD ontology.
_LIST_CONSTRAINT_FIELDS = ("exactly_one_of", "any_of", "all_of", "none_of")
_SCALAR_CONSTRAINT_FIELDS = (
    "minimum_value",
    "maximum_value",
    "minimum_cardinality",
    "maximum_cardinality",
    "exact_cardinality",
    "pattern",
    "structured_pattern",
    "equals_string",
    "equals_number",
)
_LIST_CONSTRAINT_FIELDS_EXTRA = ("equals_string_in", "equals_number_in")

_Slots = dict[str, SlotDefinition]
_Classes = dict[str, ClassDefinition]
_Enums = dict[str, EnumDefinition]
_Prefixes = dict[str, Prefix]


def _remove_slots(s: SchemaDefinition, names: set[str]) -> None:
    """Remove named slots and all class references to them."""
    slots = cast(_Slots, s.slots)
    for name in names:
        slots.pop(name, None)
    for cls_def in cast(_Classes, s.classes).values():
        if cls_def.slots:
            cls_def.slots = [sn for sn in cls_def.slots if str(sn) not in names]
        if cls_def.slot_usage:
            su = cast(dict[str, SlotDefinition], cls_def.slot_usage)
            for k in [k for k in su if k in names]:
                del su[k]


def preprocess_for_gen_owl(schema_path: str) -> str:
    """Return YAML string of schema ready for gen-owl.

    Raises:
        SchemaError: If a CURIE of the schema cannot be expanded because its prefix declarations
            (for example ``default_curi_maps``) cannot be resolved, the schema file or a local import
            does not exist, or the ``default_prefix`` is not declared.
    """
    # Before merging: LinkML's merge would fail on a missing import with an untyped FileNotFoundError.
    enum_namespaces = _collect_enum_namespaces(schema_path)
    view = SchemaView(schema_path, merge_imports=True)
    local_view = SchemaView(schema_path, merge_imports=False)
    local_schema = _get_schema(local_view)
    local_schema_id = local_schema.id
    namespace = _namespace(view)

    local_slots = cast(_Slots, local_schema.slots)
    local_classes = cast(_Classes, local_schema.classes)

    original_no_uri_slots = {name for name, slot in local_slots.items() if not slot.slot_uri}
    no_uri_classes = {name for name, cls in local_classes.items() if not cls.class_uri}

    merged_schema = _get_schema(view)
    s: SchemaDefinition = copy.deepcopy(merged_schema)
    _assign_enum_uris(s, enum_namespaces)
    renames = _collect_renames(s, namespace, view)
    _apply_renames(s, renames)
    _strip_no_uri_classes(s, no_uri_classes)
    _strip_foreign_mixins(s, namespace, view)
    _promote_attributes(s, view)
    _strip_non_local(s, local_schema_id, view, namespace)
    _strip_jsonld_slots(s)
    _strip_no_uri_original_slots(s, original_no_uri_slots)
    _strip_discriminator_slots(s, view)
    _strip_non_ontological_enums(s)
    _fix_enum_pv_labels(s, view)
    _infer_ranges_from_branches(s)
    _clear_constraints(s)
    _strip_dangling_slot_refs(s)
    _strip_schema_metadata(s)
    return yaml_dumper.dumps(s)


def _namespace(view: SchemaView) -> str:
    """Return the namespace URI of the default prefix of the schema of ``view``.

    Raises:
        SchemaError: If the schema has no ``default_prefix`` or it is not declared in ``prefixes``.
    """
    schema = _get_schema(view)
    source = schema.source_file or schema.name
    dp = schema.default_prefix
    if dp is None:
        raise SchemaError(f"{source}: schema has no default_prefix; declare one under 'default_prefix'.")
    prefixes = cast(_Prefixes, schema.prefixes)
    if dp not in prefixes:
        raise SchemaError(f"{source}: default_prefix {dp!r} is not declared in prefixes; declare it under 'prefixes'.")
    return str(cast(Prefix, prefixes[dp]).prefix_reference)


def _expand_curie(view: SchemaView, curie: str, element: str) -> str:
    """Expand ``curie`` with the prefixes of ``view``; ``element`` names its owner for the error message.

    Raises:
        SchemaError: If the prefix declarations of the schema cannot be resolved.
    """
    try:
        return view.expand_curie(curie)
    except ValueError as exc:
        schema = _get_schema(view)
        raise SchemaError(f"{schema.source_file or schema.name}: cannot expand {element}: {exc}") from exc


def _collect_enum_namespaces(schema_path: str) -> dict[str, str]:
    """Map each enum of the local imports of ``schema_path`` to the namespace of its originating sub-schema.

    Raises:
        SchemaError: If ``schema_path`` or a local (non-CURIE) import does not resolve to an existing file.
    """
    root_schema = _get_schema(load_schema_view(Path(schema_path), merge_imports=False))

    enum_to_ns: dict[str, str] = {}
    # Import cycles are legal in LinkML; walk each file once so they do not recurse forever.
    visited: set[Path] = {Path(schema_path).resolve()}

    def _walk(importer: str, imports: list[str], base_dir: Path) -> None:
        for import_name in imports:
            # CURIE imports (e.g. linkml:types) are resolved by LinkML, not from the local directory.
            if ":" in import_name:
                continue
            import_path = base_dir / f"{import_name}.yaml"
            if not import_path.is_file():
                raise SchemaError(f"{importer}: imports {import_name!r} but {import_path} does not exist.")
            if import_path.resolve() in visited:
                continue
            visited.add(import_path.resolve())
            sub_schema = _get_schema(SchemaView(str(import_path), merge_imports=False))
            dp = sub_schema.default_prefix
            prefixes = cast(_Prefixes, sub_schema.prefixes)
            if dp and dp in prefixes:
                sub_ns = str(cast(Prefix, prefixes[dp]).prefix_reference)
                for ename in cast(_Enums, sub_schema.enums):
                    if str(ename) not in enum_to_ns:
                        enum_to_ns[str(ename)] = sub_ns
            sub_imports = cast(list[str], sub_schema.imports or [])
            _walk(str(import_path), sub_imports, import_path.parent)

    root_imports = cast(list[str], root_schema.imports or [])
    _walk(schema_path, root_imports, Path(schema_path).parent)
    return enum_to_ns


def _assign_enum_uris(s: SchemaDefinition, enum_to_ns: dict[str, str]) -> None:
    """Set enum_uri on enums that lack one, using originating sub-schema namespace."""
    for ename, edef in cast(_Enums, s.enums).items():
        if edef.enum_uri:
            continue
        ns = enum_to_ns.get(str(ename))
        if ns is None:
            continue
        edef.enum_uri = f"{ns}{camelcase(str(ename))}"


def _collect_renames(s: SchemaDefinition, namespace: str, view: SchemaView) -> dict[str, str]:
    renames: dict[str, str] = {}
    for slot_name, slot_def in cast(_Slots, s.slots).items():
        if not slot_def.slot_uri:
            continue
        expanded = _expand_curie(view, slot_def.slot_uri, f"slot_uri {slot_def.slot_uri!r} of slot {slot_name!r}")
        new_name = expanded.split("#")[-1].split("/")[-1]
        in_ns = expanded.startswith(namespace)
        needs_rename = new_name != slot_name
        has_at = slot_name.startswith("@")
        if (in_ns and needs_rename) or has_at:
            renames[slot_name] = new_name
    return renames


def _apply_renames(s: SchemaDefinition, renames: dict[str, str]) -> None:
    slots = cast(_Slots, s.slots)
    for old_name, new_name in renames.items():
        slot_def = slots.pop(old_name)
        slot_def.name = new_name
        slots[new_name] = slot_def

    for class_def in cast(_Classes, s.classes).values():
        if class_def.slots:
            class_def.slots = [renames.get(str(sn), str(sn)) for sn in class_def.slots]
        if class_def.slot_usage:
            su = cast(dict[str, SlotDefinition], class_def.slot_usage)
            to_rename = {k: renames[k] for k in su if k in renames}
            for old_key, new_key in to_rename.items():
                v = su.pop(old_key)
                v.name = new_key
                su[new_key] = v


def _promote_attributes(s: SchemaDefinition, view: SchemaView) -> None:
    """Promote class attributes to top-level slots for global rdfs:range.

    Raises:
        SchemaError: If a CURIE cannot be expanded because the schema's prefix declarations cannot be resolved.
    """
    slots = cast(_Slots, s.slots)
    for cls_def in cast(_Classes, s.classes).values():
        if not cls_def.attributes:
            continue
        attr_to_slot: dict[str, str] = {}
        for attr_name, attr_def in list(cast(dict[str, SlotDefinition], cls_def.attributes).items()):
            if not attr_def.slot_uri:
                continue
            slot_name = _attr_slot_name(attr_name, attr_def, view)
            attr_to_slot[attr_name] = slot_name
            if slot_name not in slots or attr_def.slot_uri:
                promoted = copy.deepcopy(attr_def)
                promoted.name = slot_name
                slots[slot_name] = promoted
            cls_def.slots = list(cls_def.slots or []) + [slot_name]
        cls_def.attributes = {}
        if cls_def.slot_usage:
            su = cast(dict[str, SlotDefinition], cls_def.slot_usage)
            for old_name in attr_to_slot:
                if old_name in su:
                    su.pop(old_name)


def _attr_slot_name(attr_name: str, attr_def: SlotDefinition, view: SchemaView) -> str:
    if not attr_def.slot_uri:
        return attr_name
    expanded = _expand_curie(view, attr_def.slot_uri, f"slot_uri {attr_def.slot_uri!r} of attribute {attr_name!r}")
    return expanded.split("#")[-1].split("/")[-1]


def _strip_non_local(
    s: SchemaDefinition,
    local_schema_id: str,
    view: SchemaView,
    local_ns: str,
) -> None:
    """Keep only slots/enums from this module (or with local-namespace enum_uri).

    Raises:
        SchemaError: If a CURIE cannot be expanded because the schema's prefix declarations cannot be resolved.
    """
    slots = cast(_Slots, s.slots)
    foreign_slots = {name for name, slot in slots.items() if slot.from_schema != local_schema_id}
    _remove_slots(s, foreign_slots)

    enums = cast(_Enums, s.enums)
    enums_to_remove: list[str] = []
    for name, enum in enums.items():
        if enum.from_schema == local_schema_id:
            continue
        if enum.enum_uri:
            expanded = _expand_curie(view, enum.enum_uri, f"enum_uri {enum.enum_uri!r} of enum {name!r}")
            if expanded.startswith(local_ns):
                continue
        enums_to_remove.append(name)
    for name in enums_to_remove:
        del enums[name]


def _strip_jsonld_slots(s: SchemaDefinition) -> None:
    """Remove JSON-LD keyword slots (@context, @type) — no OWL counterpart."""
    slots = cast(_Slots, s.slots)
    jsonld_slots = {name for name, slot in slots.items() if (slot.alias or "").startswith("@") or name.startswith("@")}
    _remove_slots(s, jsonld_slots)


def _strip_discriminator_slots(s: SchemaDefinition, view: SchemaView) -> None:
    """Remove JSON discriminator slots (no slot_uri, range is enum without enum_uri)."""
    enums = cast(_Enums, s.enums)
    implicit_enum_names = {name for name, edef in enums.items() if not edef.enum_uri}
    slots = cast(_Slots, s.slots)
    discriminator_slots = {
        name for name, slot in slots.items() if not slot.slot_uri and slot.range in implicit_enum_names
    }
    _remove_slots(s, discriminator_slots)


def _strip_non_ontological_enums(s: SchemaDefinition) -> None:
    """Remove enums without enum_uri or with linkml: enum_uri (type discriminators)."""
    enums = cast(_Enums, s.enums)
    to_remove = [name for name, edef in enums.items() if not edef.enum_uri or str(edef.enum_uri).startswith("linkml:")]
    for name in to_remove:
        del enums[name]

    removed = set(to_remove)
    for slot_def in cast(_Slots, s.slots).values():
        if slot_def.range in removed:
            slot_def.range = "string"


def _fix_enum_pv_labels(s: SchemaDefinition, view: SchemaView) -> None:
    """Rename PV keys to match meaning IRI local name for correct rdfs:label.

    Raises:
        SchemaError: If a CURIE cannot be expanded because the schema's prefix declarations cannot be resolved.
    """
    from linkml_runtime.linkml_model.meta import PermissibleValue

    for ename, edef in cast(_Enums, s.enums).items():
        if not edef.permissible_values:
            continue
        pvs = cast(dict[str, PermissibleValue], edef.permissible_values)
        renames: list[tuple[str, str]] = []
        for key, pv in pvs.items():
            if not pv.meaning:
                continue
            expanded = _expand_curie(view, pv.meaning, f"meaning {pv.meaning!r} of permissible value '{ename}.{key}'")
            local_name = expanded.split("#")[-1].split("/")[-1]
            if local_name and local_name != key:
                renames.append((key, local_name))
        for old_key, new_key in renames:
            pv = pvs.pop(old_key)
            pv.text = new_key
            pvs[new_key] = pv


def _strip_no_uri_classes(s: SchemaDefinition, no_uri_classes: set[str]) -> None:
    """Remove classes without class_uri and clear refs to them."""
    classes = cast(_Classes, s.classes)
    for name in list(no_uri_classes):
        classes.pop(name, None)

    for cls_def in classes.values():
        if cls_def.is_a in no_uri_classes:
            cls_def.is_a = None
        if cls_def.mixins:
            cls_def.mixins = [m for m in cls_def.mixins if str(m) not in no_uri_classes]

    for slot_def in cast(_Slots, s.slots).values():
        if slot_def.range in no_uri_classes:
            slot_def.range = None


def _strip_foreign_mixins(
    s: SchemaDefinition,
    local_ns: str,
    view: SchemaView,
) -> None:
    """Strip mixins whose class_uri resolves to a foreign namespace.

    Raises:
        SchemaError: If a CURIE cannot be expanded because the schema's prefix declarations cannot be resolved.
    """
    classes = cast(_Classes, s.classes)
    for cls_def in classes.values():
        if not cls_def.mixins:
            continue
        keep = []
        for m in cls_def.mixins:
            mixin_cls = classes.get(str(m))
            if mixin_cls and mixin_cls.class_uri:
                expanded = _expand_curie(
                    view, mixin_cls.class_uri, f"class_uri {mixin_cls.class_uri!r} of mixin {str(m)!r}"
                )
                if not expanded.startswith(local_ns):
                    continue
            keep.append(m)
        cls_def.mixins = keep


def _strip_no_uri_original_slots(s: SchemaDefinition, original_no_uri_slots: set[str]) -> None:
    """Remove slots that never had a slot_uri in the unmerged schema."""
    slots = cast(_Slots, s.slots)
    present = {name for name in slots if name in original_no_uri_slots}
    _remove_slots(s, present)


def _strip_schema_metadata(s: SchemaDefinition) -> None:
    """Strip schema metadata — postprocessor reconstructs from unmerged schema."""
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
    """Promote range from union branches when all agree on one range."""
    for slot_def in cast(_Slots, s.slots).values():
        if slot_def.range:
            continue
        branches = list(slot_def.any_of or []) + list(slot_def.exactly_one_of or [])
        if not branches:
            continue
        ranges = {b.range for b in branches if b.range}
        if len(ranges) == 1:
            slot_def.range = next(iter(ranges))


def _strip_dangling_slot_refs(s: SchemaDefinition) -> None:
    """Remove class slot references that have no matching top-level slot definition."""
    existing = set(cast(_Slots, s.slots).keys())
    for cls_def in cast(_Classes, s.classes).values():
        if cls_def.slots:
            cls_def.slots = [sn for sn in cls_def.slots if str(sn) in existing]


def _clear_slot_restrictions(slot: SlotDefinition) -> None:
    for f in _LIST_CONSTRAINT_FIELDS + _LIST_CONSTRAINT_FIELDS_EXTRA:
        setattr(slot, f, [])
    for f in _SCALAR_CONSTRAINT_FIELDS:
        setattr(slot, f, None)
    slot.required = False
    slot.identifier = False
    slot.key = False
    slot.multivalued = True


_Annotations = dict[str, Any]


def _rdf_annotations(obj: SlotDefinition | ClassDefinition | EnumDefinition) -> _Annotations:
    """Return only CURIE-keyed annotations (semantic, not constraint metadata)."""
    anns = cast(_Annotations, obj.annotations or {})
    return {k: v for k, v in anns.items() if ":" in k}


def _clear_constraints(s: SchemaDefinition) -> None:
    for slot_def in cast(_Slots, s.slots).values():
        _clear_slot_restrictions(slot_def)
        slot_def.annotations = _rdf_annotations(slot_def)
    for class_def in cast(_Classes, s.classes).values():
        for attr_def in cast(dict[str, SlotDefinition], class_def.attributes or {}).values():
            _clear_slot_restrictions(attr_def)
            attr_def.annotations = _rdf_annotations(attr_def)
        class_def.slot_usage = {}
        class_def.rules = []
        class_def.annotations = _rdf_annotations(class_def)
    for enum_def in cast(_Enums, s.enums).values():
        enum_def.annotations = _rdf_annotations(enum_def)
    for type_def in s.types.values():
        type_def.pattern = None
        type_def.structured_pattern = None
        type_def.minimum_value = None
        type_def.maximum_value = None

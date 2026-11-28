"""Ordered schema passes applied to the merged LinkML schema before gen-owl."""

import copy
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from typing import Any, cast

from linkml_runtime.linkml_model.meta import (
    ClassDefinition,
    EnumDefinition,
    PermissibleValue,
    Prefix,
    SchemaDefinition,
    SlotDefinition,
)
from linkml_runtime.utils.schemaview import SchemaView

from ..transforms import Transform, TransformKind
from ...errors import SchemaError
from ...schema_utils import is_non_ontological_enum, local_name
from ...schema_utils import get_schema as _get_schema

_Slots = dict[str, SlotDefinition]
_Classes = dict[str, ClassDefinition]
_Enums = dict[str, EnumDefinition]
_Prefixes = dict[str, Prefix]


@dataclass(frozen=True, slots=True)
class OwlPreContext:
    """Facts about the unmodified schema that the passes read while they mutate its copy."""

    view: SchemaView
    namespace: str
    no_uri_classes: AbstractSet[str]
    original_no_uri_slots: AbstractSet[str]


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


def _expand_curie(view: SchemaView, curie: str, element: str) -> str:
    """Expand ``curie`` with the prefixes of ``view``; ``element`` names its owner for the error message."""
    try:
        return cast(str, view.expand_curie(curie))
    except ValueError as exc:
        schema = _get_schema(view)
        raise SchemaError(f"{schema.source_file or schema.name}: cannot expand {element}: {exc}") from exc


def _collect_renames(s: SchemaDefinition, namespace: str, view: SchemaView) -> dict[str, str]:
    renames: dict[str, str] = {}
    for slot_name, slot_def in cast(_Slots, s.slots).items():
        if not slot_def.slot_uri:
            continue
        expanded = _expand_curie(view, slot_def.slot_uri, f"slot_uri {slot_def.slot_uri!r} of slot {slot_name!r}")
        new_name = local_name(expanded)
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
    """Promote class attributes to top-level slots for global rdfs:range."""
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
        cast(dict[str, SlotDefinition], cls_def.attributes).clear()
        if cls_def.slot_usage:
            su = cast(dict[str, SlotDefinition], cls_def.slot_usage)
            for old_name in attr_to_slot:
                if old_name in su:
                    su.pop(old_name)


def _set_fields(slot: SlotDefinition) -> dict[str, Any]:
    """Return the fields of ``slot`` that carry a value."""
    return {field: value for field, value in vars(slot).items() if value not in (None, [], {})}


def _promote_renamed_usages(s: SchemaDefinition, view: SchemaView) -> None:
    """Promote each slot_usage that gives its slot another slot_uri to a top-level slot of its own."""
    slots = cast(_Slots, s.slots)
    for class_name, cls_def in cast(_Classes, s.classes).items():
        usages = cast(dict[str, SlotDefinition], cls_def.slot_usage or {})
        for slot_name, usage in list(usages.items()):
            base = slots.get(slot_name)
            if not usage.slot_uri or (base is not None and usage.slot_uri == base.slot_uri):
                continue
            element = f"slot_uri {usage.slot_uri!r} of slot_usage '{class_name}.{slot_name}'"
            unrelated = {"domain": None, "is_a": None, "subproperty_of": None, "from_schema": cls_def.from_schema}
            fields = (_set_fields(base) if base is not None else {}) | _set_fields(usage) | unrelated
            fields["name"] = local_name(_expand_curie(view, usage.slot_uri, element))
            promoted = SlotDefinition(**copy.deepcopy(fields))
            slots[promoted.name] = promoted
            own = [str(sn) for sn in cls_def.slots or [] if str(sn) != slot_name]
            cls_def.slots = [*own, promoted.name]
            del usages[slot_name]


def _attr_slot_name(attr_name: str, attr_def: SlotDefinition, view: SchemaView) -> str:
    if not attr_def.slot_uri:
        return attr_name
    expanded = _expand_curie(view, attr_def.slot_uri, f"slot_uri {attr_def.slot_uri!r} of attribute {attr_name!r}")
    return local_name(expanded)


def _strip_non_ontological_enums(s: SchemaDefinition) -> None:
    """Remove enums without enum_uri or with linkml: enum_uri (type discriminators)."""
    enums = cast(_Enums, s.enums)
    to_remove = [name for name, edef in enums.items() if is_non_ontological_enum(edef)]
    for name in to_remove:
        del enums[name]

    removed = set(to_remove)
    for slot_def in cast(_Slots, s.slots).values():
        if slot_def.range in removed:
            slot_def.range = "string"


def _fix_enum_pv_labels(s: SchemaDefinition, view: SchemaView) -> None:
    """Rename PV keys to match meaning IRI local name for correct rdfs:label."""
    for ename, edef in cast(_Enums, s.enums).items():
        if not edef.permissible_values:
            continue
        pvs = cast(dict[str, PermissibleValue], edef.permissible_values)
        renames: list[tuple[str, str]] = []
        for key, pv in pvs.items():
            if not pv.meaning:
                continue
            expanded = _expand_curie(view, pv.meaning, f"meaning {pv.meaning!r} of permissible value '{ename}.{key}'")
            pv_name = local_name(expanded)
            if pv_name and pv_name != key:
                renames.append((key, pv_name))
        for old_key, new_key in renames:
            pv = pvs.pop(old_key)
            pv.text = new_key
            pvs[new_key] = pv


def _strip_no_uri_classes(s: SchemaDefinition, no_uri_classes: AbstractSet[str]) -> None:
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
    """Strip mixins whose class_uri resolves to a foreign namespace."""
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


def _strip_no_uri_original_slots(s: SchemaDefinition, original_no_uri_slots: AbstractSet[str]) -> None:
    """Remove slots that never had a slot_uri in the unmerged schema."""
    slots = cast(_Slots, s.slots)
    present = {name for name in slots if name in original_no_uri_slots}
    _remove_slots(s, present)


def _strip_dangling_slot_refs(s: SchemaDefinition) -> None:
    """Remove class slot references that have no matching top-level slot definition."""
    existing = set(cast(_Slots, s.slots).keys())
    for cls_def in cast(_Classes, s.classes).values():
        if cls_def.slots:
            cls_def.slots = [sn for sn in cls_def.slots if str(sn) in existing]


_Annotations = dict[str, Any]


def _keep_rdf_annotations(obj: SlotDefinition | ClassDefinition | EnumDefinition) -> None:
    """Keep only the CURIE-keyed annotations of ``obj`` (semantic, not constraint metadata).

    In place: a dict assigned to a LinkML model field becomes a JsonObj, which the OWL generator cannot read.
    """
    annotations = cast(_Annotations, obj.annotations)
    for key in [key for key in annotations if ":" not in key]:
        del annotations[key]


def _clear_constraints(s: SchemaDefinition) -> None:
    for slot_def in cast(_Slots, s.slots).values():
        _keep_rdf_annotations(slot_def)
    for class_def in cast(_Classes, s.classes).values():
        for attr_def in cast(dict[str, SlotDefinition], class_def.attributes or {}).values():
            _keep_rdf_annotations(attr_def)
        cast(dict[str, SlotDefinition], class_def.slot_usage).clear()
        class_def.rules = []
        class_def.none_of = []
        _keep_rdf_annotations(class_def)
    for enum_def in cast(_Enums, s.enums).values():
        _keep_rdf_annotations(enum_def)
    for type_def in s.types.values():
        type_def.pattern = None
        type_def.structured_pattern = None
        type_def.minimum_value = None
        type_def.maximum_value = None


def _rename_slots(s: SchemaDefinition, context: OwlPreContext) -> None:
    """Rename slots to the local name of their slot_uri."""
    _apply_renames(s, _collect_renames(s, context.namespace, context.view))


OWL_PRE_TRANSFORMS: tuple[Transform, ...] = (
    Transform(
        name="rename_slots_to_uri_local_names",
        kind=TransformKind.WOT_SHAPING,
        reason="Renames slots to the local name of their slot_uri. gen-owl already builds IRIs from slot_uri, so the "
        "only measured effect is on rdfs:label.",
        apply=_rename_slots,
    ),
    Transform(
        name="strip_no_uri_classes",
        kind=TransformKind.WOT_SHAPING,
        reason="Removes classes without class_uri, which have no term in the ontology.",
        apply=lambda s, c: _strip_no_uri_classes(s, c.no_uri_classes),
    ),
    Transform(
        name="strip_foreign_mixins",
        kind=TransformKind.WOT_SHAPING,
        reason="Prevents subClassOf links into another module's classes (e.g. PropertyAffordance to DataSchema).",
        apply=lambda s, c: _strip_foreign_mixins(s, c.namespace, c.view),
    ),
    Transform(
        name="promote_attributes",
        kind=TransformKind.LINKML_GAP,
        reason="gen-owl gives class attributes no global rdfs:range.",
        apply=lambda s, c: _promote_attributes(s, c.view),
    ),
    Transform(
        name="promote_renamed_usages",
        kind=TransformKind.LINKML_GAP,
        reason="gen-owl does not declare the property of a slot_usage that gives its slot another slot_uri "
        "(e.g. jsonschema:properties in ObjectSchema).",
        apply=lambda s, c: _promote_renamed_usages(s, c.view),
    ),
    Transform(
        name="strip_no_uri_original_slots",
        kind=TransformKind.WOT_SHAPING,
        reason="Removes slots without slot_uri.",
        apply=lambda s, c: _strip_no_uri_original_slots(s, c.original_no_uri_slots),
    ),
    Transform(
        name="strip_non_ontological_enums",
        kind=TransformKind.WOT_SHAPING,
        reason="Enums without enum_uri are JSON-Schema-only. Keeping them produced double-# IRIs, which pyoxigraph "
        "rejected.",
        apply=lambda s, c: _strip_non_ontological_enums(s),
    ),
    Transform(
        name="fix_enum_pv_labels",
        kind=TransformKind.WOT_SHAPING,
        reason="Renames permissible-value keys to the local name of their meaning, so the value IRIs and labels "
        "follow the WoT vocabulary.",
        apply=lambda s, c: _fix_enum_pv_labels(s, c.view),
    ),
    Transform(
        name="clear_constraints",
        kind=TransformKind.WOT_SHAPING,
        reason="Prevents blank-node owl:Restriction axioms, which the WoT ontology does not use.",
        apply=lambda s, c: _clear_constraints(s),
    ),
    Transform(
        name="strip_dangling_slot_refs",
        kind=TransformKind.WOT_SHAPING,
        reason="Removes references to slots that earlier passes deleted.",
        apply=lambda s, c: _strip_dangling_slot_refs(s),
    ),
)

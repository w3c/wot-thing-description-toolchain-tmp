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


def _strip_dangling_slot_refs(s: SchemaDefinition) -> None:
    """Remove class slot references that have no matching top-level slot definition."""
    existing = set(cast(_Slots, s.slots).keys())
    for cls_def in cast(_Classes, s.classes).values():
        if cls_def.slots:
            cls_def.slots = [sn for sn in cls_def.slots if str(sn) in existing]


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
        name="strip_dangling_slot_refs",
        kind=TransformKind.WOT_SHAPING,
        reason="Removes references to slots that earlier passes deleted.",
        apply=lambda s, c: _strip_dangling_slot_refs(s),
    ),
)

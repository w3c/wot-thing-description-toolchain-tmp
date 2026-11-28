"""Ordered schema passes applied to the merged LinkML schema before gen-owl."""

from dataclasses import dataclass
from typing import cast

from linkml_runtime.linkml_model.meta import ClassDefinition, SchemaDefinition, SlotDefinition
from linkml_runtime.utils.schemaview import SchemaView

from ..transforms import Transform, TransformKind

_Slots = dict[str, SlotDefinition]
_Classes = dict[str, ClassDefinition]


@dataclass(frozen=True, slots=True)
class OwlPreContext:
    """Facts about the unmodified schema that the passes read while they mutate its copy."""

    view: SchemaView
    namespace: str


def _strip_dangling_slot_refs(s: SchemaDefinition) -> None:
    """Remove class slot references that have no matching top-level slot definition."""
    existing = set(cast(_Slots, s.slots).keys())
    for cls_def in cast(_Classes, s.classes).values():
        if cls_def.slots:
            cls_def.slots = [sn for sn in cls_def.slots if str(sn) in existing]


OWL_PRE_TRANSFORMS: tuple[Transform, ...] = (
    Transform(
        name="strip_dangling_slot_refs",
        kind=TransformKind.WOT_SHAPING,
        reason="Removes class slot references that the merged schema does not define; gen-owl fails on them "
        "(SchemaView.get_type_designator_slot). The module schemas use slots that only the root schema defines.",
        apply=lambda s, c: _strip_dangling_slot_refs(s),
    ),
)

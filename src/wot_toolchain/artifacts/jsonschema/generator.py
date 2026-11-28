"""Upstream linkml JSON Schema generator with the WoT toolchain's fixed arguments."""

import copy
from collections.abc import Iterable
from typing import Self

from linkml.generators.jsonschemagen import JsonSchema, JsonSchemaGenerator, SchemaResult, SlotResult
from linkml_runtime.linkml_model.meta import (
    AnonymousSlotExpression,
    ClassDefinition,
    SchemaDefinition,
    SlotDefinition,
)
from linkml_runtime.utils.schemaview import SchemaView

from .options import JsonSchemaOptions
from ...schema_utils import annotation_tag_value

PREFIX_MEMBERS = "jsonschema_prefix_members"


class WotJsonSchemaGenerator(JsonSchemaGenerator):
    """JSON Schema generator configured as the WoT toolchain publishes it."""

    @classmethod
    def from_options(cls, schema: SchemaDefinition | str, options: JsonSchemaOptions) -> Self:
        """Build a generator for ``schema`` configured by ``options``."""
        return cls(
            schema,
            # Reason not recorded.
            mergeimports=True,
            # Reason not recorded; sets the class-level JsonSchema.PRESERVE_NAMES global upstream.
            preserve_names=True,
            top_class=options.top_class,
            not_closed=options.open,
            include_null=options.include_null,
        )

    def __post_init__(self) -> None:
        """Make the generator's own schema view report no type designator for any class."""
        super().__post_init__()
        # Upstream expands an inlined range to its subclasses when the range class has a designator.
        self.schemaview.get_type_designator_slot = lambda *_args, **_kwargs: None

    def get_subschema_for_slot(
        self,
        slot: SlotDefinition | AnonymousSlotExpression,
        omit_type: bool = False,
        include_null: bool = True,
        cls: ClassDefinition | None = None,
    ) -> JsonSchema:
        """Fix the first items of an array to the slot's jsonschema_prefix_members (docs/known-linkml-gaps.md)."""
        prop = super().get_subschema_for_slot(slot, omit_type, include_null, cls)
        if not omit_type:
            self._restore_branch_type(slot, prop)
        # Upstream removes duplicate branches (string and langString) but leaves the one-item oneOf behind.
        if len(prop.get("oneOf", ())) == 1:
            prop.update(prop.pop("oneOf")[0])
        self._state_exclusive_minimum(prop)
        prefix = annotation_tag_value(slot, PREFIX_MEMBERS)
        if prefix is not None and prop.is_array:
            prop["additionalItems"] = prop["items"]
            prop["items"] = [{"const": value} for value in prefix]
        # Upstream emits nothing for list_elements_unique (docs/known-linkml-gaps.md #13).
        if getattr(slot, "list_elements_unique", False) and prop.is_array:
            prop["uniqueItems"] = True
        return prop

    def aliased_slot_name(self, slot: str | SlotDefinition) -> str:
        """Name a slot condition by the alias of the slot it constrains (docs/known-linkml-gaps.md #14)."""
        name = super().aliased_slot_name(slot)
        if isinstance(slot, str) or slot.alias:
            return name
        constrained = self.schemaview.get_slot(slot.name)
        return constrained.alias if constrained is not None and constrained.alias else name

    @staticmethod
    def _state_exclusive_minimum(prop: JsonSchema) -> None:
        """Write a minimum whose value is also excluded as exclusiveMinimum."""
        # LinkML has no exclusive minimum; schemas state it as minimum_value plus none_of equals_number.
        excluded = prop.get("not", {}).get("anyOf", ())
        if "minimum" in prop and len(excluded) == 1 and excluded[0].get("const") == prop["minimum"]:
            del prop["not"]
            prop["exclusiveMinimum"] = prop.pop("minimum")

    def _restore_branch_type(self, slot: SlotDefinition | AnonymousSlotExpression, prop: JsonSchema) -> None:
        """Give a boolean branch with an explicit range the type upstream drops when it equals default_range."""
        # Upstream cannot tell an explicit branch range from the inherited default, e.g. a none_of string branch.
        if not isinstance(slot, AnonymousSlotExpression) or not slot.range:
            return
        target = prop["items"] if prop.is_array else prop
        if "type" in target or "$ref" in target:
            return
        typ, _fmt, reference = self.get_type_info_for_slot_subschema(slot)
        if typ and reference is None:
            target["type"] = typ

    def after_generate_schema(self, schema: SchemaResult, sv: SchemaView) -> SchemaResult:
        """Drop the LinkML metamodel version, and the version of a schema that has none."""
        schema.schema_.pop("metamodel_version", None)
        if schema.schema_.get("version") is None:
            schema.schema_.pop("version", None)
        return schema

    def before_generate_class_slots(
        self, slot: Iterable[SlotDefinition], cls: ClassDefinition, sv: SchemaView
    ) -> Iterable[SlotDefinition]:
        """Leave out identifier slots: they are map keys, not JSON members."""
        return [candidate for candidate in slot if not candidate.identifier]

    def after_generate_class_slot(self, slot: SlotResult, cls: ClassDefinition, sv: SchemaView) -> SlotResult:
        """Drop the type upstream emits next to the oneOf of a class property."""
        # The top-level type conflicts with exactly_one_of branches of different types.
        if "oneOf" in slot.schema_:
            slot.schema_.pop("type", None)
        return slot

    def before_generate_class_slot(self, slot: SlotDefinition, cls: ClassDefinition, sv: SchemaView) -> SlotDefinition:
        """Hand upstream a copy of a type designator slot without the flag."""
        # Upstream raises ValueError on a designator whose range is an enum; the published schema has no use for it.
        if not slot.designates_type:
            return slot
        plain = copy.copy(slot)
        plain.designates_type = False
        return plain

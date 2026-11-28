"""Upstream linkml JSON Schema generator with the WoT toolchain's fixed arguments."""

import copy
from collections.abc import Iterable
from typing import Any, Self

from linkml.generators.jsonschemagen import ClassResult, JsonSchema, JsonSchemaGenerator, SchemaResult, SlotResult
from linkml_runtime.linkml_model.meta import (
    AnonymousSlotExpression,
    ClassDefinition,
    EnumDefinition,
    SchemaDefinition,
    SlotDefinition,
)
from linkml_runtime.utils.schemaview import SchemaView

from .annotations import ENUM_SUBSET_PARTITION
from .options import JsonSchemaOptions
from .refs import resolve_refs
from ...schema_utils import annotation_tag_value

PREFIX_MEMBERS = "jsonschema_prefix_members"
FLATTEN_SUBCLASSES = "jsonschema_flatten_subclasses"
FORM_SUBSET = "jsonschema_form_subset"
ONEOF_DISPATCH = "jsonschema_oneof_dispatch"


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
        """Drop the LinkML metamodel version, the version of a schema that has none, and each def's own metadata."""
        schema.schema_.pop("metamodel_version", None)
        if schema.schema_.get("version") is None:
            schema.schema_.pop("version", None)
        # Here rather than per class: upstream titles every def when it is added, after the class hook has run.
        for definition in schema.schema_.get("$defs", {}).values():
            definition.pop("description", None)
            definition.pop("title", None)
        return schema

    def before_generate_enums(self, enum: Iterable[EnumDefinition], sv: SchemaView) -> Iterable[EnumDefinition]:
        """Leave out the enum defs: each use of an enum states its values in place."""
        return []

    def after_generate_class(self, cls: ClassResult, sv: SchemaView) -> ClassResult:
        """Resolve the references of a class, then state it as a oneOf when it is a dispatch or partitioned class."""
        cls.schema_ = JsonSchema(resolve_refs(cls.schema_, sv))
        self._state_oneof_dispatch(cls, sv)
        self._state_enum_subset_partition(cls, sv)
        return cls

    def _state_oneof_dispatch(self, cls: ClassResult, sv: SchemaView) -> None:
        """State a dispatch class as a oneOf of its direct subclasses (docs/known-linkml-gaps.md #7)."""
        dispatch = annotation_tag_value(cls.source, ONEOF_DISPATCH)
        if not dispatch:
            return
        subclasses = sorted(name for name, candidate in sv.all_classes().items() if candidate.is_a == cls.source.name)
        branches: list[JsonSchema] = [JsonSchema.ref_for(name) for name in subclasses]
        if dispatch.get("include_unknown", False):
            branches.append(self._unknown_branch(cls, dispatch["discriminator"]))
        cls.schema_ = JsonSchema({"oneOf": branches})

    def _state_enum_subset_partition(self, cls: ClassResult, sv: SchemaView) -> None:
        """State a partitioned class as a oneOf of one variant def per subset of its enum slot."""
        partition = annotation_tag_value(cls.source, ENUM_SUBSET_PARTITION)
        if not partition:
            return
        slot_name, name = partition["slot"], cls.source.name
        properties = dict(cls.schema_.get("properties", {}))
        slot_schema = properties.pop(slot_name, {})
        base_name = f"{name}_element_base"
        base = {
            "type": "object",
            "properties": properties,
            "required": cls.schema_.get("required", []),
            "additionalProperties": cls.schema_.get("additionalProperties", True),
        }
        self.top_level_schema.add_def(base_name, JsonSchema(base))
        constraints = self._array_constraints(slot_schema)
        variants: list[JsonSchema] = []
        for subset, values in self._subset_values(partition["enum"], sv).items():
            array_branch = {"type": "array", "items": {"enum": values}} | constraints
            narrowed = {"oneOf": [{"const": value} for value in values] + [array_branch]}
            narrowing = {"type": "object", "properties": {slot_name: narrowed}}
            variant_name = f"{name}_element_{subset}"
            variant = {"allOf": [{"$ref": f"#/$defs/{base_name}"}, narrowing]}
            self.top_level_schema.add_def(variant_name, JsonSchema(variant))
            variants.append(JsonSchema({"$ref": f"#/$defs/{variant_name}"}))
        cls.schema_ = JsonSchema({"oneOf": variants})

    @staticmethod
    def _subset_values(enum_name: str, sv: SchemaView) -> dict[str, list[str]]:
        """Return the permissible values of an enum by the subsets they are in."""
        subsets: dict[str, list[str]] = {}
        for value_name, value in sv.get_enum(enum_name).permissible_values.items():
            for subset in value.in_subset or []:
                subsets.setdefault(subset, []).append(value_name)
        return subsets

    @staticmethod
    def _array_constraints(slot_schema: dict[str, Any]) -> dict[str, Any]:
        """Return the array keywords (e.g. minItems) of the array form of a slot subschema, without its items."""
        branches = [slot_schema, *slot_schema.get("oneOf", []), *slot_schema.get("anyOf", [])]
        array: dict[str, Any] = next((branch for branch in branches if branch.get("type") == "array"), {})
        return {key: value for key, value in array.items() if key not in ("type", "items")}

    @staticmethod
    def _unknown_branch(cls: ClassResult, discriminator: str) -> JsonSchema:
        """Return the dispatch class itself, for a discriminator value with a prefix."""
        # A prefixed value, so that the catch-all does not overlap the known subclasses.
        unknown = JsonSchema(cls.schema_)
        unknown["description"] = f"Additional {cls.source.name} not covered by known subclasses"
        unknown["properties"] = unknown.get("properties", {}) | {discriminator: {"type": "string", "pattern": ".+:.*"}}
        unknown["required"] = [name for name in unknown.get("required", []) if name != discriminator] + [discriminator]
        return unknown

    def before_generate_class_slots(
        self, slot: Iterable[SlotDefinition], cls: ClassDefinition, sv: SchemaView
    ) -> Iterable[SlotDefinition]:
        """Leave out identifier slots: they are map keys, not JSON members."""
        members = [candidate for candidate in slot if not candidate.identifier]
        return members + self._flattened_subclass_members(cls, members, sv)

    def before_generate_classes(self, cls: Iterable[ClassDefinition], sv: SchemaView) -> Iterable[ClassDefinition]:
        """Leave out the direct subclasses of a flattened class: that class states their members."""
        return [candidate for candidate in cls if not self._flattens_subclasses(candidate.is_a, sv)]

    @staticmethod
    def _flattens_subclasses(class_name: str | None, sv: SchemaView) -> bool:
        """Return whether the class is annotated jsonschema_flatten_subclasses."""
        return class_name is not None and bool(annotation_tag_value(sv.get_class(class_name), FLATTEN_SUBCLASSES))

    def _flattened_subclass_members(
        self, cls: ClassDefinition, members: list[SlotDefinition], sv: SchemaView
    ) -> list[SlotDefinition]:
        """Return the optional members a flattened class, or a class that mixes one in, takes from the subclasses."""
        names = {self.aliased_slot_name(member) for member in members}
        added: list[SlotDefinition] = []
        for parent in (cls.name, *cls.mixins):
            if not self._flattens_subclasses(parent, sv):
                continue
            for subclass in sv.all_classes().values():
                if subclass.is_a != parent:
                    continue
                for member in sv.class_induced_slots(subclass.name):
                    name = self.aliased_slot_name(member)
                    if member.identifier or name in names:
                        continue
                    names.add(name)
                    optional = copy.copy(member)
                    optional.required = False
                    added.append(optional)
        return added

    def after_generate_class_slot(self, slot: SlotResult, cls: ClassDefinition, sv: SchemaView) -> SlotResult:
        """Drop the type upstream emits next to the oneOf of a class property."""
        # The top-level type conflicts with exactly_one_of branches of different types.
        if "oneOf" in slot.schema_:
            slot.schema_.pop("type", None)
        self._narrow_to_subset_variant(slot, cls, sv)
        return slot

    @staticmethod
    def _narrow_to_subset_variant(slot: SlotResult, cls: ClassDefinition, sv: SchemaView) -> None:
        """Narrow the array items of a jsonschema_form_subset slot to its subset variant."""
        subset = annotation_tag_value(slot.source, FORM_SUBSET)
        if not subset or "items" not in slot.schema_:
            return
        for name, partitioned in sv.all_classes().items():
            partition = annotation_tag_value(partitioned, ENUM_SUBSET_PARTITION)
            if not partition:
                continue
            values = sv.get_enum(partition["enum"]).permissible_values.values()
            if not any(subset in (value.in_subset or []) for value in values):
                continue
            # Items of a subclass of the partitioned class keep the subclass next to the variant.
            items, variant = slot.schema_["items"], {"$ref": f"#/$defs/{name}_element_{subset}"}
            slot.schema_["items"] = variant if items == {"$ref": f"#/$defs/{name}"} else {"allOf": [items, variant]}
            return

    def before_generate_class_slot(self, slot: SlotDefinition, cls: ClassDefinition, sv: SchemaView) -> SlotDefinition:
        """Hand upstream a copy of a type designator slot without the flag."""
        # Upstream raises ValueError on a designator whose range is an enum; the published schema has no use for it.
        if not slot.designates_type:
            return slot
        plain = copy.copy(slot)
        plain.designates_type = False
        return plain

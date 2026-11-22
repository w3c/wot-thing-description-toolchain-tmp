"""Upstream linkml JSON Schema generator with the WoT toolchain's fixed arguments."""

import copy
from typing import Self

from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml_runtime.linkml_model.meta import ClassDefinition, SchemaDefinition, SlotDefinition
from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.artifacts.jsonschema.options import JsonSchemaOptions


class WotJsonSchemaGenerator(JsonSchemaGenerator):  # type: ignore[misc]  # linkml ships no type information
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

    def before_generate_class_slot(self, slot: SlotDefinition, cls: ClassDefinition, sv: SchemaView) -> SlotDefinition:
        """Hand upstream a copy of a type designator slot without the flag."""
        # Upstream raises ValueError on a designator whose range is an enum; the published schema has no use for it.
        if not slot.designates_type:
            return slot
        plain = copy.copy(slot)
        plain.designates_type = False
        return plain

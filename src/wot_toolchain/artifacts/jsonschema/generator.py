"""Upstream linkml JSON Schema generator with the WoT toolchain's fixed arguments."""

from typing import Self

from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml_runtime.linkml_model.meta import SchemaDefinition

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

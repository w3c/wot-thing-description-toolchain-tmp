"""Upstream linkml SHACL generator with the WoT toolchain's fixed arguments."""

from typing import Self

from linkml.generators.shaclgen import ShaclGenerator
from linkml_runtime.linkml_model.meta import SchemaDefinition

from wot_toolchain.artifacts.shacl.options import ShaclOptions


class WotShaclGenerator(ShaclGenerator):  # type: ignore[misc]  # linkml ships no type information
    """SHACL generator whose shape IRIs match the published WoT shapes."""

    @classmethod
    def from_options(cls, schema: SchemaDefinition | str, options: ShaclOptions) -> Self:
        """Build a generator for ``schema`` configured by ``options``."""
        return cls(
            schema,
            # Shape IRIs are published as <class IRI>Shape.
            suffix="Shape",
            # Shape IRIs are published as generated without merging imports.
            mergeimports=False,
            closed=not options.open,
            exclude_imports=options.only_root_schema_classes,
        )

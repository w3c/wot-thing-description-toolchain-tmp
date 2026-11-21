"""Upstream linkml OWL generator with the WoT toolchain's fixed arguments."""

from typing import Self

from linkml.generators import owlgen
from linkml.generators.owlgen import OwlSchemaGenerator
from linkml_runtime.linkml_model.meta import SchemaDefinition
from rdflib import OWL, URIRef

from wot_toolchain.artifacts.owl.options import OwlOptions, PermissibleValueKind

_PERMISSIBLE_VALUE_TYPES: dict[PermissibleValueKind, URIRef] = {
    PermissibleValueKind.CLASS: OWL.Class,
    PermissibleValueKind.INDIVIDUAL: OWL.NamedIndividual,
}


class WotOwlGenerator(OwlSchemaGenerator):  # type: ignore[misc]  # linkml ships no type information
    """OWL generator configured as the WoT toolchain runs it."""

    @classmethod
    def from_options(cls, schema: SchemaDefinition | str, options: OwlOptions) -> Self:
        """Build a generator for ``schema`` configured by ``options``."""
        return cls(
            schema,
            # Reason not recorded; True adds OWL shadows of the metamodel classes, i.e. punning (owlgen.py:132).
            metaclasses=False,
            # Reason not recorded; True represents types as classes, so every slot becomes an ObjectProperty.
            type_objects=False,
            # Reason not recorded; False takes IRIs from class_uri / slot_uri instead of definition_uri.
            use_native_uris=False,
            # Reason not recorded; suppresses owl:allValuesFrom restrictions that repeat the global rdfs:range.
            skip_vacuous_local_range_axioms=True,
            # Reason not recorded; suppresses owl:minCardinality 0 restrictions.
            skip_vacuous_min_zero_cardinality_axioms=True,
            # Reason not recorded; keeps separate min/max cardinality restrictions (upstream default made explicit).
            consolidate_cardinality_axioms=False,
            # Reason not recorded; suppresses the owl:unionOf covering axiom of abstract classes over their children.
            skip_abstract_class_as_unionof_subclasses=True,
            metadata_profiles=[owlgen.MetadataProfile(options.metadata_profile.value)],
            mergeimports=not options.only_root_schema,
            default_permissible_value_type=_PERMISSIBLE_VALUE_TYPES[options.permissible_values],
        )

"""Upstream linkml OWL generator with the WoT toolchain's fixed arguments."""

import copy
from dataclasses import dataclass
from typing import Self

from linkml.generators import owlgen
from linkml.generators.owlgen import OwlSchemaGenerator
from linkml_runtime.linkml_model.meta import (
    ClassDefinition,
    Definition,
    EnumDefinition,
    PermissibleValue,
    SchemaDefinition,
)
from rdflib import OWL, RDF, RDFS, SKOS, URIRef

from wot_toolchain.artifacts.owl.options import OwlOptions, PermissibleValueKind
from wot_toolchain.schema_utils import resolve_prefix_namespace

# INSTANCE is emitted by WotOwlGenerator.add_enum, so upstream keeps its default for it.
_PERMISSIBLE_VALUE_TYPES: dict[PermissibleValueKind, URIRef] = {
    PermissibleValueKind.CLASS: OWL.Class,
    PermissibleValueKind.INDIVIDUAL: OWL.NamedIndividual,
    PermissibleValueKind.INSTANCE: OWL.Class,
}

# Annotation predicates whose IRI-looking values name resources, not strings.
_RESOURCE_PREDICATES = frozenset({RDFS.isDefinedBy, RDFS.seeAlso, RDFS.subClassOf})
_IRI_PREFIXES = ("http://", "https://", "urn:")


@dataclass
class WotOwlGenerator(OwlSchemaGenerator):  # type: ignore[misc]  # linkml ships no type information
    """OWL generator configured as the WoT toolchain runs it."""

    permissible_values: PermissibleValueKind = PermissibleValueKind.CLASS

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
            permissible_values=options.permissible_values,
        )

    def add_class(self, cls: ClassDefinition) -> None:
        """Emit ``cls`` without linking its class_uri to its native URI."""
        super().add_class(cls)
        # Upstream adds class_uri skos:exactMatch native URI inline in add_class (owlgen.py:510-516), with no hook.
        mapped_uri = URIRef(self.schemaview.get_uri(cls, expand=True, native=not self.use_native_uris))
        self.graph.remove((self._class_uri(cls.name), SKOS.exactMatch, mapped_uri))

    def add_metadata(self, e: Definition | PermissibleValue, uri: URIRef) -> None:
        """Emit the annotations of ``e`` in the published form.

        Own scheme, alias as label, no exact_mappings, rdfs:isDefinedBy for elements of the schema's own namespace,
        IRI values of resource annotations (rdfs:seeAlso, rdfs:subClassOf, rdfs:isDefinedBy) as IRIs.
        """
        # Upstream maps from_schema to skos:inScheme (owlgen.py:358), so merged imports would name their own schema.
        # Upstream maps exact_mappings to skos:exactMatch, which the published ontologies do not carry.
        # Upstream maps name to rdfs:label and alias to skos:prefLabel; the published label is the alias.
        alias = getattr(e, "alias", None)
        # Upstream emits every CURIE-keyed annotation value as a Literal (owlgen.py:424), with no hook.
        resource_annotations = self._resource_annotations(e)
        if e.from_schema or e.exact_mappings or alias or resource_annotations:
            e = copy.copy(e)
            # Item assignment, as linkml's own normalisation does; attribute assignment wraps a dict in a JsonObj.
            e["annotations"] = {k: v for k, v in e.annotations.items() if k not in resource_annotations}
            e.exact_mappings = []
            if e.from_schema:
                e.from_schema = str(self.graph.identifier)
            if alias:
                e.name, e.alias = alias, None
        super().add_metadata(e, uri)
        for predicate, value in resource_annotations.values():
            self.graph.add((uri, predicate, URIRef(value)))
        # Upstream never emits rdfs:isDefinedBy; elements with a foreign IRI are defined elsewhere.
        if str(uri).startswith(self._own_namespace()):
            self.graph.add((uri, RDFS.isDefinedBy, self.graph.identifier))

    def _resource_annotations(self, e: Definition | PermissibleValue) -> dict[str, tuple[URIRef, str]]:
        """Return the annotations of ``e`` with an IRI value for a resource predicate, keyed by annotation key."""
        found = {}
        for key, annotation in e.annotations.items():
            predicate = URIRef(self.schemaview.expand_curie(key)) if ":" in key else None
            value = annotation.value
            if predicate in _RESOURCE_PREDICATES and isinstance(value, str) and value.startswith(_IRI_PREFIXES):
                found[key] = (predicate, value)
        return found

    def _own_namespace(self) -> str:
        """Return the namespace IRI of the schema's default prefix."""
        return resolve_prefix_namespace(self.schemaview, self.schemaview.schema.default_prefix)

    def add_enum(self, e: EnumDefinition) -> None:
        """Emit ``e``; INSTANCE values are typed by the enum class only."""
        if self.permissible_values is not PermissibleValueKind.INSTANCE:
            super().add_enum(e)
            return
        # Adapted from upstream add_enum (owlgen.py:1157): no value declaration, covering axiom or
        # linkml:permissible_values, which upstream always emits.
        enum_uri = self._enum_uri(e.name)
        self.graph.add((enum_uri, RDF.type, OWL.Class))
        self.add_metadata(e, enum_uri)
        for parent in [e.is_a, *sorted(e.mixins)]:
            if parent:
                self.graph.add((enum_uri, RDFS.subClassOf, self._enum_uri(parent)))
        for pv in e.permissible_values.values():
            if pv.meaning:
                self._add_enum_instance(pv, enum_uri)

    def _add_enum_instance(self, pv: PermissibleValue, enum_uri: URIRef) -> None:
        """Emit ``pv`` as an instance of ``enum_uri``, named by its ``meaning``."""
        pv_uri = URIRef(self.schemaview.expand_curie(pv.meaning))
        self.add_metadata(pv, pv_uri)
        self.graph.add((pv_uri, RDF.type, enum_uri))
        self.graph.add((pv_uri, RDFS.label, self._literal(pv.text, pv)))

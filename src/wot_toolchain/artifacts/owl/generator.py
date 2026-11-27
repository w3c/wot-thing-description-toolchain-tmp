"""Upstream linkml OWL generator with the WoT toolchain's fixed arguments."""

import copy
from dataclasses import dataclass, field
from typing import Self

from linkml.generators import owlgen
from linkml.generators.owlgen import OwlSchemaGenerator
from linkml_runtime.linkml_model.meta import (
    AnonymousClassExpression,
    AnonymousSlotExpression,
    ClassDefinition,
    Definition,
    EnumDefinition,
    PermissibleValue,
    SchemaDefinition,
    SlotDefinition,
    TypeDefinition,
)
from rdflib import OWL, RDF, RDFS, SKOS, XSD, BNode, Graph, Literal, URIRef
from rdflib.collection import Collection

from .header import add_ontology_header
from .options import OwlOptions, PermissibleValueKind
from ...schema_utils import resolve_prefix_namespace

# INSTANCE is emitted by WotOwlGenerator.add_enum, so upstream keeps its default for it.
_PERMISSIBLE_VALUE_TYPES: dict[PermissibleValueKind, URIRef] = {
    PermissibleValueKind.CLASS: OWL.Class,
    PermissibleValueKind.INDIVIDUAL: OWL.NamedIndividual,
    PermissibleValueKind.INSTANCE: OWL.Class,
}

# Annotation predicates whose IRI-looking values name resources, not strings.
_RESOURCE_PREDICATES = frozenset({RDFS.isDefinedBy, RDFS.seeAlso, RDFS.subClassOf})
_IRI_PREFIXES = ("http://", "https://", "urn:")

# Annotation predicates whose text the published ontologies tag with a language.
_LANGUAGE_TAGGED_PREDICATES = frozenset({SKOS.definition, RDFS.comment, RDFS.label})

# Vocabularies whose properties OWL 2 declares itself.
_BUILT_IN_NAMESPACES = (str(RDF), str(RDFS), str(OWL))


def declare_super_properties(graph: Graph) -> None:
    """Declare each undeclared parent of an object or datatype property of ``graph`` with the kind of its child."""
    for kind in (OWL.ObjectProperty, OWL.DatatypeProperty):
        for child in set(graph.subjects(RDF.type, kind)):
            for parent in set(graph.objects(child, RDFS.subPropertyOf)):
                if (parent, RDF.type, None) not in graph:
                    graph.add((parent, RDF.type, kind))


def declare_referenced_classes(graph: Graph) -> None:
    """Declare as owl:Class each named resource that ``graph`` uses as a class without defining it.

    An XSD datatype is never a class, whatever position it stands in.
    """
    object_properties = set(graph.subjects(RDF.type, OWL.ObjectProperty))
    unions = [members for union, members in graph.subject_objects(OWL.unionOf) if (union, RDF.type, OWL.Class) in graph]
    referenced = {
        *graph.objects(None, RDFS.domain),
        *graph.objects(None, RDFS.subClassOf),
        *graph.objects(None, RDF.type),
        *(range_ for property_, range_ in graph.subject_objects(RDFS.range) if property_ in object_properties),
        *(member for members in unions for member in Collection(graph, members)),
    }
    for resource in referenced:
        if isinstance(resource, URIRef) and not str(resource).startswith((*_BUILT_IN_NAMESPACES, str(XSD))):
            graph.add((resource, RDF.type, OWL.Class))


@dataclass
class WotOwlGenerator(OwlSchemaGenerator):
    """OWL generator configured as the WoT toolchain runs it."""

    permissible_values: PermissibleValueKind = PermissibleValueKind.CLASS
    only_root_schema: bool = False
    # Ontology IRI by vocabulary namespace, naming where a term of another vocabulary is defined.
    ontologies: dict[str, URIRef] = field(default_factory=dict)

    @classmethod
    def from_options(
        cls, schema: SchemaDefinition | str, options: OwlOptions, ontologies: dict[str, URIRef] | None = None
    ) -> Self:
        """Build a generator for ``schema`` configured by ``options``; ``ontologies`` maps namespace to ontology IRI."""
        return cls(
            schema,
            ontologies=ontologies or {},
            # Reason not recorded; True adds OWL shadows of the metamodel classes, i.e. punning (owlgen.py:132).
            metaclasses=False,
            # Reason not recorded; True represents types as classes, so every slot becomes an ObjectProperty.
            type_objects=False,
            # Reason not recorded; False takes IRIs from class_uri / slot_uri instead of definition_uri.
            use_native_uris=False,
            # No effect on the output, since classes carry no restrictions; set explicitly to silence the upstream
            # deprecation warnings about their defaults.
            skip_vacuous_local_range_axioms=True,
            skip_vacuous_min_zero_cardinality_axioms=True,
            consolidate_cardinality_axioms=False,
            # Reason not recorded; suppresses the owl:unionOf covering axiom of abstract classes over their children.
            skip_abstract_class_as_unionof_subclasses=True,
            default_permissible_value_type=_PERMISSIBLE_VALUE_TYPES[options.permissible_values],
            permissible_values=options.permissible_values,
            only_root_schema=options.only_root_schema,
            metadata_profiles=[owlgen.MetadataProfile(options.metadata_profile.value)],
            # Published ontologies tag human-readable text @en; the schemas carry no in_language.
            default_language="en",
        )

    def as_graph(self) -> Graph:
        """Build the ontology graph and declare the classes and properties it refers to."""
        graph: Graph = super().as_graph()
        declare_super_properties(graph)
        declare_referenced_classes(graph)
        self._name_defining_ontologies(graph)
        return graph

    def _name_defining_ontologies(self, graph: Graph) -> None:
        """Link each declared term that another vocabulary defines to that vocabulary's ontology."""
        for term in set(graph.subjects(RDF.type, None)):
            if not isinstance(term, URIRef) or (term, RDFS.isDefinedBy, None) in graph:
                continue
            for namespace, ontology in self.ontologies.items():
                if str(term).startswith(namespace) and ontology != graph.identifier:
                    graph.add((term, RDFS.isDefinedBy, ontology))

    def add_class(self, cls: ClassDefinition) -> None:
        """Emit ``cls`` without linking its class_uri to its native URI."""
        if self._is_out_of_scope(self._class_uri(cls.name)):
            return
        super().add_class(cls)
        # Upstream adds class_uri skos:exactMatch native URI inline in add_class (owlgen.py:510-516), with no hook.
        mapped_uri = URIRef(self.schemaview.get_uri(cls, expand=True, native=not self.use_native_uris))
        self.graph.remove((self._class_uri(cls.name), SKOS.exactMatch, mapped_uri))
        self._drop_empty_disjoint_unions(self._class_uri(cls.name))

    def _drop_empty_disjoint_unions(self, class_uri: URIRef) -> None:
        """Remove a disjoint union without operands, which would make the class unsatisfiable."""
        # Upstream emits owl:disjointUnionOf for every exactly_one_of, also when no branch yields a class
        # expression, as for branches made of slot_conditions only.
        for operands in list(self.graph.objects(class_uri, OWL.disjointUnionOf)):
            if (operands, RDF.first, None) not in self.graph:
                self.graph.remove((class_uri, OWL.disjointUnionOf, operands))

    def add_slot(self, slot: SlotDefinition, attribute: bool = False) -> None:
        """Emit ``slot`` unless it is out of scope."""
        uri = self._prop_uri(slot)
        if self._is_out_of_scope(uri):
            return
        super().add_slot(slot, attribute)

    def _type_values_are_nodes(self, type_name: str) -> bool:
        """Treat the values of every type as literals, so a slot of range ``uri`` is a datatype property."""
        return False

    def _add_annotation_property_axioms(self, slot: SlotDefinition, slot_uri: URIRef) -> None:
        """Give an annotation property of a type range that datatype as its range, as for a datatype property."""
        # Upstream decides here by the type itself, not by _type_values_are_nodes, so a ``uri`` range gets no range.
        super()._add_annotation_property_axioms(slot, slot_uri)
        if slot.range in self.schemaview.all_types() and (slot_uri, RDFS.range, None) not in self.graph:
            self.graph.add((slot_uri, RDFS.range, self._range_uri(slot)))

    def add_type(self, typ: TypeDefinition) -> None:
        """Emit ``typ`` unless it is out of scope."""
        if not self._is_out_of_scope(self._type_uri(typ.name)):
            super().add_type(typ)

    def get_own_slots(self, cls: ClassDefinition | AnonymousClassExpression) -> list[SlotDefinition]:
        """Return no slots, so classes carry no slot restrictions; constraints are published as SHACL."""
        # Upstream turns each own slot into owl:Restriction and cardinality axioms inline in
        # transform_class_expression (owlgen.py:703-791), with no hook.
        return []

    def transform_class_slot_expression(
        self,
        cls: ClassDefinition | AnonymousClassExpression | None,
        slot: SlotDefinition | AnonymousSlotExpression,
        main_slot: SlotDefinition | None = None,
        owl_types: set[URIRef] | None = None,
    ) -> URIRef | BNode | None:
        """Return the named range of ``slot`` only; boolean branches and value constraints are published as SHACL."""
        # Upstream intersects the range with branch and datatype-restriction expressions (owlgen.py:857-927).
        named_range = SlotDefinition(name=(main_slot or slot).name, range=slot.range)
        expr: URIRef | BNode | None = super().transform_class_slot_expression(
            cls, named_range, main_slot or named_range, owl_types
        )
        return expr

    def add_metadata(self, e: SchemaDefinition | Definition | PermissibleValue, uri: URIRef) -> None:
        """Emit the annotations of ``e`` in the published form; for the schema itself, the ontology header.

        Own scheme, alias as label, no exact_mappings, rdfs:isDefinedBy for elements of the schema's own namespace,
        IRI values of resource annotations (rdfs:seeAlso, rdfs:subClassOf, rdfs:isDefinedBy) and expandable CURIE
        values of rdfs:subPropertyOf annotations as IRIs.
        """
        # Upstream describes the ontology with the schema's metaslots through this same hook (owlgen.py:344),
        # e.g. pav:version, skos:definition and the schema name as label; the published header differs.
        if isinstance(e, SchemaDefinition):
            add_ontology_header(self.graph, e, uri, self._own_namespace())
            return
        # Upstream maps from_schema to skos:inScheme (owlgen.py:358), so merged imports would name their own schema.
        # Upstream maps exact_mappings to skos:exactMatch, which the published ontologies do not carry.
        # Upstream maps name to rdfs:label and alias to skos:prefLabel; the published label is the alias.
        alias = getattr(e, "alias", None)
        # Upstream emits every CURIE-keyed annotation value as a Literal (owlgen.py:424), with no hook.
        resource_annotations = self._resource_annotations(e)
        if alias or resource_annotations:
            e = copy.copy(e)
            # Item assignment, as linkml's own normalisation does; attribute assignment wraps a dict in a JsonObj.
            e["annotations"] = {k: v for k, v in e.annotations.items() if k not in resource_annotations}
            if alias:
                e.name, e.alias = alias, None
        super().add_metadata(e, uri)
        for predicate, value in resource_annotations.values():
            self.graph.add((uri, predicate, URIRef(value)))
        # Upstream never emits rdfs:isDefinedBy; elements with a foreign IRI are defined elsewhere.
        if str(uri).startswith(self._own_namespace()):
            self.graph.add((uri, RDFS.isDefinedBy, self.graph.identifier))
        self._drop_untagged_predicate_languages(uri)

    def _drop_untagged_predicate_languages(self, uri: URIRef) -> None:
        """Drop the language tag of each literal of ``uri`` outside label, definition and comment."""
        # Upstream tags every string metaslot (owlgen.py:399), e.g. comments as skos:note.
        for predicate, obj in list(self.graph.predicate_objects(uri)):
            if isinstance(obj, Literal) and obj.language and predicate not in _LANGUAGE_TAGGED_PREDICATES:
                self.graph.remove((uri, predicate, obj))
                self.graph.add((uri, predicate, Literal(str(obj))))

    def _resource_annotations(self, e: Definition | PermissibleValue) -> dict[str, tuple[URIRef, str]]:
        """Return the annotations of ``e`` whose value names a resource, as (predicate, IRI) by annotation key."""
        found = {}
        for key, annotation in e.annotations.items():
            if ":" not in key:
                continue
            predicate = URIRef(self.schemaview.expand_curie(key))
            if iri := self._resource_iri(predicate, annotation.value):
                found[key] = (predicate, iri)
        return found

    def _resource_iri(self, predicate: URIRef, value: object) -> str | None:
        """Return the IRI that ``value`` names as an object of ``predicate``, or None if it is a plain string."""
        if not isinstance(value, str):
            return None
        if predicate in _RESOURCE_PREDICATES and value.startswith(_IRI_PREFIXES):
            return value
        if predicate == RDFS.subPropertyOf:
            expanded: str | None = self.schemaview.expand_curie(value)
            return expanded if expanded and expanded != value else None
        return None

    def _own_namespace(self) -> str:
        """Return the namespace IRI of the schema's default prefix."""
        return resolve_prefix_namespace(self.schemaview, self.schemaview.schema.default_prefix)

    def _is_out_of_scope(self, uri: URIRef) -> bool:
        """Return whether ``only_root_schema`` excludes the element named ``uri``."""
        # The modules share terms across namespaces, so a root element named by a foreign IRI is defined elsewhere.
        return self.only_root_schema and not str(uri).startswith(self._own_namespace())

    def add_enum(self, e: EnumDefinition) -> None:
        """Emit ``e``; INSTANCE values are typed by the enum class only."""
        if self._is_out_of_scope(self._enum_uri(e.name)):
            return
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
        if self._is_out_of_scope(pv_uri):
            return
        self.add_metadata(pv, pv_uri)
        self.graph.add((pv_uri, RDF.type, enum_uri))
        self.graph.add((pv_uri, RDFS.label, Literal(pv.text, lang=self._resolve_language(pv))))

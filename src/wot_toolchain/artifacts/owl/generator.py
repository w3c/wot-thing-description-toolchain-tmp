"""Upstream linkml OWL generator with the WoT toolchain's fixed arguments."""

import copy
from dataclasses import dataclass
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

from wot_toolchain.artifacts.owl.header import add_ontology_header
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

# Annotation predicates whose text the published ontologies tag with a language.
_LANGUAGE_TAGGED_PREDICATES = frozenset({SKOS.definition, RDFS.comment, RDFS.label})

# Vocabularies whose properties OWL 2 declares itself.
_BUILT_IN_NAMESPACES = (str(RDF), str(RDFS), str(OWL))


def declare_annotation_properties(graph: Graph) -> None:
    """Declare as owl:AnnotationProperty each predicate of ``graph`` that is neither built in nor a logical property.

    A property that an object or datatype property specialises is logical too: declaring it would pun it.
    """
    typed = {*graph.subjects(RDF.type, OWL.ObjectProperty), *graph.subjects(RDF.type, OWL.DatatypeProperty)}
    logical = typed | {parent for child, parent in graph.subject_objects(RDFS.subPropertyOf) if child in typed}
    for predicate in set(graph.predicates()) - logical:
        if not str(predicate).startswith(_BUILT_IN_NAMESPACES):
            graph.add((predicate, RDF.type, OWL.AnnotationProperty))


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
class WotOwlGenerator(OwlSchemaGenerator):  # type: ignore[misc]  # linkml ships no type information
    """OWL generator configured as the WoT toolchain runs it."""

    permissible_values: PermissibleValueKind = PermissibleValueKind.CLASS
    only_root_schema: bool = False

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
            only_root_schema=options.only_root_schema,
            # Published ontologies tag human-readable text @en; the schemas carry no in_language.
            default_language="en",
        )

    def as_graph(self) -> Graph:
        """Build the ontology graph and declare the classes and properties it refers to."""
        graph: Graph = super().as_graph()
        declare_super_properties(graph)
        declare_referenced_classes(graph)
        declare_annotation_properties(graph)
        return graph

    def add_class(self, cls: ClassDefinition) -> None:
        """Emit ``cls`` without linking its class_uri to its native URI."""
        if self._is_out_of_scope(self._class_uri(cls.name)):
            return
        super().add_class(cls)
        # Upstream adds class_uri skos:exactMatch native URI inline in add_class (owlgen.py:510-516), with no hook.
        mapped_uri = URIRef(self.schemaview.get_uri(cls, expand=True, native=not self.use_native_uris))
        self.graph.remove((self._class_uri(cls.name), SKOS.exactMatch, mapped_uri))

    def add_slot(self, slot: SlotDefinition, attribute: bool = False) -> None:
        """Emit ``slot`` unless it is out of scope; an object property gets no XSD datatype as its range."""
        uri = self._prop_uri(slot)
        if self._is_out_of_scope(uri):
            return
        super().add_slot(slot, attribute)
        # Upstream types a slot from ``implements`` before its range (owlgen.py:1673-1676) and still emits the range.
        if (uri, RDF.type, OWL.ObjectProperty) in self.graph:
            for range_ in list(self.graph.objects(uri, RDFS.range)):
                if str(range_).startswith(str(XSD)):
                    self.graph.remove((uri, RDFS.range, range_))

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
        self._drop_untagged_predicate_languages(uri)

    def _literal(self, value: str, element: Definition | PermissibleValue | None = None) -> Literal:
        """Return ``value`` as a literal without a language tag."""
        # Upstream tags annotation values through _literal (owlgen.py:439); the published ontologies do not.
        return Literal(value)

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

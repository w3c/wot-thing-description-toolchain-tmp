"""Upstream linkml OWL generator with the WoT toolchain's fixed arguments."""

import copy
from dataclasses import dataclass, field
from functools import cached_property
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
from linkml_runtime.utils.schemaview import SchemaView
from rdflib import OWL, RDF, RDFS, SKOS, XSD, BNode, Graph, Literal, URIRef
from rdflib.collection import Collection

from .header import add_ontology_header
from .options import OwlOptions, PermissibleValueKind
from ..rdf_terms import (
    class_valued_properties,
    domain_classes_by_property,
    indexed_classes_by_property,
    language_map_property_iris,
    most_general_classes,
)
from ...errors import SchemaError
from ...schema_utils import is_non_ontological_enum, local_name, resolve_prefix_namespace

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

# The ontology has no LinkML terms.
_LINKML_NAMESPACE = "https://w3id.org/linkml/"

# Vocabularies whose properties OWL 2 declares itself.
_BUILT_IN_NAMESPACES = (str(RDF), str(RDFS), str(OWL))


@dataclass
class WotOwlGenerator(OwlSchemaGenerator):
    """OWL generator configured as the WoT toolchain runs it."""

    permissible_values: PermissibleValueKind = PermissibleValueKind.CLASS
    only_root_schema: bool = False
    # Ontology IRI by vocabulary namespace, naming where a term of another vocabulary is defined.
    ontologies: dict[str, URIRef] = field(default_factory=dict)
    # The schema before OWL preprocessing: it still has the enums, domain_of and JSON-LD annotations.
    source: SchemaView | None = None

    @classmethod
    def from_options(
        cls,
        schema: SchemaDefinition,
        options: OwlOptions,
        ontologies: dict[str, URIRef] | None = None,
        source: SchemaView | None = None,
    ) -> Self:
        """Build a generator for ``schema`` configured by ``options``.

        ``ontologies`` maps namespace to ontology IRI; ``source`` is the schema before OWL preprocessing.
        """
        return cls(
            schema,
            ontologies=ontologies or {},
            source=source,
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
        """Build the ontology graph, then declare the terms it refers to without declaring them."""
        graph: Graph = super().as_graph()
        # Upstream states subclass, range and super-property axioms without a hook for the term they name, so the
        # undeclared ones are read off the finished graph. Nothing is emitted after this step.
        for term, kind in sorted(self._undeclared_references()):
            self._declare(term, kind)
        return graph

    def _undeclared_references(self) -> set[tuple[URIRef, URIRef]]:
        """Return each named term the graph refers to without declaring it, with the kind its use gives it.

        A parent of an object or datatype property is a property of the same kind. A resource in the position of a
        class is a class; an XSD datatype is never one, whatever position it stands in.
        """
        graph = self.graph
        references: set[tuple[URIRef, URIRef]] = set()
        for kind in (OWL.ObjectProperty, OWL.DatatypeProperty):
            for child in graph.subjects(RDF.type, kind):
                for parent in graph.objects(child, RDFS.subPropertyOf):
                    if isinstance(parent, URIRef) and (parent, RDF.type, None) not in graph:
                        references.add((parent, kind))
        object_properties = set(graph.subjects(RDF.type, OWL.ObjectProperty))
        unions = [m for u, m in graph.subject_objects(OWL.unionOf) if (u, RDF.type, OWL.Class) in graph]
        classes = {
            *graph.objects(None, RDFS.domain),
            *graph.objects(None, RDFS.subClassOf),
            *graph.objects(None, RDF.type),
            *(range_ for property_, range_ in graph.subject_objects(RDFS.range) if property_ in object_properties),
            *(member for members in unions for member in Collection(graph, members)),
        }
        for resource in classes:
            if isinstance(resource, URIRef) and not str(resource).startswith((*_BUILT_IN_NAMESPACES, str(XSD))):
                if (resource, RDF.type, OWL.Class) not in graph:
                    references.add((resource, OWL.Class))
        return references

    def _declare(self, term: URIRef, kind: URIRef) -> None:
        """Declare ``term`` as a ``kind``, naming the ontology that defines it."""
        self.graph.add((term, RDF.type, kind))
        self._name_defining_ontology(term)

    def _name_defining_ontology(self, term: URIRef) -> None:
        """Link ``term`` to the ontology of its vocabulary, unless it already names one.

        A term of this vocabulary that this ontology does not describe gets no link.
        """
        if (term, RDFS.isDefinedBy, None) in self.graph:
            return
        for namespace, ontology in self.ontologies.items():
            if str(term).startswith(namespace) and ontology != self.graph.identifier:
                self.graph.add((term, RDFS.isDefinedBy, ontology))

    def add_class(self, cls: ClassDefinition) -> None:
        """Emit ``cls`` without linking its class_uri to its native URI."""
        if self._is_out_of_scope(self._class_uri(cls.name)):
            return
        # Upstream turns rules and none_of into class axioms inline in add_class, with no hook.
        without_constraints = copy.copy(cls)
        without_constraints.rules, without_constraints.none_of = [], []
        super().add_class(without_constraints)
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
        """Emit ``slot`` unless it is out of scope, with every class of its domain."""
        uri = self._prop_uri(slot)
        if self._is_out_of_scope(uri):
            return
        # Upstream emits rdfs:domain from the slot's own domain only, as one named class (owlgen.py:1186).
        without_domain = copy.copy(slot)
        without_domain.domain = None
        # The values of an enum that names no vocabulary term are plain strings.
        if (enum := self.schemaview.get_enum(slot.range)) and is_non_ontological_enum(enum):
            without_domain.range = "string"
        super().add_slot(without_domain, attribute)
        if (uri, RDF.type, None) not in self.graph or (uri, RDFS.domain, None) in self.graph:
            return
        if domain := self._domain_classes(slot, uri):
            self.graph.add((uri, RDFS.domain, self._class_or_union(domain)))

    def _domain_classes(self, slot: SlotDefinition, uri: URIRef) -> list[URIRef]:
        """Return the classes of the domain of ``slot``, sorted.

        They are its declared domain, else the classes that use it, together with the classes whose instances it
        indexes: a property named by ``jsonld_index`` on a slot is stated on the values of that slot.
        """
        declared = {str(self._class_uri(slot.domain))} if slot.domain else self._using_classes.get(str(uri), set())
        indexed = self._indexed_classes.get(str(uri))
        if self.source is None or not indexed or not declared <= self._class_names.keys():
            return sorted(URIRef(iri) for iri in declared)
        general = most_general_classes(self.source, indexed | {self._class_names[iri] for iri in declared})
        return sorted(URIRef(iri) for iri, name in self._class_names.items() if name in general)

    def _class_or_union(self, classes: list[URIRef]) -> URIRef | BNode:
        """Return the single class of ``classes``, or a new owl:unionOf class over all of them."""
        if len(classes) == 1:
            return classes[0]
        union = BNode()
        self.graph.add((union, RDF.type, OWL.Class))
        self.graph.add((union, OWL.unionOf, Collection(self.graph, BNode(), list(classes)).uri))
        return union

    @cached_property
    def _using_classes(self) -> dict[str, set[str]]:
        """Per property IRI, the IRIs of the classes that use it."""
        return domain_classes_by_property(self.source) if self.source else {}

    @cached_property
    def _indexed_classes(self) -> dict[str, set[str]]:
        """Per JSON-LD index property IRI, the names of the classes whose instances it indexes."""
        return indexed_classes_by_property(self.source) if self.source else {}

    @cached_property
    def _class_names(self) -> dict[str, str]:
        """The name of each class of the source schema, by class IRI."""
        if self.source is None:
            return {}
        classes = self.source.all_classes()
        return {self.source.expand_curie(cls.class_uri): name for name, cls in classes.items() if cls.class_uri}

    @cached_property
    def _language_map_properties(self) -> set[str]:
        """The IRIs of the properties serialized as a JSON-LD language map."""
        return language_map_property_iris(self.source) if self.source else set()

    @cached_property
    def _class_values(self) -> dict[str, list[str]]:
        """Per property IRI, the IRIs of the classes that the values of its enum name by ``meaning``."""
        return class_valued_properties(self.source) if self.source else {}

    def slot_owl_type(self, slot: SlotDefinition) -> URIRef:
        """Return the kind of property ``slot`` is in RDF, which its JSON range does not always tell."""
        role: URIRef = super().slot_owl_type(slot)
        # A slot whose enum values each name a class holds that class in RDF, not the JSON string.
        if role == OWL.DatatypeProperty and str(self._prop_uri(slot)) in self._class_values:
            return OWL.ObjectProperty
        # A slot of range Any gets no range, and a property without a range is a datatype property.
        if role == OWL.ObjectProperty and slot.range and str(self._range_uri(slot)).startswith(_LINKML_NAMESPACE):
            return OWL.DatatypeProperty
        return role

    def _rdf_range(self, slot: SlotDefinition) -> URIRef | BNode | None:
        """Return the range ``slot`` has in RDF where it is not its JSON range, else None."""
        uri = str(self._prop_uri(slot))
        role = self.slot_owl_type(slot)
        if role == OWL.ObjectProperty and uri in self._class_values:
            one_of = BNode()
            self.graph.add((one_of, RDF.type, OWL.Class))
            classes = Collection(self.graph, BNode(), [URIRef(iri) for iri in self._class_values[uri]])
            self.graph.add((one_of, OWL.oneOf, classes.uri))
            return one_of
        # The values of a language map are language-tagged strings, not the class that models the map in JSON.
        if role == OWL.DatatypeProperty and uri in self._language_map_properties:
            return RDF.langString
        return None

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
        if self._is_out_of_scope(self._type_uri(typ.name)):
            return
        # Upstream turns the facets of a type into owl:withRestrictions, with no hook.
        without_facets = copy.copy(typ)
        without_facets.pattern = without_facets.structured_pattern = None
        without_facets.minimum_value = without_facets.maximum_value = None
        super().add_type(without_facets)

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
        """Return the named range of ``slot`` only; boolean branches and value constraints are published as SHACL.

        The range of a property itself is its range in RDF, and never a LinkML term.
        """
        if cls is None and isinstance(slot, SlotDefinition) and (rdf_range := self._rdf_range(slot)):
            return rdf_range
        # Upstream intersects the range with branch and datatype-restriction expressions (owlgen.py:857-927).
        named_range = SlotDefinition(name=(main_slot or slot).name, range=slot.range)
        expr: URIRef | BNode | None = super().transform_class_slot_expression(
            cls, named_range, main_slot or named_range, owl_types
        )
        # A slot of range Any gets rdfs:range linkml:Any upstream.
        if cls is None and isinstance(expr, URIRef) and str(expr).startswith(_LINKML_NAMESPACE):
            return None
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
        e = copy.copy(e)
        # Upstream emits an annotation without a prefix as a property of the schema's namespace;
        # such annotations configure the other generators and name no vocabulary term.
        # Item assignment, as linkml's own normalisation does; attribute assignment wraps a dict in a JsonObj.
        e["annotations"] = {k: v for k, v in e.annotations.items() if ":" in k and k not in resource_annotations}
        if alias:
            e.name, e.alias = alias, None
        super().add_metadata(e, uri)
        for predicate, value in resource_annotations.values():
            self.graph.add((uri, predicate, URIRef(value)))
        # Upstream never emits rdfs:isDefinedBy.
        if str(uri).startswith(self._own_namespace()):
            self.graph.add((uri, RDFS.isDefinedBy, self.graph.identifier))
        else:
            self._name_defining_ontology(uri)
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
        if is_non_ontological_enum(e) or self._is_out_of_scope(self._enum_uri(e.name)):
            return
        e = self._named_by_meaning(e)
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

    def _named_by_meaning(self, e: EnumDefinition) -> EnumDefinition:
        """Return a copy of ``e`` whose values that have a ``meaning`` are named by the local name of that IRI."""
        # The JSON value may differ from the term it denotes (``invokeaction`` for ``td:invokeAction``).
        values: dict[str, PermissibleValue] = {}
        for text, pv in e.permissible_values.items():
            if pv.meaning:
                pv = copy.copy(pv)
                pv.text = local_name(self._expand_meaning(pv, e)) or text
            values[pv.text] = pv
        renamed = copy.copy(e)
        # Item assignment, as linkml's own normalisation does; attribute assignment wraps a dict in a JsonObj.
        renamed["permissible_values"] = values
        return renamed

    def _expand_meaning(self, pv: PermissibleValue, e: EnumDefinition) -> str:
        """Return the IRI that ``pv`` of ``e`` denotes."""
        try:
            return str(self.schemaview.expand_curie(pv.meaning))
        except ValueError as exc:
            source = self.schemaview.schema.source_file or self.schemaview.schema.name
            element = f"meaning {pv.meaning!r} of permissible value '{e.name}.{pv.text}'"
            raise SchemaError(f"{source}: cannot expand {element}: {exc}") from exc

    def _add_enum_instance(self, pv: PermissibleValue, enum_uri: URIRef) -> None:
        """Emit ``pv`` as an instance of ``enum_uri``, named by its ``meaning``."""
        pv_uri = URIRef(self.schemaview.expand_curie(pv.meaning))
        if self._is_out_of_scope(pv_uri):
            return
        self.add_metadata(pv, pv_uri)
        self.graph.add((pv_uri, RDF.type, enum_uri))
        self.graph.add((pv_uri, RDFS.label, Literal(pv.text, lang=self._resolve_language(pv))))

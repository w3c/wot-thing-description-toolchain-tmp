"""Custom Turtle serializer matching W3C WoT upstream ontology style."""

from __future__ import annotations

from rdflib import OWL, RDF, RDFS, SKOS, BNode, Graph, Namespace
from rdflib.plugins.serializers.longturtle import LongTurtleSerializer
from rdflib.term import Node

SCHEMA = Namespace("http://schema.org/")
DCTERMS = Namespace("http://purl.org/dc/terms/")
VANN = Namespace("http://purl.org/vocab/vann/")


class WotTurtleSerializer(LongTurtleSerializer):
    """Long-form Turtle serializer, registered as ``wot-turtle``, with WoT ontology predicate and subject order."""

    short_name = "wot-turtle"

    predicateOrder = [
        RDF.type,
        DCTERMS.title,
        RDFS.label,
        RDFS.subClassOf,
        RDFS.subPropertyOf,
        RDFS.comment,
        SKOS.definition,
        VANN.preferredNamespacePrefix,
        VANN.preferredNamespaceUri,
        OWL.versionInfo,
        DCTERMS.license,
        DCTERMS.author,
        DCTERMS.creator,
        DCTERMS.contributor,
        DCTERMS.publisher,
        RDFS.domain,
        SCHEMA.rangeIncludes,
        RDFS.range,
        RDFS.isDefinedBy,
        SKOS.inScheme,
    ]

    topClasses = [OWL.Ontology, OWL.Class, RDFS.Class]

    def __init__(self, store: Graph) -> None:
        """Create a serializer for ``store`` that writes ``rdf:type`` in full instead of ``a``."""
        super().__init__(store)
        self.keywords = {}

    def startDocument(self) -> None:
        """Write the optional ``BASE`` and the namespace declarations as ``@prefix`` lines, sorted by prefix."""
        self._started = True
        ns_list = sorted(self.namespaces.items())
        if self.base:
            self.write(self.indent() + f"BASE <{self.base}>\n")
        for prefix, uri in ns_list:
            self.write(self.indent() + f"@prefix {prefix}: <{uri}> .\n")
        if ns_list and self._spacious:
            self.write("\n")

    def orderSubjects(self) -> list[Node]:
        """Order subjects: ontologies, classes, individuals, other named subjects such as properties, blank nodes.

        Individuals are named subjects with an ``rdf:type`` that is neither a top class nor an OWL property type.
        Every group except the blank nodes is sorted by IRI.
        """
        seen: dict[Node, bool] = {}
        subjects: list[Node] = []

        for class_uri in self.topClasses:
            members = sorted(
                (s for s in self.store.subjects(RDF.type, class_uri) if not isinstance(s, BNode)),
                key=lambda s: str(s),
            )
            for member in members:
                if member not in seen:
                    subjects.append(member)
                    self._topLevels[member] = True
                    seen[member] = True

        individuals = sorted(
            (
                s
                for s in self._subjects
                if s not in seen
                and not isinstance(s, BNode)
                and any(
                    o
                    for o in self.store.objects(s, RDF.type)
                    if o not in {OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty}
                    and o not in set(self.topClasses)
                )
            ),
            key=lambda s: str(s),
        )
        for s in individuals:
            subjects.append(s)
            seen[s] = True

        properties = sorted(
            (s for s in self._subjects if s not in seen and not isinstance(s, BNode)),
            key=lambda s: str(s),
        )
        for s in properties:
            subjects.append(s)
            seen[s] = True

        bnodes = [s for s in self._subjects if s not in seen]
        subjects.extend(bnodes)

        return subjects

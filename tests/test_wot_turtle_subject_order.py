"""WotTurtleSerializer subject order does not depend on which subject the store yields first."""

from io import BytesIO

import pytest
from rdflib import OWL, RDF, RDFS, BNode, Graph, Literal, Namespace
from rdflib.term import Node

from wot_toolchain.serializers.wot_turtle import DCTERMS, SCHEMA, WotTurtleSerializer

EX = Namespace("https://example.org/s#")


def _graph() -> Graph:
    graph = Graph()
    graph.bind("ex", EX)
    publisher = BNode()
    graph.add((EX[""], RDF.type, OWL.Ontology))
    graph.add((EX[""], DCTERMS.publisher, publisher))
    graph.add((publisher, RDF.type, SCHEMA.Organization))
    graph.add((publisher, SCHEMA.name, Literal("Example Org")))
    graph.add((EX.Operation, RDF.type, OWL.Class))
    graph.add((EX.zebra, RDF.type, EX.Operation))
    graph.add((EX.yak, RDF.type, EX.Operation))
    graph.add((EX.hasName, RDF.type, OWL.DatatypeProperty))
    graph.add((EX.hasName, RDFS.domain, EX.Operation))
    return graph


def _first_subject_is(blank_node_first: bool) -> type[WotTurtleSerializer]:
    """Return a serializer whose subject map starts with a blank node, or with a named subject."""

    class Forced(WotTurtleSerializer):
        # The store yields triples in set order, so the first subject is otherwise left to chance.
        def preprocess(self) -> None:
            super().preprocess()
            ordered = sorted(self._subjects, key=lambda s: isinstance(s, BNode) != blank_node_first)
            self._subjects = dict.fromkeys(ordered, True)
            assert isinstance(next(iter(self._subjects)), BNode) is blank_node_first

    return Forced


def _named_order(graph: Graph, blank_node_first: bool) -> list[Node]:
    serializer = _first_subject_is(blank_node_first)(graph)
    serializer.preprocess()
    return [s for s in serializer.orderSubjects() if not isinstance(s, BNode)]


def _turtle(graph: Graph, blank_node_first: bool) -> str:
    stream = BytesIO()
    _first_subject_is(blank_node_first)(graph).serialize(stream)
    return stream.getvalue().decode()


@pytest.mark.parametrize("blank_node_first", [False, True], ids=["named-first", "blank-node-first"])
def test_individuals_precede_properties_whichever_subject_comes_first(blank_node_first: bool) -> None:
    assert _named_order(_graph(), blank_node_first) == [EX[""], EX.Operation, EX.yak, EX.zebra, EX.hasName]


def test_output_is_identical_whichever_subject_comes_first() -> None:
    graph = _graph()

    assert _turtle(graph, blank_node_first=True) == _turtle(graph, blank_node_first=False)

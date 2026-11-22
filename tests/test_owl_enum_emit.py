"""WotOwlGenerator emits the published enum shape itself, before any post pass."""

import warnings

import pytest
from rdflib import OWL, RDF, RDFS, SKOS, Graph, Literal, Namespace, URIRef

from wot_toolchain.artifacts.owl.generator import WotOwlGenerator
from wot_toolchain.artifacts.owl.options import OwlOptions, PermissibleValueKind

EX = Namespace("https://example.org/s#")
LINKML = Namespace("https://w3id.org/linkml/")

SCHEMA = """\
id: https://example.org/s
name: s
default_prefix: ex
prefixes:
  ex: https://example.org/s#
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
enums:
  Color:
    enum_uri: ex:Color
    description: A colour.
    permissible_values:
      Red:
        meaning: ex:Red
        description: The colour red.
      Green:
        meaning: ex:Green
        description: The colour green.
      blue:
        description: A value without meaning has no ontology IRI.
classes:
  Thing:
    class_uri: ex:Thing
"""

VALUES = (EX.Red, EX.Green)


@pytest.fixture(scope="module")
def graph() -> Graph:
    options = OwlOptions(permissible_values=PermissibleValueKind.INSTANCE)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        result: Graph = WotOwlGenerator.from_options(SCHEMA, options).as_graph()
    return result


def test_enum_is_a_class(graph: Graph) -> None:
    assert (EX.Color, RDF.type, OWL.Class) in graph


@pytest.mark.parametrize("value", VALUES)
def test_value_is_typed_by_its_enum_only(graph: Graph, value: URIRef) -> None:
    assert set(graph.objects(value, RDF.type)) == {EX.Color}


@pytest.mark.parametrize("value", VALUES)
def test_value_is_labelled_and_defined(graph: Graph, value: URIRef) -> None:
    assert set(graph.objects(value, RDFS.label)) == {Literal(value.fragment)}
    assert set(graph.objects(value, SKOS.definition)) == {Literal(f"The colour {value.fragment.lower()}.")}


def test_no_upstream_enum_artifacts(graph: Graph) -> None:
    assert not list(graph.triples((None, RDF.type, OWL.NamedIndividual)))
    assert not list(graph.triples((None, RDF.type, SKOS.Concept)))
    assert not list(graph.triples((None, OWL.oneOf, None)))
    assert not list(graph.triples((None, OWL.unionOf, None)))
    assert not list(graph.triples((None, LINKML.permissible_values, None)))
    assert not list(graph.triples((None, RDFS.subClassOf, EX.Color)))


def test_value_without_meaning_is_not_emitted(graph: Graph) -> None:
    assert not [s for s in graph.subjects() if "blue" in str(s)]

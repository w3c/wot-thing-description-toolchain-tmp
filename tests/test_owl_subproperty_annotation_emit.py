"""WotOwlGenerator emits CURIE-valued rdfs:subPropertyOf annotations as IRIs, before any post pass."""

import warnings

import pytest
from rdflib import RDFS, Graph, Literal, URIRef

from wot_toolchain.artifacts.owl.generator import WotOwlGenerator
from wot_toolchain.artifacts.owl.options import OwlOptions

EX = "https://example.org/s#"

# Upstream add_metadata emits every CURIE-keyed annotation value as a Literal.
SCHEMA = """\
id: https://example.org/s
name: s
default_prefix: ex
prefixes:
  ex: https://example.org/s#
  rdfs: http://www.w3.org/2000/01/rdf-schema#
  dcterms: http://purl.org/dc/terms/
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
slots:
  title:
    slot_uri: ex:title
    annotations:
      rdfs:subPropertyOf: dcterms:title
  heading:
    slot_uri: ex:heading
    annotations:
      rdfs:subPropertyOf: unknown:heading
"""


@pytest.fixture(scope="module")
def generator(tmp_path_factory: pytest.TempPathFactory) -> WotOwlGenerator:
    schema_path = tmp_path_factory.mktemp("schemas") / "s.yaml"
    schema_path.write_text(SCHEMA, encoding="utf-8")
    return WotOwlGenerator.from_options(str(schema_path), OwlOptions())


@pytest.fixture(scope="module")
def graph(generator: WotOwlGenerator) -> Graph:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        result: Graph = generator.as_graph()
    return result


def test_sub_property_of_curie_is_emitted_as_iri(graph: Graph) -> None:
    objects = set(graph.objects(URIRef(EX + "title"), RDFS.subPropertyOf))
    assert objects == {URIRef("http://purl.org/dc/terms/title")}


def test_sub_property_of_unexpandable_value_stays_literal(graph: Graph) -> None:
    assert set(graph.objects(URIRef(EX + "heading"), RDFS.subPropertyOf)) == {Literal("unknown:heading")}


def test_schema_annotations_are_left_untouched(graph: Graph, generator: WotOwlGenerator) -> None:
    annotations = generator.schemaview.get_slot("title").annotations
    assert {key: a.value for key, a in annotations.items()} == {"rdfs:subPropertyOf": "dcterms:title"}

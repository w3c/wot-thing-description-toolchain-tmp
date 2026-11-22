"""WotOwlGenerator emits IRI-valued annotations of resource predicates as IRIs, before any post pass."""

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
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
slots:
  version:
    slot_uri: ex:version
    annotations:
      rdfs:seeAlso: http://schema.org/version
  note:
    slot_uri: ex:note
    annotations:
      rdfs:seeAlso: see the version slot
  remark:
    slot_uri: ex:remark
    annotations:
      rdfs:comment: http://schema.org/remark
enums:
  Operation:
    enum_uri: ex:Operation
    annotations:
      rdfs:subClassOf: http://schema.org/Enumeration
    permissible_values:
      read:
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


def test_see_also_iri_is_emitted_as_iri(graph: Graph) -> None:
    assert set(graph.objects(URIRef(EX + "version"), RDFS.seeAlso)) == {URIRef("http://schema.org/version")}


def test_sub_class_of_iri_is_emitted_as_iri(graph: Graph) -> None:
    objects = set(graph.objects(URIRef(EX + "Operation"), RDFS.subClassOf))
    assert URIRef("http://schema.org/Enumeration") in objects
    assert Literal("http://schema.org/Enumeration") not in objects


def test_non_iri_see_also_stays_literal(graph: Graph) -> None:
    assert set(graph.objects(URIRef(EX + "note"), RDFS.seeAlso)) == {Literal("see the version slot")}


def test_iri_under_other_predicate_stays_literal(graph: Graph) -> None:
    assert set(graph.objects(URIRef(EX + "remark"), RDFS.comment)) == {Literal("http://schema.org/remark")}


def test_schema_annotations_are_left_untouched(graph: Graph, generator: WotOwlGenerator) -> None:
    annotations = generator.schemaview.get_slot("version").annotations
    assert {key: a.value for key, a in annotations.items()} == {"rdfs:seeAlso": "http://schema.org/version"}
    enum_annotations = generator.schemaview.get_enum("Operation").annotations
    assert {key: a.value for key, a in enum_annotations.items()} == {"rdfs:subClassOf": "http://schema.org/Enumeration"}

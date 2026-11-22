"""WotOwlGenerator emits no restrictions, cardinalities or anonymous ranges; constraints live in SHACL."""

import warnings

import pytest
from rdflib import OWL, RDF, RDFS, XSD, BNode, Graph, URIRef

from wot_toolchain.artifacts.owl.generator import WotOwlGenerator
from wot_toolchain.artifacts.owl.options import OwlOptions

EX = "https://example.org/s#"

# Upstream turns required, single-valued, branched and bounded slots into owl:Restriction and datatype axioms.
SCHEMA = """\
id: https://example.org/s
name: s
default_prefix: ex
prefixes:
  ex: https://example.org/s#
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
default_range: string
classes:
  Link:
    class_uri: ex:Link
  Form:
    class_uri: ex:Form
    slots:
      - href
      - count
      - target
      - op
      - choice
      - members
    slot_usage:
      count:
        maximum_value: 5
    rules:
      - preconditions:
          slot_conditions:
            href:
              equals_string: a
        postconditions:
          slot_conditions:
            count:
              required: true
slots:
  href:
    slot_uri: ex:href
    range: uri
    required: true
    identifier: true
    pattern: "^h"
  count:
    slot_uri: ex:count
    range: integer
    minimum_value: 0
    maximum_value: 10
    minimum_cardinality: 1
  target:
    slot_uri: ex:target
    range: Link
    key: true
  op:
    slot_uri: ex:op
    range: string
    any_of:
      - equals_string: read
      - equals_string: write
  choice:
    slot_uri: ex:choice
    exactly_one_of:
      - range: Link
      - range: Form
  members:
    slot_uri: ex:members
    range: Link
    multivalued: true
    maximum_cardinality: 3
    has_member:
      range: Link
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


def test_no_restriction_nodes(graph: Graph) -> None:
    assert set(graph.subjects(RDF.type, OWL.Restriction)) == set()


def test_no_anonymous_class_axioms(graph: Graph) -> None:
    axioms = graph.subject_objects(RDFS.subClassOf)
    assert {(s, o) for s, o in axioms if isinstance(s, BNode) or isinstance(o, BNode)} == set()


def test_no_cardinality_or_datatype_restrictions(graph: Graph) -> None:
    predicates = {OWL.minCardinality, OWL.maxCardinality, OWL.cardinality, OWL.withRestrictions, OWL.onProperty}
    assert {p for _, p, _ in graph if p in predicates} == set()


def test_no_functional_properties(graph: Graph) -> None:
    assert set(graph.subjects(RDF.type, OWL.FunctionalProperty)) == set()


def test_class_has_no_local_axioms(graph: Graph) -> None:
    assert set(graph.objects(URIRef(EX + "Form"), RDFS.subClassOf)) == set()


@pytest.mark.parametrize(
    ("slot", "owl_type", "range_"),
    [
        ("href", OWL.DatatypeProperty, XSD.anyURI),
        ("count", OWL.DatatypeProperty, XSD.integer),
        ("target", OWL.ObjectProperty, URIRef(EX + "Link")),
        ("op", OWL.DatatypeProperty, XSD.string),
        ("members", OWL.ObjectProperty, URIRef(EX + "Link")),
    ],
)
def test_property_keeps_type_and_named_range(graph: Graph, slot: str, owl_type: URIRef, range_: URIRef) -> None:
    prop = URIRef(EX + slot)
    assert set(graph.objects(prop, RDF.type)) == {owl_type}
    assert set(graph.objects(prop, RDFS.range)) == {range_}


def test_rangeless_branched_slot_has_no_range(graph: Graph) -> None:
    assert set(graph.objects(URIRef(EX + "choice"), RDFS.range)) == set()


def test_schema_slots_are_left_untouched(generator: WotOwlGenerator) -> None:
    href = generator.schemaview.get_slot("href")
    assert (href.required, href.identifier, href.pattern) == (True, True, "^h")

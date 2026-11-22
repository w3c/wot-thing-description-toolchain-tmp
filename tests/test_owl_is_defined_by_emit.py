"""WotOwlGenerator emits rdfs:isDefinedBy for the elements of its own namespace, before any post pass."""

import warnings

import pytest
from rdflib import RDFS, Graph, URIRef

from wot_toolchain.artifacts.owl.generator import WotOwlGenerator
from wot_toolchain.artifacts.owl.options import OwlOptions, PermissibleValueKind

# Borrowed keeps a foreign class_uri, so it is not defined by this ontology.
SCHEMA = """\
id: https://example.org/s
name: s
default_prefix: ex
prefixes:
  ex: https://example.org/s#
  other: https://example.org/other#
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
classes:
  Thing:
    class_uri: ex:Thing
    slots:
      - colour
  Borrowed:
    class_uri: other:Borrowed
slots:
  colour:
    slot_uri: ex:colour
    range: Colour
enums:
  Colour:
    enum_uri: ex:Colour
    permissible_values:
      red:
        meaning: ex:red
"""

ONTOLOGY = URIRef("https://example.org/s")
LOCAL = [URIRef(f"https://example.org/s#{name}") for name in ("Thing", "colour", "Colour", "red")]
FOREIGN = URIRef("https://example.org/other#Borrowed")


@pytest.fixture(scope="module")
def graph(tmp_path_factory: pytest.TempPathFactory) -> Graph:
    schema_path = tmp_path_factory.mktemp("schemas") / "s.yaml"
    schema_path.write_text(SCHEMA, encoding="utf-8")
    options = OwlOptions(permissible_values=PermissibleValueKind.INSTANCE)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        result: Graph = WotOwlGenerator.from_options(str(schema_path), options).as_graph()
    return result


@pytest.mark.parametrize("subject", LOCAL, ids=str)
def test_local_element_is_defined_by_the_ontology(graph: Graph, subject: URIRef) -> None:
    assert set(graph.objects(subject, RDFS.isDefinedBy)) == {ONTOLOGY}


def test_foreign_element_is_not_defined_by_the_ontology(graph: Graph) -> None:
    assert (FOREIGN, None, None) in graph
    assert set(graph.objects(FOREIGN, RDFS.isDefinedBy)) == set()


def test_ontology_is_not_defined_by_itself(graph: Graph) -> None:
    assert set(graph.objects(ONTOLOGY, RDFS.isDefinedBy)) == set()

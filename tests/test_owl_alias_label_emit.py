"""WotOwlGenerator emits a slot alias as the rdfs:label, before any post pass."""

import warnings

import pytest
from rdflib import RDFS, SKOS, Graph, Literal, URIRef

from wot_toolchain.artifacts.owl.generator import WotOwlGenerator
from wot_toolchain.artifacts.owl.options import OwlOptions

# apikey_in carries an alias, so upstream add_metadata emits the name as rdfs:label and the alias as skos:prefLabel.
SCHEMA = """\
id: https://example.org/s
name: s
default_prefix: ex
prefixes:
  ex: https://example.org/s#
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
classes:
  Scheme:
    class_uri: ex:Scheme
    slots:
      - apikey_in
      - colour
slots:
  apikey_in:
    slot_uri: ex:apikeyIn
    alias: in
    range: string
  colour:
    slot_uri: ex:colour
    range: string
"""

ALIASED = URIRef("https://example.org/s#apikeyIn")
PLAIN = URIRef("https://example.org/s#colour")


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


def test_alias_is_the_only_label(graph: Graph) -> None:
    assert set(graph.objects(ALIASED, RDFS.label)) == {Literal("in", lang="en")}


def test_no_pref_label_is_emitted(graph: Graph) -> None:
    assert set(graph.triples((None, SKOS.prefLabel, None))) == set()


def test_slot_without_alias_keeps_its_name_as_label(graph: Graph) -> None:
    assert set(graph.objects(PLAIN, RDFS.label)) == {Literal("colour", lang="en")}


def test_schema_alias_and_name_are_left_untouched(graph: Graph, generator: WotOwlGenerator) -> None:
    slot = generator.schemaview.get_slot("apikey_in")
    assert (slot.name, slot.alias) == ("apikey_in", "in")

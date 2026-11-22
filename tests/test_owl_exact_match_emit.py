"""WotOwlGenerator emits no skos:exactMatch, before any post pass."""

import warnings

import pytest
from rdflib import SKOS, Graph

from wot_toolchain.artifacts.owl.generator import WotOwlGenerator
from wot_toolchain.artifacts.owl.options import OwlOptions

# Thing's class_uri differs from its native URI, so upstream links the two with skos:exactMatch;
# every exact_mappings value is mapped to skos:exactMatch by upstream add_metadata.
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
    class_uri: other:Thing
    exact_mappings:
      - other:Item
    slots:
      - colour
slots:
  colour:
    slot_uri: ex:colour
    range: Colour
    exact_mappings:
      - other:color
enums:
  Colour:
    enum_uri: ex:Colour
    exact_mappings:
      - other:Colour
    permissible_values:
      red:
        meaning: ex:red
        exact_mappings:
          - other:red
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


def test_no_exact_match_is_emitted(graph: Graph) -> None:
    assert set(graph.triples((None, SKOS.exactMatch, None))) == set()


def test_schema_exact_mappings_are_left_untouched(graph: Graph, generator: WotOwlGenerator) -> None:
    assert generator.schemaview.get_class("Thing").exact_mappings == ["other:Item"]

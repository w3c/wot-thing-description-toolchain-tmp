"""WotOwlGenerator puts every element in the scheme of the ontology it generates, before any post pass."""

import warnings

import pytest
from rdflib import SKOS, Graph, Namespace, URIRef

from wot_toolchain.artifacts.owl.generator import WotOwlGenerator
from wot_toolchain.artifacts.owl.options import OwlOptions

EX = Namespace("https://example.org/s#")
ONTOLOGY = URIRef("https://example.org/s")

IMPORTED_SCHEMA = """\
id: https://example.org/other
name: other
default_prefix: ex
prefixes:
  ex: https://example.org/s#
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
classes:
  Imported:
    class_uri: ex:Imported
"""

SCHEMA = """\
id: https://example.org/s
name: s
default_prefix: ex
prefixes:
  ex: https://example.org/s#
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
  - other
classes:
  Thing:
    class_uri: ex:Thing
"""


@pytest.fixture(scope="module")
def graph(tmp_path_factory: pytest.TempPathFactory) -> Graph:
    schema_dir = tmp_path_factory.mktemp("schemas")
    (schema_dir / "other.yaml").write_text(IMPORTED_SCHEMA, encoding="utf-8")
    schema_path = schema_dir / "s.yaml"
    schema_path.write_text(SCHEMA, encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        result: Graph = WotOwlGenerator.from_options(str(schema_path), OwlOptions()).as_graph()
    return result


@pytest.mark.parametrize("element", [EX.Thing, EX.Imported])
def test_element_is_in_the_ontology_scheme(graph: Graph, element: URIRef) -> None:
    assert set(graph.objects(element, SKOS.inScheme)) == {ONTOLOGY}


def test_no_element_is_in_another_scheme(graph: Graph) -> None:
    assert set(graph.objects(None, SKOS.inScheme)) == {ONTOLOGY}

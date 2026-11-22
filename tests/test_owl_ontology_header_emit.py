"""WotOwlGenerator emits the published owl:Ontology header itself, before any post pass."""

import warnings
from pathlib import Path

import pytest
from rdflib import OWL, RDF, RDFS, BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, VANN

from wot_toolchain.artifacts.owl.generator import WotOwlGenerator
from wot_toolchain.artifacts.owl.options import OwlOptions
from wot_toolchain.errors import SchemaError

SDO = Namespace("http://schema.org/")
ONTOLOGY = URIRef("https://example.org/s")

_BASE = """\
id: https://example.org/s
name: s
default_prefix: ex
prefixes:
  ex: https://example.org/s#
  linkml: https://w3id.org/linkml/
  schema: http://schema.org/
  dcterms: http://purl.org/dc/terms/
imports:
  - linkml:types
classes:
  Thing:
    class_uri: ex:Thing
"""

_METADATA = """\
title: Example Things
description: Schema text that the published header does not carry.
version: "1.2"
license: https://example.org/license
created_by: mailto:author@example.org
contributors:
  - https://example.org/people#a
  - https://example.org/people#b
created_on: "2023-12-05T00:00:00Z"
last_updated_on: "2026-10-16T00:00:00Z"
see_also:
  - https://example.org/spec
annotations:
  dcterms:publisher:
    value:
      "@type": schema:Organization
      schema:name: Example Group
      schema:url: https://example.org/group
"""

_MALFORMED_PUBLISHER = """\
annotations:
  dcterms:publisher: Example Group
"""


def _graph(directory: Path, schema: str) -> Graph:
    schema_path = directory / "s.yaml"
    schema_path.write_text(schema, encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        result: Graph = WotOwlGenerator.from_options(str(schema_path), OwlOptions()).as_graph()
    return result


@pytest.fixture(scope="module")
def graph(tmp_path_factory: pytest.TempPathFactory) -> Graph:
    return _graph(tmp_path_factory.mktemp("schemas"), _BASE + _METADATA)


def test_header_carries_exactly_the_published_triples(graph: Graph) -> None:
    header = {(p, o) for p, o in graph.predicate_objects(ONTOLOGY) if not isinstance(o, BNode)}

    assert header == {
        (RDF.type, OWL.Ontology),
        (DCTERMS.title, Literal("Example Things Ontology", lang="en")),
        (RDFS.label, Literal("Example Things", lang="en")),
        (RDFS.comment, Literal("Ontology for the W3C Web of Things Example Things vocabulary.", lang="en")),
        (VANN.preferredNamespacePrefix, Literal("ex")),
        (VANN.preferredNamespaceUri, Literal("https://example.org/s#")),
        (OWL.versionInfo, Literal("1.2")),
        (DCTERMS.license, URIRef("https://example.org/license")),
        (DCTERMS.creator, URIRef("mailto:author@example.org")),
        (DCTERMS.contributor, URIRef("https://example.org/people#a")),
        (DCTERMS.contributor, URIRef("https://example.org/people#b")),
    }


def test_header_names_the_publisher_organization(graph: Graph) -> None:
    (publisher,) = graph.objects(ONTOLOGY, DCTERMS.publisher)

    assert set(graph.predicate_objects(publisher)) == {
        (RDF.type, SDO.Organization),
        (SDO.name, Literal("Example Group")),
        (SDO.url, URIRef("https://example.org/group")),
    }


def test_schema_without_metadata_gets_the_minimal_header(tmp_path: Path) -> None:
    graph = _graph(tmp_path, _BASE)

    assert set(graph.predicate_objects(ONTOLOGY)) == {
        (RDF.type, OWL.Ontology),
        (VANN.preferredNamespacePrefix, Literal("ex")),
        (VANN.preferredNamespaceUri, Literal("https://example.org/s#")),
    }


def test_malformed_publisher_raises_schema_error(tmp_path: Path) -> None:
    with pytest.raises(SchemaError, match=r"annotation 'dcterms:publisher' "):
        _graph(tmp_path, _BASE + _MALFORMED_PUBLISHER)

"""The OWL postprocessor must report a malformed ``dcterms:publisher`` annotation instead of silently dropping it."""

from __future__ import annotations

import pytest
from linkml_runtime.linkml_model.meta import SchemaDefinition
from linkml_runtime.utils.schemaview import SchemaView
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF

from wot_toolchain.artifacts.owl.header import SCHEMA, _publisher_node
from wot_toolchain.errors import SchemaError

_HEADER = """\
id: https://example.org/s
name: s
default_prefix: ex
prefixes:
  ex: https://example.org/s#
  schema: http://schema.org/
  dcterms: http://purl.org/dc/terms/
"""

_WELL_FORMED = """\
annotations:
  dcterms:publisher:
    value:
      "@type": schema:Organization
      schema:name: Example Group
      schema:url: https://example.org/group
"""

_PLAIN_STRING = """\
annotations:
  dcterms:publisher: Example Group
"""

_MISSING_NAME = """\
annotations:
  dcterms:publisher:
    value:
      "@type": schema:Organization
      schema:url: https://example.org/group
"""

_MISSING_URL = """\
annotations:
  dcterms:publisher:
    value:
      "@type": schema:Organization
      schema:name: Example Group
"""

_MISSING_TYPE = """\
annotations:
  dcterms:publisher:
    value:
      schema:name: Example Group
      schema:url: https://example.org/group
"""

_WRONG_TYPE = """\
annotations:
  dcterms:publisher:
    value:
      "@type": schema:Person
      schema:name: Example Group
      schema:url: https://example.org/group
"""

_EMPTY_URL = """\
annotations:
  dcterms:publisher:
    value:
      "@type": schema:Organization
      schema:name: Example Group
      schema:url: ""
"""


def _schema(body: str) -> SchemaDefinition:
    return SchemaView(_HEADER + body).schema


def test_schema_without_publisher_yields_no_node() -> None:
    g = Graph()

    assert _publisher_node(g, _schema("")) is None
    assert len(g) == 0


def test_well_formed_publisher_yields_organization_node() -> None:
    g = Graph()

    node = _publisher_node(g, _schema(_WELL_FORMED))

    assert set(g.predicate_objects(node)) == {
        (RDF.type, SCHEMA.Organization),
        (SCHEMA.name, Literal("Example Group")),
        (SCHEMA.url, URIRef("https://example.org/group")),
    }


@pytest.mark.parametrize(
    "body",
    [_PLAIN_STRING, _MISSING_NAME, _MISSING_URL, _MISSING_TYPE, _WRONG_TYPE, _EMPTY_URL],
    ids=["plain-string", "missing-name", "missing-url", "missing-type", "wrong-type", "empty-url"],
)
def test_malformed_publisher_raises_schema_error(body: str) -> None:
    g = Graph()

    with pytest.raises(SchemaError, match=r"^s: annotation 'dcterms:publisher' "):
        _publisher_node(g, _schema(body))

    assert len(g) == 0

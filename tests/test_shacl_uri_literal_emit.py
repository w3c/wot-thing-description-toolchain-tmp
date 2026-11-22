"""A URI-valued slot is an IRI node only when it implements owl:ObjectProperty; otherwise an xsd:anyURI literal."""

from pathlib import Path

import pytest
from rdflib import SH, XSD, Graph, Namespace, URIRef

from wot_toolchain.artifacts.shacl.generator import WotShaclGenerator
from wot_toolchain.artifacts.shacl.options import ShaclOptions

EX = Namespace("https://example.org/s#")

_SCHEMA = """\
id: https://example.org/s
name: s
default_prefix: ex
default_range: string
prefixes:
  ex: https://example.org/s#
  linkml: https://w3id.org/linkml/
  owl: http://www.w3.org/2002/07/owl#
imports:
  - linkml:types
slots:
  proxy:
    slot_uri: ex:proxy
    implements: [owl:ObjectProperty]
    range: uri
  homepage:
    slot_uri: ex:homepage
    range: uri
  owner:
    slot_uri: ex:owner
    range: Agent
classes:
  Agent:
    class_uri: ex:Agent
  Thing:
    class_uri: ex:Thing
    slots: [proxy, homepage, owner]
    attributes:
      mirror:
        slot_uri: ex:mirror
        range: uri
"""


@pytest.fixture(scope="module")
def shapes(tmp_path_factory: pytest.TempPathFactory) -> Graph:
    schema_path: Path = tmp_path_factory.mktemp("schemas") / "s.yaml"
    schema_path.write_text(_SCHEMA, encoding="utf-8")
    graph: Graph = WotShaclGenerator.from_options(str(schema_path), ShaclOptions()).as_graph()
    return graph


def _constraints(shapes: Graph, path: URIRef, predicate: URIRef) -> set[object]:
    return {value for shape in shapes.subjects(SH.path, path) for value in shapes.objects(shape, predicate)}


@pytest.mark.parametrize("path", [EX.homepage, EX.mirror])
def test_uri_slot_is_an_any_uri_literal(shapes: Graph, path: URIRef) -> None:
    assert _constraints(shapes, path, SH.nodeKind) == {SH.Literal}
    assert _constraints(shapes, path, SH.datatype) == {XSD.anyURI}


def test_uri_slot_implementing_object_property_is_an_iri(shapes: Graph) -> None:
    assert _constraints(shapes, EX.proxy, SH.nodeKind) == {SH.IRI}
    assert not _constraints(shapes, EX.proxy, SH.datatype)


def test_class_ranged_slot_keeps_its_node_kind(shapes: Graph) -> None:
    assert _constraints(shapes, EX.owner, SH.nodeKind) == {SH.BlankNodeOrIRI}
    assert not _constraints(shapes, EX.owner, SH.datatype)

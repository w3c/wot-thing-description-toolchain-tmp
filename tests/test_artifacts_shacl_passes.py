from pathlib import Path

import pytest
from linkml.generators.shaclgen import ShaclGenerator
from linkml_runtime.utils.schemaview import SchemaView
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.collection import Collection
from rdflib.compare import isomorphic
from rdflib.namespace import RDF, RDFS, SH, XSD

from wot_toolchain.artifacts.passes import PassKind
from wot_toolchain.artifacts.shacl.passes import SHACL_PASSES
from wot_toolchain.artifacts.shacl.postprocess import post_process_shacl

SCHEMA = """\
id: https://example.org/mini
name: mini
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/
default_prefix: ex
default_range: string
imports:
  - linkml:types
slots:
  context:
    alias: "@context"
    slot_uri: ex:atContext
  title:
classes:
  Thing:
    class_uri: ex:Thing
    slots:
      - context
      - title
"""

EX = "https://example.org/"
AT_CONTEXT = URIRef(f"{EX}atContext")
TITLE = URIRef(f"{EX}title")
THING = URIRef(f"{EX}Thing")


@pytest.fixture
def schema_view(tmp_path: Path) -> SchemaView:
    (tmp_path / "mini.yaml").write_text(SCHEMA, encoding="utf-8")
    return SchemaView(str(tmp_path / "mini.yaml"))


def _raw_shacl(schema_view: SchemaView) -> str:
    return ShaclGenerator(schema_view.schema, mergeimports=False, closed=True, suffix="Shape").serialize()


KEYWORD_PASS = "remove_jsonld_keyword_properties"


def test_pass_names_are_unique_and_every_pass_has_a_reason() -> None:
    names = [p.name for p in SHACL_PASSES]
    assert len(names) == len(set(names))
    assert all(p.reason.strip() for p in SHACL_PASSES)


def test_keyword_slot_pass_is_wot_shaping() -> None:
    assert {p.name: p for p in SHACL_PASSES}[KEYWORD_PASS].kind is PassKind.WOT_SHAPING


def test_keyword_slot_property_shape_removed_and_ordinary_one_kept(schema_view: SchemaView) -> None:
    graph = Graph()
    node_shape, keyword_shape, title_shape = URIRef(f"{EX}ThingShape"), BNode(), BNode()
    graph.add((node_shape, SH.targetClass, THING))
    graph.add((node_shape, SH.property, keyword_shape))
    graph.add((keyword_shape, SH.path, AT_CONTEXT))
    graph.add((keyword_shape, SH.maxCount, Literal(1)))
    graph.add((node_shape, SH.property, title_shape))
    graph.add((title_shape, SH.path, TITLE))
    graph.add((title_shape, SH.datatype, XSD.string))

    {p.name: p for p in SHACL_PASSES}[KEYWORD_PASS].apply(graph, schema_view)

    assert (None, SH.path, AT_CONTEXT) not in graph
    assert (keyword_shape, None, None) not in graph
    assert (node_shape, SH.property, keyword_shape) not in graph
    assert (node_shape, SH.property, title_shape) in graph
    assert (title_shape, SH.datatype, XSD.string) in graph


def test_post_process_shacl_drops_keyword_shapes_and_literal_datatypes(schema_view: SchemaView) -> None:
    raw = _raw_shacl(schema_view)
    expected = Graph().parse(data=raw, format="turtle")
    assert (None, SH.path, AT_CONTEXT) in expected
    for property_shape in list(expected.subjects(SH.path, AT_CONTEXT)):
        expected.remove((None, SH.property, property_shape))
        expected.remove((property_shape, None, None))
    expected.remove((None, SH.datatype, RDFS.Literal))

    actual = Graph().parse(data=post_process_shacl(raw, schema_view), format="turtle")

    assert (None, SH.path, TITLE) in actual
    assert isomorphic(actual, expected)


LITERAL_DATATYPE_PASS = "remove_literal_datatype"


def test_literal_datatype_pass_is_upstream_gap_and_runs_after_keyword_pass() -> None:
    names = [p.name for p in SHACL_PASSES]
    assert {p.name: p for p in SHACL_PASSES}[LITERAL_DATATYPE_PASS].kind is PassKind.UPSTREAM_GAP
    # Order kept from post_process_shacl before the move; the two passes touch disjoint triples.
    assert names.index(KEYWORD_PASS) < names.index(LITERAL_DATATYPE_PASS)


def test_literal_datatype_removed_and_concrete_datatype_kept(schema_view: SchemaView) -> None:
    graph = Graph()
    literal_shape, title_shape = BNode(), BNode()
    graph.add((literal_shape, SH.datatype, RDFS.Literal))
    graph.add((literal_shape, SH.nodeKind, SH.Literal))
    graph.add((title_shape, SH.datatype, XSD.string))

    {p.name: p for p in SHACL_PASSES}[LITERAL_DATATYPE_PASS].apply(graph, schema_view)

    assert (None, SH.datatype, RDFS.Literal) not in graph
    assert (literal_shape, SH.nodeKind, SH.Literal) in graph
    assert (title_shape, SH.datatype, XSD.string) in graph


LANGSTRING_PASS = "rewrite_langstring_union_to_sh_or"

LANGSTRING_SCHEMA = """\
id: https://example.org/mini
name: mini
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/
  rdf: http://www.w3.org/1999/02/22-rdf-syntax-ns#
default_prefix: ex
default_range: string
imports:
  - linkml:types
types:
  langString:
    uri: rdf:langString
    base: str
slots:
  label:
    slot_uri: ex:label
  title:
    slot_uri: ex:title
classes:
  Thing:
    class_uri: ex:Thing
    slots: [label, title]
    slot_usage:
      title:
        exactly_one_of:
          - range: string
          - range: langString
"""


@pytest.fixture
def langstring_schema_view(tmp_path: Path) -> SchemaView:
    (tmp_path / "langstring.yaml").write_text(LANGSTRING_SCHEMA, encoding="utf-8")
    return SchemaView(str(tmp_path / "langstring.yaml"))


def test_langstring_pass_is_upstream_gap_and_last_in_todays_order() -> None:
    assert {p.name: p for p in SHACL_PASSES}[LANGSTRING_PASS].kind is PassKind.UPSTREAM_GAP
    # Order only preserves post_process_shacl before the move; on TD output the passes touch disjoint shapes.
    assert [p.name for p in SHACL_PASSES] == [KEYWORD_PASS, LITERAL_DATATYPE_PASS, LANGSTRING_PASS]


def test_langstring_union_rewritten_to_sh_or_and_unrelated_shape_kept(langstring_schema_view: SchemaView) -> None:
    graph = Graph()
    node_shape, title_shape, label_shape = URIRef(f"{EX}ThingShape"), BNode(), BNode()
    graph.add((node_shape, SH.targetClass, THING))
    graph.add((node_shape, SH.property, title_shape))
    graph.add((title_shape, SH.path, TITLE))
    graph.add((title_shape, SH.datatype, XSD.string))
    graph.add((node_shape, SH.property, label_shape))
    graph.add((label_shape, SH.path, URIRef(f"{EX}label")))
    graph.add((label_shape, SH.datatype, XSD.string))

    {p.name: p for p in SHACL_PASSES}[LANGSTRING_PASS].apply(graph, langstring_schema_view)

    assert (title_shape, SH.datatype, None) not in graph
    union = graph.value(title_shape, SH["or"])
    assert union is not None
    branches = list(Collection(graph, union))
    assert [graph.value(branch, SH.datatype) for branch in branches] == [XSD.string, RDF.langString]
    assert set(graph.predicate_objects(label_shape)) == {(SH.path, URIRef(f"{EX}label")), (SH.datatype, XSD.string)}

from pathlib import Path

import pytest
from linkml_runtime.utils.schemaview import SchemaView
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD

from wot_toolchain.artifacts.owl.passes import OWL_PASSES
from wot_toolchain.artifacts.owl.postprocess import postprocess_owl_graph
from wot_toolchain.artifacts.passes import Pass, PassKind

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
  title:
    slot_uri: ex:title
  href:
    slot_uri: ex:href
classes:
  Thing:
    class_uri: ex:Thing
    slots: [title, href]
  Form:
    class_uri: ex:Form
    slots: [title]
"""

EX = Namespace("https://example.org/")
LINKML = Namespace("https://w3id.org/linkml/")
SDO = Namespace("http://schema.org/")

LINKML_RANGE_PASS = "strip_linkml_ranges"
DOMAIN_INCLUDES_PASS = "add_domain_includes"


@pytest.fixture
def schema_view(tmp_path: Path) -> SchemaView:
    (tmp_path / "mini.yaml").write_text(SCHEMA, encoding="utf-8")
    return SchemaView(str(tmp_path / "mini.yaml"))


def _pass(name: str) -> Pass:
    return {p.name: p for p in OWL_PASSES}[name]


def test_pass_names_are_unique_and_every_pass_has_a_reason() -> None:
    names = [p.name for p in OWL_PASSES]
    assert len(names) == len(set(names))
    assert all(p.reason.strip() for p in OWL_PASSES)


def test_pass_order_is_the_order_of_postprocess_owl_graph_before_the_move() -> None:
    assert [p.name for p in OWL_PASSES] == [LINKML_RANGE_PASS, DOMAIN_INCLUDES_PASS]


def test_linkml_range_pass_is_wot_shaping_and_domain_includes_pass_is_upstream_gap() -> None:
    assert _pass(LINKML_RANGE_PASS).kind is PassKind.WOT_SHAPING
    assert _pass(DOMAIN_INCLUDES_PASS).kind is PassKind.UPSTREAM_GAP


def test_linkml_range_removed_and_other_range_kept(schema_view: SchemaView) -> None:
    graph = Graph()
    graph.add((EX.const, RDF.type, OWL.DatatypeProperty))
    graph.add((EX.const, RDFS.range, LINKML.Any))
    graph.add((EX.title, RDF.type, OWL.DatatypeProperty))
    graph.add((EX.title, RDFS.range, XSD.string))

    _pass(LINKML_RANGE_PASS).apply(graph, schema_view)

    assert (None, RDFS.range, LINKML.Any) not in graph
    assert (EX.const, RDF.type, OWL.DatatypeProperty) in graph
    assert (EX.title, RDFS.range, XSD.string) in graph


def test_object_property_left_without_range_is_demoted_to_datatype_property(schema_view: SchemaView) -> None:
    graph = Graph()
    graph.add((EX.lone, RDF.type, OWL.ObjectProperty))
    graph.add((EX.lone, RDFS.range, LINKML.Any))
    graph.add((EX.mixed, RDF.type, OWL.ObjectProperty))
    graph.add((EX.mixed, RDFS.range, LINKML.Any))
    graph.add((EX.mixed, RDFS.range, EX.Thing))
    graph.add((EX.unranged, RDF.type, OWL.ObjectProperty))

    _pass(LINKML_RANGE_PASS).apply(graph, schema_view)

    assert set(graph.objects(EX.lone, RDF.type)) == {OWL.DatatypeProperty}
    assert set(graph.objects(EX.mixed, RDF.type)) == {OWL.ObjectProperty}
    assert set(graph.objects(EX.mixed, RDFS.range)) == {EX.Thing}
    assert set(graph.objects(EX.unranged, RDF.type)) == {OWL.ObjectProperty}


def test_domain_includes_added_only_for_a_property_of_several_classes(schema_view: SchemaView) -> None:
    graph = Graph()
    graph.add((EX.title, RDF.type, OWL.DatatypeProperty))
    graph.add((EX.href, RDF.type, OWL.DatatypeProperty))

    _pass(DOMAIN_INCLUDES_PASS).apply(graph, schema_view)

    assert set(graph.objects(EX.title, SDO.domainIncludes)) == {EX.Thing, EX.Form}
    assert (EX.href, SDO.domainIncludes, None) not in graph


def test_domain_includes_not_added_for_a_property_absent_from_the_graph(schema_view: SchemaView) -> None:
    graph = Graph()

    _pass(DOMAIN_INCLUDES_PASS).apply(graph, schema_view)

    assert len(graph) == 0


def test_postprocess_owl_graph_runs_the_passes_and_writes_the_module_file(
    schema_view: SchemaView, tmp_path: Path
) -> None:
    graph = Graph()
    graph.add((EX.title, RDF.type, OWL.DatatypeProperty))
    graph.add((EX.title, RDFS.range, LINKML.Any))

    postprocess_owl_graph(graph, "mini.yaml", "mini.ttl", tmp_path, tmp_path / "out", sv_merged=schema_view)

    written = Graph().parse(tmp_path / "out" / "mini.ttl", format="turtle")
    assert (None, RDFS.range, LINKML.Any) not in written
    assert set(written.objects(URIRef(EX.title), SDO.domainIncludes)) == {EX.Thing, EX.Form}

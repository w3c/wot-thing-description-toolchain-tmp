"""An owl:ObjectProperty never has an XSD datatype as its rdfs:range."""

import warnings
from pathlib import Path

import pytest
from rdflib import OWL, RDF, RDFS, XSD, Graph, Namespace, URIRef

from wot_toolchain import pipeline
from wot_toolchain.artifacts.owl.generator import WotOwlGenerator
from wot_toolchain.artifacts.owl.options import OwlOptions
from wot_toolchain.config import load_project
from wot_toolchain.schema_utils import load_schema_view

CONFIG = Path(__file__).resolve().parent.parent / "wot-toolchain.yaml"
MODULES = ("hctl", "jsonschema", "td", "tm", "wotsec")

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
  names:
    slot_uri: ex:names
    implements: [owl:ObjectProperty]
    range: string
    multivalued: true
  owner:
    slot_uri: ex:owner
    range: Agent
  homepage:
    slot_uri: ex:homepage
    range: uri
classes:
  Agent:
    class_uri: ex:Agent
  Thing:
    class_uri: ex:Thing
    slots: [proxy, names, owner, homepage]
"""


def _object_properties_with_xsd_range(graph: Graph) -> set[URIRef]:
    return {
        property_
        for property_, range_ in graph.subject_objects(RDFS.range)
        if (property_, RDF.type, OWL.ObjectProperty) in graph and str(range_).startswith(str(XSD))
    }


@pytest.fixture(scope="module")
def example(tmp_path_factory: pytest.TempPathFactory) -> Graph:
    schema_path = tmp_path_factory.mktemp("schemas") / "s.yaml"
    schema_path.write_text(_SCHEMA, encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        graph: Graph = WotOwlGenerator.from_options(str(schema_path), OwlOptions()).as_graph()
    return graph


@pytest.fixture(scope="module")
def generated(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Graph]:
    output_dir = tmp_path_factory.mktemp("owl")
    project = load_project(CONFIG)
    pipeline._gen_owl(project, load_schema_view(project.root_schema, merge_imports=True), output_dir)
    return {path.stem: Graph().parse(path, format="turtle") for path in output_dir.glob("*.ttl")}


@pytest.mark.parametrize("slot", [EX.proxy, EX.names])
def test_object_property_with_a_literal_range_has_no_range(example: Graph, slot: URIRef) -> None:
    assert set(example.objects(slot, RDF.type)) == {OWL.ObjectProperty}
    assert not set(example.objects(slot, RDFS.range))


def test_object_property_keeps_its_class_range(example: Graph) -> None:
    assert set(example.objects(EX.owner, RDFS.range)) == {EX.Agent}


def test_datatype_property_keeps_its_xsd_range(example: Graph) -> None:
    assert set(example.objects(EX.homepage, RDF.type)) == {OWL.DatatypeProperty}
    assert set(example.objects(EX.homepage, RDFS.range)) == {XSD.anyURI}


@pytest.mark.parametrize("module", MODULES)
def test_module_has_no_object_property_with_an_xsd_range(generated: dict[str, Graph], module: str) -> None:
    assert not _object_properties_with_xsd_range(generated[module])

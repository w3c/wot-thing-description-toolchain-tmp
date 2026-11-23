"""Every predicate a generated ontology uses as an annotation is declared an owl:AnnotationProperty."""

import warnings
from pathlib import Path

import pytest
from rdflib import OWL, RDF, RDFS, SKOS, Graph, Namespace, URIRef
from rdflib.namespace import DCTERMS, VANN

from wot_toolchain import pipeline
from wot_toolchain.artifacts.owl.generator import WotOwlGenerator
from wot_toolchain.artifacts.owl.options import OwlOptions
from wot_toolchain.config import load_project
from wot_toolchain.schema_utils import load_schema_view

CONFIG = Path(__file__).resolve().parent.parent / "wot-toolchain.yaml"
MODULES = ("hctl", "jsonschema", "td", "tm", "wotsec")
BUILT_IN_NAMESPACES = (str(RDF), str(RDFS), str(OWL))
LOGICAL_PROPERTY_TYPES = (OWL.ObjectProperty, OWL.DatatypeProperty)

EX = Namespace("https://example.org/s#")
SDO = Namespace("http://schema.org/")

_SCHEMA = """\
id: https://example.org/s
name: s
title: Example Things
default_prefix: ex
default_range: string
prefixes:
  ex: https://example.org/s#
  linkml: https://w3id.org/linkml/
  schema: http://schema.org/
  dcterms: http://purl.org/dc/terms/
  rdfs: http://www.w3.org/2000/01/rdf-schema#
imports:
  - linkml:types
annotations:
  dcterms:publisher:
    value:
      "@type": schema:Organization
      schema:name: Example Group
      schema:url: https://example.org/group
slots:
  summary:
    slot_uri: ex:summary
    description: A short text.
    annotations:
      rdfs:subPropertyOf: dcterms:description
classes:
  Thing:
    class_uri: ex:Thing
    description: A thing.
    slots: [summary]
"""


def _logical_properties(graph: Graph) -> set[URIRef]:
    """Return the object and datatype properties of ``graph`` and the properties they specialise."""
    typed = {s for owl_type in LOGICAL_PROPERTY_TYPES for s in graph.subjects(RDF.type, owl_type)}
    return typed | {parent for child, parent in graph.subject_objects(RDFS.subPropertyOf) if child in typed}


def _annotation_predicates(graph: Graph) -> set[URIRef]:
    """Return the predicates of ``graph`` that OWL reads as annotations and does not itself declare."""
    used = {p for p in graph.predicates() if not str(p).startswith(BUILT_IN_NAMESPACES)}
    return used - _logical_properties(graph)


def _declared_annotation_properties(graph: Graph) -> set[URIRef]:
    return set(graph.subjects(RDF.type, OWL.AnnotationProperty))


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


def test_generator_declares_the_annotation_predicates_it_emits(example: Graph) -> None:
    assert _declared_annotation_properties(example) == {
        DCTERMS.title,
        DCTERMS.publisher,
        VANN.preferredNamespacePrefix,
        VANN.preferredNamespaceUri,
        SDO.name,
        SDO.url,
        SKOS.definition,
        SKOS.inScheme,
    }


def test_generator_declares_the_parent_of_a_datatype_property_a_datatype_property(example: Graph) -> None:
    assert (EX.summary, RDFS.subPropertyOf, DCTERMS.description) in example
    assert set(example.objects(DCTERMS.description, RDF.type)) == {OWL.DatatypeProperty}


def test_generator_declares_no_built_in_or_logical_property(example: Graph) -> None:
    declared = _declared_annotation_properties(example)

    assert not {p for p in declared if str(p).startswith(BUILT_IN_NAMESPACES)}
    assert not declared & _logical_properties(example)


def test_all_modules_are_generated(generated: dict[str, Graph]) -> None:
    assert set(generated) == set(MODULES)


@pytest.mark.parametrize("module", MODULES)
def test_module_declares_every_annotation_predicate(generated: dict[str, Graph], module: str) -> None:
    graph = generated[module]

    assert _annotation_predicates(graph) <= _declared_annotation_properties(graph)


@pytest.mark.parametrize("module", MODULES)
def test_module_declares_no_logical_property_as_annotation(generated: dict[str, Graph], module: str) -> None:
    graph = generated[module]

    assert not _declared_annotation_properties(graph) & _logical_properties(graph)

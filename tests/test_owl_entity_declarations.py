"""Every class and super-property a generated ontology refers to is declared, so OWL 2 DL tools need not guess."""

from pathlib import Path

import pytest
from rdflib import OWL, RDF, RDFS, XSD, BNode, Graph, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import DCTERMS

from wot_toolchain import pipeline
from wot_toolchain.artifacts.owl.generator import declare_referenced_classes, declare_super_properties
from wot_toolchain.config import load_project
from wot_toolchain.schema_utils import load_schema_view

CONFIG = Path(__file__).resolve().parent.parent / "wot-toolchain.yaml"
MODULES = ("hctl", "jsonschema", "td", "tm", "wotsec")
BUILT_IN_NAMESPACES = (str(RDF), str(RDFS), str(OWL), str(XSD))
LOGICAL_PROPERTY_TYPES = (OWL.ObjectProperty, OWL.DatatypeProperty)

EX = Namespace("https://example.org/s#")
OTHER = Namespace("https://example.org/other#")


def _classes(graph: Graph) -> set[URIRef]:
    return set(graph.subjects(RDF.type, OWL.Class))


def _referenced_classes(graph: Graph) -> set[URIRef]:
    """Return the named, not built-in resources that ``graph`` uses where OWL expects a class."""
    object_properties = set(graph.subjects(RDF.type, OWL.ObjectProperty))
    referenced = {
        *graph.objects(None, RDFS.domain),
        *graph.objects(None, RDFS.subClassOf),
        *graph.objects(None, RDF.type),
        *(o for s, o in graph.subject_objects(RDFS.range) if s in object_properties),
    }
    return {c for c in referenced if isinstance(c, URIRef) and not str(c).startswith(BUILT_IN_NAMESPACES)}


def _graph(*triples: tuple[URIRef | BNode, URIRef, URIRef | BNode]) -> Graph:
    graph = Graph()
    for triple in triples:
        graph.add(triple)
    return graph


@pytest.fixture(scope="module")
def generated(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Graph]:
    output_dir = tmp_path_factory.mktemp("owl")
    project = load_project(CONFIG)
    pipeline._gen_owl(project, load_schema_view(project.root_schema, merge_imports=True), output_dir)
    return {path.stem: Graph().parse(path, format="turtle") for path in output_dir.glob("*.ttl")}


def test_class_in_the_domain_of_a_property_is_declared() -> None:
    graph = _graph((EX.name, RDF.type, OWL.DatatypeProperty), (EX.name, RDFS.domain, OTHER.Thing))
    declare_referenced_classes(graph)
    assert _classes(graph) == {OTHER.Thing}


def test_class_in_the_range_of_an_object_property_is_declared() -> None:
    graph = _graph((EX.part, RDF.type, OWL.ObjectProperty), (EX.part, RDFS.range, OTHER.Part))
    declare_referenced_classes(graph)
    assert _classes(graph) == {OTHER.Part}


def test_datatype_in_the_range_of_a_datatype_property_is_not_declared_a_class() -> None:
    graph = _graph((EX.name, RDF.type, OWL.DatatypeProperty), (EX.name, RDFS.range, OTHER.Text))
    declare_referenced_classes(graph)
    assert not _classes(graph)


def test_xsd_datatype_in_the_range_of_an_object_property_is_not_declared_a_class() -> None:
    graph = _graph((EX.link, RDF.type, OWL.ObjectProperty), (EX.link, RDFS.range, XSD.anyURI))
    declare_referenced_classes(graph)
    assert not _classes(graph)


def test_superclass_and_type_of_an_individual_are_declared() -> None:
    publisher = BNode()
    graph = _graph(
        (EX.Kind, RDF.type, OWL.Class),
        (EX.Kind, RDFS.subClassOf, OTHER.Enumeration),
        (publisher, RDF.type, OTHER.Organization),
    )
    declare_referenced_classes(graph)
    assert _classes(graph) == {EX.Kind, OTHER.Enumeration, OTHER.Organization}


def test_member_of_a_class_union_is_declared() -> None:
    union, members = BNode(), BNode()
    graph = _graph(
        (EX.part, RDF.type, OWL.ObjectProperty),
        (EX.part, RDFS.range, union),
        (union, RDF.type, OWL.Class),
        (union, OWL.unionOf, members),
    )
    Collection(graph, members, [OTHER.Part, OTHER.Whole])
    declare_referenced_classes(graph)
    assert {c for c in _classes(graph) if isinstance(c, URIRef)} == {OTHER.Part, OTHER.Whole}


def test_built_in_and_anonymous_classes_are_left_alone() -> None:
    restriction = BNode()
    graph = _graph(
        (EX.Kind, RDF.type, OWL.Class),
        (EX.Kind, RDFS.subClassOf, OWL.Thing),
        (EX.Kind, RDFS.subClassOf, restriction),
        (restriction, RDF.type, OWL.Restriction),
    )
    declare_referenced_classes(graph)
    assert _classes(graph) == {EX.Kind}


@pytest.mark.parametrize("kind", LOGICAL_PROPERTY_TYPES)
def test_parent_of_a_logical_property_is_declared_with_the_same_kind(kind: URIRef) -> None:
    graph = _graph((EX.summary, RDF.type, kind), (EX.summary, RDFS.subPropertyOf, DCTERMS.description))
    declare_super_properties(graph)
    assert set(graph.objects(DCTERMS.description, RDF.type)) == {kind}


def test_parent_that_is_already_declared_is_left_alone() -> None:
    graph = _graph(
        (EX.summary, RDF.type, OWL.DatatypeProperty),
        (EX.text, RDF.type, OWL.DatatypeProperty),
        (EX.summary, RDFS.subPropertyOf, EX.text),
    )
    before = set(graph)
    declare_super_properties(graph)
    assert set(graph) == before


@pytest.mark.parametrize("module", MODULES)
def test_module_declares_every_class_it_refers_to(generated: dict[str, Graph], module: str) -> None:
    graph = generated[module]
    assert _referenced_classes(graph) <= _classes(graph)


@pytest.mark.parametrize("module", MODULES)
def test_module_declares_every_super_property(generated: dict[str, Graph], module: str) -> None:
    graph = generated[module]
    typed = {s for kind in LOGICAL_PROPERTY_TYPES for s in graph.subjects(RDF.type, kind)}
    parents = {parent for child, parent in graph.subject_objects(RDFS.subPropertyOf) if child in typed}
    assert parents <= typed

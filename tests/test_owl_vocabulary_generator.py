"""Test the module-scoped OWL vocabulary serializer."""
from __future__ import annotations

from pathlib import Path

import pytest
from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS

from src.wotis.generators.owl import MODULES, generate_owl_vocabularies


@pytest.fixture(scope="module")
def ontologies(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Graph]:
    output_dir = tmp_path_factory.mktemp("owl")
    generate_owl_vocabularies(output_dir)
    graphs = {}
    for _, filename in MODULES:
        graph = Graph()
        graph.parse(output_dir / filename, format="turtle")
        graphs[filename] = graph
    return graphs


@pytest.mark.parametrize(
    ("filename", "ontology_iri", "class_iri", "property_iri"),
    [
        ("td.ttl", "https://www.w3.org/2019/wot/td", "https://www.w3.org/2019/wot/td#Thing", "https://www.w3.org/2019/wot/td#hasForm"),
        ("hctl.ttl", "https://www.w3.org/2019/wot/hypermedia", "https://www.w3.org/2019/wot/hypermedia#Form", "https://www.w3.org/2019/wot/hypermedia#hasTarget"),
        ("wotsec.ttl", "https://www.w3.org/2019/wot/security", "https://www.w3.org/2019/wot/security#SecurityScheme", "https://www.w3.org/2019/wot/security#apikeyIn"),
        ("jsonschema.ttl", "https://www.w3.org/2019/wot/json-schema", "https://www.w3.org/2019/wot/json-schema#DataSchema", "https://www.w3.org/2019/wot/json-schema#minimum"),
    ],
)
def test_module_ontology_contains_its_owned_vocabulary(
    ontologies: dict[str, Graph], filename: str, ontology_iri: str, class_iri: str, property_iri: str
) -> None:
    graph = ontologies[filename]
    ontology = URIRef(ontology_iri)
    class_term = URIRef(class_iri)
    property_term = URIRef(property_iri)

    assert (ontology, RDF.type, OWL.Ontology) in graph
    assert (class_term, RDF.type, OWL.Class) in graph
    assert (class_term, SKOS.inScheme, ontology) in graph
    assert (property_term, RDFS.isDefinedBy, ontology) in graph
    assert (property_term, SKOS.inScheme, ontology) in graph


def test_owl_vocabulary_files_do_not_contain_linkml_validation_axioms(ontologies: dict[str, Graph]) -> None:
    for graph in ontologies.values():
        assert not list(graph.triples((None, RDF.type, URIRef("https://w3id.org/linkml/ClassDefinition"))))
        assert not list(graph.triples((None, RDF.type, OWL.Restriction)))


def test_legacy_merged_ontology_is_removed(tmp_path: Path) -> None:
    legacy_output = tmp_path / "ontology.owl.ttl"
    legacy_output.write_text("obsolete", encoding="utf-8")

    generate_owl_vocabularies(tmp_path)

    assert not legacy_output.exists()


@pytest.mark.parametrize(
    ("filename", "unexpected_property"),
    [
        ("td.ttl", "https://www.w3.org/2019/wot/td#actions"),
        ("hctl.ttl", "https://www.w3.org/2019/wot/hypermedia#href"),
        ("wotsec.ttl", "https://www.w3.org/2019/wot/security#scheme"),
    ],
)
def test_implicit_json_members_are_not_invented_as_ontology_properties(
    ontologies: dict[str, Graph], filename: str, unexpected_property: str
) -> None:
    assert not list(ontologies[filename].triples((URIRef(unexpected_property), RDF.type, None)))


def test_explicit_terms_from_untyped_helper_classes_are_preserved(ontologies: dict[str, Graph]) -> None:
    graph = ontologies["td.ttl"]
    for property_name in ("instance", "model"):
        assert list(
            graph.triples((URIRef(f"https://www.w3.org/2019/wot/td#{property_name}"), RDF.type, OWL.DatatypeProperty))
        )

"""Validate the governance metadata for approved upstream divergences."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from rdflib import Graph, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL
from rdflib.term import Node


TESTS_DIR = Path(__file__).resolve().parent.parent
DIVERGENCES_DIR = TESTS_DIR / "resources" / "approved_divergences"
DOCUMENTS = {
    "html.yaml": {"semantic-correction", "editorial-correction"},
    "snippets.yaml": {"complete-example"},
}


@pytest.mark.parametrize(("filename", "categories"), DOCUMENTS.items())
def test_approved_divergence_document_is_well_formed(filename: str, categories: set[str]) -> None:
    document = yaml.safe_load((DIVERGENCES_DIR / filename).read_text(encoding="utf-8"))

    assert set(document) == {"schema_version", "upstream", "policy", "divergences"}
    assert document["schema_version"] == 1
    assert document["upstream"]["repository"] == "w3c/wot-thing-description"
    assert document["upstream"]["artifact"] == "resources/upstream/html/index.html"
    assert document["policy"]

    divergences = document["divergences"]
    identifiers = [entry["id"] for entry in divergences]
    assert len(identifiers) == len(set(identifiers)), "divergence IDs must be unique"
    for entry in divergences:
        assert entry["category"] in categories
        assert entry["review"] in {"approved", "proposed"}
        assert entry["rationale"]
        assert entry["upstream_locator"]
        assert entry["expected_generated"]


def test_html_divergences_have_complete_locators() -> None:
    document = yaml.safe_load((DIVERGENCES_DIR / "html.yaml").read_text(encoding="utf-8"))
    for entry in document["divergences"]:
        locator = entry["upstream_locator"]
        if locator["kind"] == "table_cell":
            assert {"section_id", "table", "row_id", "column"} <= set(locator)
        else:
            assert locator["kind"] == "assertion"
            assert locator.get("assertion_id")
        assert entry["expected_generated"].get("text")


def test_snippet_divergences_have_complete_locators() -> None:
    document = yaml.safe_load((DIVERGENCES_DIR / "snippets.yaml").read_text(encoding="utf-8"))
    for entry in document["divergences"]:
        locator = entry["upstream_locator"]
        assert locator["kind"] == "example"
        assert locator.get("example_id") or (locator.get("section_id") and locator.get("position"))
        assert entry["expected_difference_paths"]
        assert entry["expected_generated"].get("json_paths")


OWL_DIR = TESTS_DIR.parent / "resources" / "gens" / "owl"
OWL_DOCUMENT = yaml.safe_load((DIVERGENCES_DIR / "owl.yaml").read_text(encoding="utf-8"))
OWL_CATEGORIES = {"semantic-correction", "vocabulary-change"}


@pytest.fixture(scope="module")
def generated_ontologies() -> Graph:
    graph = Graph()
    for path in sorted(OWL_DIR.glob("*.ttl")):
        graph.parse(path)
    return graph


def _iri(graph: Graph, name: str) -> URIRef:
    """Return ``name`` as an IRI: an absolute IRI as it is, a CURIE expanded with the prefixes of ``graph``."""
    return URIRef(name) if "://" in name else graph.namespace_manager.expand_curie(name)


def _values(graph: Graph, subject: URIRef, predicate: URIRef) -> set[Node]:
    """Return the values of ``predicate`` on ``subject``, an owl:unionOf or owl:oneOf class as its members."""
    values: set[Node] = set()
    for value in graph.objects(subject, predicate):
        lists = [*graph.objects(value, OWL.unionOf), *graph.objects(value, OWL.oneOf)]
        values.update(member for members in lists for member in Collection(graph, members))
        if not lists:
            values.add(value)
    return values


def test_owl_divergence_document_is_well_formed() -> None:
    assert set(OWL_DOCUMENT) == {"schema_version", "upstream", "policy", "divergences"}
    assert OWL_DOCUMENT["schema_version"] == 1
    assert set(OWL_DOCUMENT["upstream"]) == {"repository", "artifact", "revision"}
    assert OWL_DOCUMENT["upstream"]["repository"] == "w3c/wot-thing-description"
    assert OWL_DOCUMENT["policy"]

    identifiers = [entry["id"] for entry in OWL_DOCUMENT["divergences"]]
    assert len(identifiers) == len(set(identifiers)), "divergence IDs must be unique"
    for entry in OWL_DOCUMENT["divergences"]:
        assert entry["category"] in OWL_CATEGORIES
        assert entry["review"] in {"approved", "proposed"}
        assert entry["rationale"]
        assert entry["upstream_locator"]
        assert entry["expected_generated"]
        assert set(entry["expected_generated"]) <= {"terms", "absent"}


@pytest.mark.parametrize("entry", OWL_DOCUMENT["divergences"], ids=lambda entry: entry["id"])
def test_owl_divergence_holds_in_generated_ontologies(entry: dict, generated_ontologies: Graph) -> None:
    graph = generated_ontologies
    expected = entry["expected_generated"]
    for term, statements in expected.get("terms", {}).items():
        for predicate, values in statements.items():
            found = _values(graph, _iri(graph, term), _iri(graph, predicate))
            assert found == {_iri(graph, value) for value in values}, f"{term} {predicate}"
    for name in expected.get("absent", []):
        node = _iri(graph, name)
        used = (node, None, None) in graph or (None, node, None) in graph or (None, None, node) in graph
        assert not used, f"{name} occurs in the generated ontologies"

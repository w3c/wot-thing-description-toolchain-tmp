"""Structural smoke tests for generated OWL ontologies.

These do NOT compare against upstream targets (which may themselves be wrong).
They verify parse validity, ontology headers, label coverage, and absence of
generator artifacts — properties that must hold regardless of spec interpretation.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import rdflib
from rdflib import OWL, RDF, RDFS

OWL_DIR = Path(__file__).resolve().parent.parent / "resources" / "gens" / "owl"

MODULES = {
    "td": "https://www.w3.org/2019/wot/td",
    "hctl": "https://www.w3.org/2019/wot/hypermedia",
    "wotsec": "https://www.w3.org/2019/wot/security",
    "jsonschema": "https://www.w3.org/2019/wot/json-schema",
    "tm": "https://www.w3.org/2019/wot/tm",
}


def _load(module: str) -> rdflib.Graph:
    g = rdflib.Graph()
    g.parse(OWL_DIR / f"{module}.ttl", format="turtle")
    return g


@pytest.fixture(scope="module", params=list(MODULES.keys()))
def owl_module(request):
    return request.param, _load(request.param)


def test_parse_valid(owl_module):
    _, g = owl_module
    assert len(g) > 0


def test_ontology_header(owl_module):
    module, g = owl_module
    ontologies = list(g.subjects(RDF.type, OWL.Ontology))
    assert len(ontologies) == 1, f"{module}: expected 1 owl:Ontology, got {len(ontologies)}"
    assert str(ontologies[0]) == MODULES[module]


def test_label_coverage(owl_module):
    module, g = owl_module
    labeled = set(g.subjects(RDFS.label, None))
    classes = set(g.subjects(RDF.type, OWL.Class))
    props = set(g.subjects(RDF.type, OWL.ObjectProperty)) | set(g.subjects(RDF.type, OWL.DatatypeProperty))
    own = {term for term in classes | props if str(term).startswith(MODULES[module])}
    unlabeled = own - labeled
    assert not unlabeled, f"{module}: missing rdfs:label on {[str(u) for u in sorted(unlabeled)]}"


def test_no_linkml_artifacts(owl_module):
    module, g = owl_module
    linkml_triples = [(s, p, o) for s, p, o in g if "linkml" in str(p).lower()]
    assert not linkml_triples, (
        f"{module}: found {len(linkml_triples)} triples with linkml predicates: "
        f"{[str(p) for _, p, _ in linkml_triples[:5]]}"
    )

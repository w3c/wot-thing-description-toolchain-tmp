"""Regression tests for LinkML-declared WoT JSON-LD context mappings."""

from __future__ import annotations

import json
from pathlib import Path

from rdflib import Graph, Literal, URIRef


REPO_ROOT = Path(__file__).resolve().parent.parent
CONTEXT_PATH = REPO_ROOT / "resources/gens/jsonldcontext/context.jsonld"
JSON_SCHEMA_PATH = REPO_ROOT / "resources/gens/jsonschema/jsonschema.json"


def _context() -> dict:
    return json.loads(CONTEXT_PATH.read_text(encoding="utf-8"))["@context"]


def _json_schema() -> dict:
    return json.loads(JSON_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_security_name_is_a_scoped_json_key() -> None:
    context = _context()
    security_context = context["securityDefinitions"]["@context"]

    assert "@name" not in context
    assert security_context["name"]["@id"] == "wotsec:name"

    definitions = _json_schema()["$defs"]
    for class_name in ("APIKeySecurityScheme", "BasicSecurityScheme", "BearerSecurityScheme", "DigestSecurityScheme"):
        properties = definitions[class_name]["properties"]
        assert "name" in properties
        assert "@name" not in properties


def test_indexed_maps_preserve_their_rdf_key_predicates() -> None:
    context = _context()

    assert context["properties"]["@index"] == "name"
    assert context["actions"]["@index"] == "name"
    assert context["events"]["@index"] == "name"
    assert context["uriVariables"]["@index"] == "name"
    assert context["securityDefinitions"]["@index"] == "hasInstanceConfiguration"
    assert context["schemaDefinitions"]["@index"] == "hasInstanceConfiguration"

    data_schema_context = context["properties"]["@context"]
    assert data_schema_context["properties"]["@index"] == "name"


def test_scoped_contexts_select_the_correct_vocabulary() -> None:
    context = _context()

    assert context["properties"]["@context"]["@vocab"].endswith("json-schema#")
    assert context["securityDefinitions"]["@context"]["@vocab"].endswith("security#")
    assert context["forms"]["@context"]["type"]["@id"] == "hctl:hintsAtMediaType"
    assert context["links"]["@context"]["type"]["@id"] == "hctl:hintsAtMediaType"


def test_context_scopes_derive_from_range_ownership() -> None:
    context = _context()
    assert context["properties"]["@context"]["@vocab"].endswith("json-schema#")
    assert context["links"]["@context"]["@vocab"].endswith("hypermedia#")
    assert context["forms"]["@context"]["@vocab"].endswith("hypermedia#")
    assert context["securityDefinitions"]["@context"]["@vocab"].endswith("security#")
    assert context["schemaDefinitions"]["@context"]["@vocab"].endswith("json-schema#")
    assert context["uriVariables"]["@context"]["@vocab"].endswith("json-schema#")
    assert context["input"]["@context"]["@vocab"].endswith("json-schema#")
    assert "@context" not in context["allOf"]
    assert "@context" not in context["security"]


def test_jsonld_keywords_expand_a_minimal_thing() -> None:
    context = _context()
    document = {
        "@context": context,
        "@type": "Thing",
        "id": "urn:example:thing",
        "title": "Example Thing",
    }

    graph = Graph()
    graph.parse(data=json.dumps(document), format="json-ld")

    subject = URIRef("urn:example:thing")
    assert (
        subject,
        URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        URIRef("https://www.w3.org/2019/wot/td#Thing"),
    ) in graph


def test_security_references_expand_as_literals() -> None:
    document = {
        "@context": _context(),
        "@type": "Thing",
        "id": "urn:example:thing",
        "title": "Example Thing",
        "security": ["basic_sc", "nosec_sc"],
    }

    graph = Graph()
    graph.parse(data=json.dumps(document), format="json-ld")

    predicate = URIRef("https://www.w3.org/2019/wot/td#hasSecurityConfiguration")
    values = set(graph.objects(URIRef("urn:example:thing"), predicate))
    assert values == {Literal("basic_sc"), Literal("nosec_sc")}

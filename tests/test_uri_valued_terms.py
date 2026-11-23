"""A term whose value is a URI that names no node of the Thing Description is an ``xsd:anyURI`` literal."""

import json
from pathlib import Path
from typing import Any

import pytest
from rdflib import OWL, RDF, RDFS, SH, XSD, Graph, Literal, Namespace, URIRef

from wot_toolchain import pipeline
from wot_toolchain.config import load_project
from wot_toolchain.schema_utils import load_schema_view

CONFIG = Path(__file__).resolve().parent.parent / "wot-toolchain.yaml"
BASE = "https://td.example.com/td.jsonld"
HCTL = Namespace("https://www.w3.org/2019/wot/hypermedia#")
WOTSEC = Namespace("https://www.w3.org/2019/wot/security#")

THING: dict[str, Any] = {
    "id": "urn:example:thing",
    "title": "Lamp",
    "securityDefinitions": {
        "oauth2_sc": {
            "scheme": "oauth2",
            "flow": "code",
            "proxy": "https://proxy.example.com/",
            "authorization": "https://auth.example.com/authorize",
            "token": "https://auth.example.com/token",
            "refresh": "https://auth.example.com/refresh",
        }
    },
    "security": "oauth2_sc",
    "links": [{"href": "https://lamp.example.com/manual", "anchor": "https://lamp.example.com/bulb"}],
}

URI_VALUED = (
    ("hctl", "anchor", HCTL.hasAnchor, "https://lamp.example.com/bulb"),
    ("wotsec", "proxy", WOTSEC.proxy, "https://proxy.example.com/"),
    ("wotsec", "authorization", WOTSEC.authorization, "https://auth.example.com/authorize"),
    ("wotsec", "token", WOTSEC.token, "https://auth.example.com/token"),
    ("wotsec", "refresh", WOTSEC.refresh, "https://auth.example.com/refresh"),
)


def _project_and_view() -> tuple[Any, Any]:
    project = load_project(CONFIG)
    return project, load_schema_view(project.root_schema, merge_imports=True)


@pytest.fixture(scope="module")
def thing(tmp_path_factory: pytest.TempPathFactory) -> Graph:
    """Return the RDF graph of ``THING`` read with the generated JSON-LD context."""
    output_dir = tmp_path_factory.mktemp("context")
    project, view = _project_and_view()
    pipeline._gen_jsonldcontext(project, view, output_dir)
    context = json.loads((output_dir / "context.jsonld").read_text(encoding="utf-8"))["@context"]
    return Graph().parse(data=json.dumps({"@context": context, **THING}), format="json-ld", base=BASE)


@pytest.fixture(scope="module")
def ontologies(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Graph]:
    output_dir = tmp_path_factory.mktemp("owl")
    project, view = _project_and_view()
    pipeline._gen_owl(project, view, output_dir)
    return {path.stem: Graph().parse(path, format="turtle") for path in output_dir.glob("*.ttl")}


@pytest.fixture(scope="module")
def shapes(tmp_path_factory: pytest.TempPathFactory) -> Graph:
    output_dir = tmp_path_factory.mktemp("shacl")
    project, view = _project_and_view()
    pipeline._gen_shacl(project, view, output_dir)
    return Graph().parse(output_dir / "shapes.shacl.ttl", format="turtle")


@pytest.fixture(scope="module")
def json_schema(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    output_dir = tmp_path_factory.mktemp("jsonschema")
    project, view = _project_and_view()
    pipeline._gen_jsonschema(project, view, output_dir)
    schema: dict[str, Any] = json.loads((output_dir / "jsonschema.json").read_text(encoding="utf-8"))
    return schema


@pytest.mark.parametrize(("module", "_term", "property_", "_value"), URI_VALUED)
def test_term_is_a_datatype_property_ranging_over_any_uri(
    ontologies: dict[str, Graph], module: str, _term: str, property_: URIRef, _value: str
) -> None:
    graph = ontologies[module]

    assert set(graph.objects(property_, RDF.type)) == {OWL.DatatypeProperty}
    assert set(graph.objects(property_, RDFS.range)) == {XSD.anyURI}


@pytest.mark.parametrize(("_module", "_term", "property_", "value"), URI_VALUED)
def test_value_reads_as_an_any_uri_literal(
    thing: Graph, _module: str, _term: str, property_: URIRef, value: str
) -> None:
    assert set(thing.objects(None, property_)) == {Literal(value, datatype=XSD.anyURI)}


@pytest.mark.parametrize(("_module", "_term", "property_", "_value"), URI_VALUED)
def test_shape_asks_for_an_any_uri_literal(
    shapes: Graph, _module: str, _term: str, property_: URIRef, _value: str
) -> None:
    property_shapes = list(shapes.subjects(SH.path, property_))

    assert property_shapes
    for shape in property_shapes:
        assert set(shapes.objects(shape, SH.datatype)) == {XSD.anyURI}
        assert set(shapes.objects(shape, SH.nodeKind)) == {SH.Literal}


@pytest.mark.parametrize(("_module", "term", "_property", "_value"), URI_VALUED)
def test_term_stays_a_uri_string_in_json(
    json_schema: dict[str, Any], _module: str, term: str, _property: URIRef, _value: str
) -> None:
    holders = [d["properties"][term] for d in json_schema["$defs"].values() if term in d.get("properties", {})]

    assert holders
    for holder in holders:
        assert holder["type"] == "string"
        assert holder["format"] == "uri"

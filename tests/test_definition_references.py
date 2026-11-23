"""A ``security`` or ``schema`` name refers to the node its definitions map defines under that name."""

import json
from pathlib import Path
from typing import Any

import pytest
from rdflib import OWL, RDF, RDFS, SH, Graph, Namespace, URIRef
from rdflib.term import Node

from wot_toolchain import pipeline
from wot_toolchain.config import load_project
from wot_toolchain.schema_utils import load_schema_view

CONFIG = Path(__file__).resolve().parent.parent / "wot-toolchain.yaml"
BASE = "https://td.example.com/td.jsonld"
TD = Namespace("https://www.w3.org/2019/wot/td#")
HCTL = Namespace("https://www.w3.org/2019/wot/hypermedia#")
WOTSEC = Namespace("https://www.w3.org/2019/wot/security#")
JSONSCHEMA = Namespace("https://www.w3.org/2019/wot/json-schema#")

THING: dict[str, Any] = {
    "id": "urn:example:thing",
    "title": "Lamp",
    "securityDefinitions": {"basic_sc": {"scheme": "basic"}, "title": {"scheme": "nosec"}},
    "security": ["basic_sc", "title"],
    "schemaDefinitions": {"errorPayload": {"type": "string"}},
    "actions": {
        "toggle": {
            "forms": [
                {
                    "href": "https://lamp.example.com/toggle",
                    "security": "basic_sc",
                    "additionalResponses": [{"contentType": "application/json", "schema": "errorPayload"}],
                }
            ]
        }
    },
}

REFERENCES = (
    ("td", TD.hasSecurityConfiguration, WOTSEC.SecurityScheme),
    ("hctl", HCTL.hasAdditionalOutputSchema, JSONSCHEMA.DataSchema),
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


def _property_shapes(shapes: Graph, path: URIRef) -> list[Node]:
    return list(shapes.subjects(SH.path, path))


def test_security_definitions_are_named_nodes(thing: Graph) -> None:
    assert set(thing.objects(None, TD.definesSecurityScheme)) == {
        URIRef("https://td.example.com/basic_sc"),
        URIRef("https://td.example.com/title"),
    }


def test_security_names_refer_to_the_defined_schemes(thing: Graph) -> None:
    defined = set(thing.objects(None, TD.definesSecurityScheme))
    referred = set(thing.objects(None, TD.hasSecurityConfiguration))

    assert referred == defined


def test_a_referred_scheme_carries_its_definition(thing: Graph) -> None:
    scheme = URIRef("https://td.example.com/basic_sc")

    assert (scheme, RDF.type, WOTSEC.BasicSecurityScheme) in thing or set(thing.objects(scheme, WOTSEC.scheme))


def test_schema_name_refers_to_the_defined_schema(thing: Graph) -> None:
    defined = set(thing.objects(None, TD.schemaDefinitions))
    referred = set(thing.objects(None, HCTL.hasAdditionalOutputSchema))

    assert referred == defined == {URIRef("https://td.example.com/errorPayload")}


@pytest.mark.parametrize(("module", "property_", "range_"), REFERENCES)
def test_reference_is_an_object_property_ranging_over_the_defined_class(
    ontologies: dict[str, Graph], module: str, property_: URIRef, range_: URIRef
) -> None:
    graph = ontologies[module]

    assert set(graph.objects(property_, RDF.type)) == {OWL.ObjectProperty}
    assert set(graph.objects(property_, RDFS.range)) == {range_}


@pytest.mark.parametrize(("_module", "property_", "range_"), REFERENCES)
def test_reference_shape_asks_for_a_node_of_the_defined_class(
    shapes: Graph, _module: str, property_: URIRef, range_: URIRef
) -> None:
    property_shapes = _property_shapes(shapes, property_)

    assert property_shapes
    for shape in property_shapes:
        assert set(shapes.objects(shape, SH["class"])) == {range_}
        assert not set(shapes.objects(shape, SH.datatype))


def test_references_stay_names_in_json(json_schema: dict[str, Any]) -> None:
    definitions = json_schema["$defs"]
    schema_reference = definitions["AdditionalExpectedResponse"]["properties"]["schema"]

    assert schema_reference["type"] == "string"
    assert "$ref" not in json.dumps(definitions["Form_element_base"]["properties"]["security"])

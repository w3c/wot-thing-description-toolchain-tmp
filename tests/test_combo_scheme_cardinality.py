"""A combo security scheme lists two or more scheme names in ``oneOf`` or ``allOf`` when the term is present."""

import json
from pathlib import Path
from typing import Any

import pytest
from rdflib import RDF, SH, Graph, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.term import Node

from wot_toolchain import pipeline
from wot_toolchain.config import load_project
from wot_toolchain.schema_utils import load_schema_view

CONFIG = Path(__file__).resolve().parent.parent / "wot-toolchain.yaml"
WOTSEC = Namespace("https://www.w3.org/2019/wot/security#")
COMBO_SHAPE = WOTSEC.ComboSecuritySchemeShape
TERMS = ("oneOf", "allOf")


@pytest.fixture(scope="module")
def json_schema(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    output_dir = tmp_path_factory.mktemp("jsonschema")
    project = load_project(CONFIG)
    pipeline._gen_jsonschema(project, load_schema_view(project.root_schema, merge_imports=True), output_dir)
    schema: dict[str, Any] = json.loads((output_dir / "jsonschema.json").read_text(encoding="utf-8"))
    return schema


@pytest.fixture(scope="module")
def shapes(tmp_path_factory: pytest.TempPathFactory) -> Graph:
    output_dir = tmp_path_factory.mktemp("shacl")
    project = load_project(CONFIG)
    pipeline._gen_shacl(project, load_schema_view(project.root_schema, merge_imports=True), output_dir)
    return Graph().parse(output_dir / "shapes.shacl.ttl", format="turtle")


def _property_shape(shapes: Graph, path: URIRef) -> Node:
    (shape,) = [s for s in shapes.objects(COMBO_SHAPE, SH.property) if (s, SH.path, path) in shapes]
    return shape


def _count_alternatives(shapes: Graph, path: URIRef) -> list[dict[URIRef, int]]:
    """Return the count constraints of every ``sh:or`` branch of the combo shape that constrains ``path``."""
    return [
        {predicate: int(value) for predicate, value in shapes.predicate_objects(branch) if predicate != SH.path}
        for alternatives in shapes.objects(COMBO_SHAPE, SH["or"])
        for branch in Collection(shapes, alternatives)
        if (branch, SH.path, path) in shapes
    ]


@pytest.mark.parametrize("term", TERMS)
def test_json_schema_requires_two_items_when_the_term_is_present(json_schema: dict[str, Any], term: str) -> None:
    combo = json_schema["$defs"]["ComboSecurityScheme"]

    assert combo["properties"][term]["minItems"] == 2
    assert "minimum" not in combo["properties"][term]["items"]
    assert term not in combo["required"]


@pytest.mark.parametrize("term", TERMS)
def test_shape_puts_no_value_range_and_no_required_count_on_the_term(shapes: Graph, term: str) -> None:
    shape = _property_shape(shapes, WOTSEC[term])

    assert (shape, SH.minInclusive, None) not in shapes
    assert (shape, SH.minCount, None) not in shapes


@pytest.mark.parametrize("term", TERMS)
def test_shape_accepts_an_absent_term_or_two_or_more_values(shapes: Graph, term: str) -> None:
    assert (COMBO_SHAPE, RDF.type, SH.NodeShape) in shapes
    assert sorted(_count_alternatives(shapes, WOTSEC[term]), key=str) == sorted(
        [{SH.maxCount: 0}, {SH.minCount: 2}], key=str
    )

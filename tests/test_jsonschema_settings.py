"""The ``generators.jsonschema`` settings of the config file determine the header, dialect and file name."""

from __future__ import annotations

import dataclasses
import json
import shutil
from pathlib import Path
from typing import Any

import jsonschema
import pytest
import yaml

from wot_toolchain.artifacts.jsonschema.dialect import apply_settings
from wot_toolchain.config import load_project
from wot_toolchain.errors import GenerationError
from wot_toolchain.pipeline import run_pipeline

MINI_PROJECT = Path(__file__).resolve().parent / "fixtures" / "mini-project"
DRAFT_07 = "http://json-schema.org/draft-07/schema#"
DRAFT_2019_09 = "https://json-schema.org/draft/2019-09/schema"


def _schema() -> dict[str, Any]:
    return {
        "$schema": DRAFT_2019_09,
        "$id": "https://example.org/from-linkml",
        "description": "From the top class.",
        "type": "object",
        "properties": {
            "plain": {"$ref": "#/$defs/Reading"},
            "described": {"$ref": "#/$defs/Reading", "description": "A reading."},
            "$defs": {"type": "string"},
        },
        "$defs": {"Reading": {"type": "object", "properties": {"next": {"$ref": "#/$defs/Reading"}}}},
    }


def _applied(dialect: str) -> dict[str, Any]:
    schema = _schema()
    apply_settings(schema, id="https://example.org/sensor", description="A sensor.", dialect=dialect)
    return schema


@pytest.mark.parametrize(("dialect", "uri"), [("draft-07", DRAFT_07), ("2019-09", DRAFT_2019_09)])
def test_header_comes_from_the_settings(dialect: str, uri: str) -> None:
    schema = _applied(dialect)
    assert (schema["$schema"], schema["$id"], schema["description"]) == (uri, "https://example.org/sensor", "A sensor.")


def test_2019_09_keeps_the_definitions_and_references() -> None:
    expected = _schema() | {"$id": "https://example.org/sensor", "description": "A sensor."}
    assert _applied("2019-09") == expected


def test_draft_07_names_the_definitions_definitions() -> None:
    schema = _applied("draft-07")
    assert "$defs" not in schema
    assert schema["definitions"]["Reading"]["properties"]["next"] == {"$ref": "#/definitions/Reading"}
    assert schema["properties"]["plain"] == {"$ref": "#/definitions/Reading"}


def test_draft_07_keeps_a_property_named_like_the_definitions_keyword() -> None:
    assert _applied("draft-07")["properties"]["$defs"] == {"type": "string"}


def test_draft_07_moves_a_reference_with_sibling_keywords_into_all_of() -> None:
    # Draft-07 ignores every keyword next to "$ref".
    assert _applied("draft-07")["properties"]["described"] == {
        "description": "A reading.",
        "allOf": [{"$ref": "#/definitions/Reading"}],
    }


def test_draft_07_schema_is_a_valid_draft_07_schema() -> None:
    jsonschema.Draft7Validator.check_schema(_applied("draft-07"))


def test_draft_07_rejects_a_keyword_that_draft_07_does_not_define() -> None:
    schema = _schema()
    schema["$defs"]["Reading"]["unevaluatedProperties"] = False
    with pytest.raises(GenerationError, match=r"unevaluatedProperties.*draft-07"):
        apply_settings(schema, id="https://example.org/sensor", description="A sensor.", dialect="draft-07")


def test_pipeline_writes_the_json_schema_that_the_config_file_describes(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    shutil.copytree(MINI_PROJECT, project_dir)
    config_path = project_dir / "wot-toolchain.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["generators"]["jsonschema"] |= {
        "id": "https://example.org/sensor.schema.json",
        "description": "Validates a sensor.",
        "dialect": "draft-07",
        "output": "sensor.schema.json",
    }
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    run_pipeline(dataclasses.replace(load_project(config_path), generators=("jsonschema",)))

    output_dir = project_dir / "gens" / "jsonschema"
    assert [path.name for path in output_dir.iterdir()] == ["sensor.schema.json"]
    schema = json.loads((output_dir / "sensor.schema.json").read_text(encoding="utf-8"))
    assert schema["$schema"] == DRAFT_07
    assert schema["$id"] == "https://example.org/sensor.schema.json"
    assert schema["description"] == "Validates a sensor."
    assert "Reading" in schema["definitions"]
    jsonschema.Draft7Validator.check_schema(schema)

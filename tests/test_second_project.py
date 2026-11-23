"""A LinkML project that is not the Thing Description generates correct artifacts with the same toolchain.

The fixture in ``tests/fixtures/mini-project`` has its own config file, top class and prefix. Every TD name
the Python code relied on would show up here as a missing or wrong artifact.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from pyld import jsonld

PROJECT = Path(__file__).resolve().parent / "fixtures" / "mini-project"
CLI_BIN = Path(sys.executable).parent / "wot-toolchain"
NAMESPACE = "https://example.org/sensor#"
SENSOR_SLOTS = ("serialNumber", "unit", "readings")
READING_SLOTS = ("measuredValue", "measuredAt")


@dataclass(frozen=True)
class Generation:
    """One run of the CLI on the mini project."""

    output_dir: Path
    result: subprocess.CompletedProcess[str]

    def json(self, *parts: str) -> Any:
        return json.loads(self.output_dir.joinpath(*parts).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def generation(tmp_path_factory: pytest.TempPathFactory) -> Generation:
    elsewhere = tmp_path_factory.mktemp("elsewhere")
    output_dir = tmp_path_factory.mktemp("mini-out") / "out"
    result = subprocess.run(
        [
            str(CLI_BIN),
            "generate-wot-resources",
            "-c",
            str(PROJECT / "wot-toolchain.yaml"),
            "--output-dir",
            str(output_dir),
            "--only",
            "jsonschema",
            "--only",
            "jsonldcontext",
        ],
        cwd=elsewhere,
        capture_output=True,
        text=True,
        check=False,
    )
    return Generation(output_dir=output_dir, result=result)


def test_cli_exits_zero(generation: Generation) -> None:
    assert generation.result.returncode == 0, generation.result.stderr


def test_only_the_requested_generators_run(generation: Generation) -> None:
    assert sorted(path.name for path in generation.output_dir.iterdir()) == ["jsonldcontext", "jsonschema"]


def test_json_schema_root_is_the_top_class(generation: Generation) -> None:
    schema = generation.json("jsonschema", "jsonschema.json")
    assert schema["title"] == "Sensor Vocabulary"
    assert set(schema["properties"]) == set(SENSOR_SLOTS)
    assert schema["required"] == ["serialNumber"]


def test_json_schema_defines_the_nested_class(generation: Generation) -> None:
    schema = generation.json("jsonschema", "jsonschema.json")
    reading = schema["$defs"]["Reading"]
    assert set(reading["properties"]) == set(READING_SLOTS)
    assert reading["required"] == ["measuredValue"]
    assert schema["properties"]["readings"]["type"] == "array"
    assert schema["properties"]["readings"]["items"]["$ref"] == "#/$defs/Reading"


def test_module_context_maps_the_project_vocabulary(generation: Generation) -> None:
    context = generation.json("jsonldcontext", "sensor-context.jsonld")["@context"]
    assert context["@vocab"] == NAMESPACE
    for term in (*SENSOR_SLOTS, *READING_SLOTS, "Sensor", "Reading"):
        assert term in context, term


def test_merged_context_declares_the_prefix(generation: Generation) -> None:
    context = generation.json("jsonldcontext", "context.jsonld")["@context"]
    assert context["sen"] == NAMESPACE


@pytest.mark.parametrize("context_file", ["sensor-context.jsonld", "context.jsonld"])
def test_context_expands_every_term_to_its_schema_iri(generation: Generation, context_file: str) -> None:
    document = {
        **generation.json("jsonldcontext", context_file),
        "@type": "Sensor",
        "serialNumber": "S-1",
        "unit": "Cel",
        "readings": [{"@type": "Reading", "measuredValue": 21.5, "measuredAt": "2026-01-01T00:00:00Z"}],
    }
    (sensor,) = jsonld.expand(document)
    (reading,) = sensor[NAMESPACE + "hasReading"]
    assert sensor["@type"] == [NAMESPACE + "Sensor"]
    assert reading["@type"] == [NAMESPACE + "Reading"]
    assert set(sensor) == {"@type", *(NAMESPACE + name for name in ("serialNumber", "unit", "hasReading"))}
    assert set(reading) == {"@type", *(NAMESPACE + name for name in READING_SLOTS)}

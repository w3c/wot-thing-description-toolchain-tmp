"""A schema the LinkML JSON Schema generator rejects raises a typed error and leaves the schema view untouched."""

from __future__ import annotations

from pathlib import Path

import pytest
from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain import pipeline
from wot_toolchain.config import JsonSchemaSettings, Project
from wot_toolchain.errors import GenerationError

# The dangling ``is_a`` loads fine but makes JsonSchemaGenerator raise ValueError.
REJECTED_SCHEMA = """
id: https://example.org/probe
name: probe
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/ex#
default_prefix: ex
imports: [linkml:types]
slots:
  kind:
    range: string
    designates_type: true
classes:
  A:
    is_a: Missing
    slots: [kind]
"""


def _project(tmp_path: Path) -> Project:
    schema = tmp_path / "probe.yaml"
    schema.write_text(REJECTED_SCHEMA, encoding="utf-8")
    return Project(
        config_path=tmp_path / "wot-toolchain.yaml",
        root_schema=schema,
        output_dir=tmp_path / "out",
        generators=("jsonschema",),
        jsonschema=JsonSchemaSettings(
            top_class="A",
            id="https://example.org/probe",
            description="A probe.",
            dialect="2019-09",
            output="jsonschema.json",
        ),
        vocabularies=(),
        spec=None,
    )


def test_generator_value_error_raises_generation_error_naming_schema(tmp_path: Path) -> None:
    project = _project(tmp_path)
    with pytest.raises(GenerationError, match=r"probe\.yaml") as excinfo:
        pipeline.run_pipeline(project)
    assert isinstance(excinfo.value.__cause__, ValueError)


def test_generator_failure_restores_designates_type(tmp_path: Path) -> None:
    project = _project(tmp_path)
    sv = SchemaView(str(project.root_schema))
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    with pytest.raises(GenerationError):
        pipeline._gen_jsonschema(project, sv, output_dir)
    assert sv.schema.slots["kind"].designates_type is True

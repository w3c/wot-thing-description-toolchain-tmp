import copy
import dataclasses
import json
from pathlib import Path

import pytest
from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.artifacts.jsonschema.generator import WotJsonSchemaGenerator
from wot_toolchain.artifacts.jsonschema.options import JsonSchemaOptions
from wot_toolchain.config import Project, load_project
from wot_toolchain.schema_utils import load_schema_view

REPO_ROOT = Path(__file__).resolve().parent.parent

CONSTRUCTOR_STATE = ("mergeimports", "top_class", "not_closed", "include_null", "preserve_names")


@pytest.fixture(scope="module")
def td_project() -> Project:
    return load_project(REPO_ROOT / "wot-toolchain.yaml")


@pytest.fixture(scope="module")
def td_schema_view(td_project: Project) -> SchemaView:
    return load_schema_view(td_project.root_schema, merge_imports=True)


def _inline_kwargs_generator(schema: object, top_class: str | None) -> JsonSchemaGenerator:
    """The generator exactly as ``_gen_jsonschema`` built it before typed options."""
    return JsonSchemaGenerator(
        schema,
        mergeimports=True,
        top_class=top_class,
        not_closed=True,
        include_null=False,
        preserve_names=True,
    )


def _state(generator: JsonSchemaGenerator) -> dict[str, object]:
    return {name: getattr(generator, name) for name in CONSTRUCTOR_STATE}


def test_options_defaults() -> None:
    assert JsonSchemaOptions() == JsonSchemaOptions(top_class=None, open=True, include_null=False)


def test_options_are_frozen_with_exactly_three_fields() -> None:
    options = JsonSchemaOptions()
    assert [f.name for f in dataclasses.fields(JsonSchemaOptions)] == ["top_class", "open", "include_null"]
    with pytest.raises(dataclasses.FrozenInstanceError):
        options.open = False  # type: ignore[misc]


def test_from_options_matches_todays_inline_constructor_state(td_project: Project, td_schema_view: SchemaView) -> None:
    wot = WotJsonSchemaGenerator.from_options(
        copy.deepcopy(td_schema_view.schema), JsonSchemaOptions(top_class=td_project.jsonschema.top_class)
    )
    upstream = _inline_kwargs_generator(copy.deepcopy(td_schema_view.schema), td_project.jsonschema.top_class)
    assert _state(wot) == _state(upstream)


def test_options_map_to_upstream_arguments(td_schema_view: SchemaView) -> None:
    wot = WotJsonSchemaGenerator.from_options(
        copy.deepcopy(td_schema_view.schema), JsonSchemaOptions(top_class="Thing", open=False, include_null=True)
    )
    assert (wot.top_class, wot.not_closed, wot.include_null) == ("Thing", False, True)


def test_td_output_equals_inline_kwargs_output(td_project: Project, td_schema_view: SchemaView) -> None:
    upstream = json.loads(
        _inline_kwargs_generator(copy.deepcopy(td_schema_view.schema), td_project.jsonschema.top_class).serialize()
    )
    wot = json.loads(
        WotJsonSchemaGenerator.from_options(
            copy.deepcopy(td_schema_view.schema), JsonSchemaOptions(top_class=td_project.jsonschema.top_class)
        ).serialize()
    )
    assert wot == upstream

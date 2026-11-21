"""ResolvedProject loads each schema view once per run and hands out what load_schema_view gives today."""

from pathlib import Path

import pytest
from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.config import Project, load_project
from wot_toolchain.generators import respec
from wot_toolchain.model import resolved as resolved_module
from wot_toolchain.model.resolved import ResolvedProject
from wot_toolchain.schema_utils import load_schema_view

REPO_MANIFEST = Path(__file__).resolve().parent.parent / "wot-toolchain.yaml"


@pytest.fixture(scope="module")
def project() -> Project:
    """The repository project."""
    return load_project(REPO_MANIFEST)


def _names(sv: SchemaView) -> dict[str, set[str]]:
    return {
        "classes": set(sv.all_classes()),
        "slots": set(sv.all_slots()),
        "enums": set(sv.all_enums()),
        "types": set(sv.all_types()),
    }


def _forbid_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_args: object, **_kwargs: object) -> SchemaView:
        raise AssertionError("schema loaded although ResolvedProject already holds the view")

    monkeypatch.setattr(resolved_module, "load_schema_view", fail)
    monkeypatch.setattr(respec, "load_schema_view", fail)


def test_merged_view_equals_todays_merged_load(project: Project) -> None:
    merged = ResolvedProject(project.main_schema).merged
    today = load_schema_view(project.main_schema, merge_imports=True)

    assert _names(merged) == _names(today)
    for slot, cls in [("title", "Thing"), ("href", "Form"), ("security", "Thing"), ("type", "DataSchema")]:
        assert merged.induced_slot(slot, cls) == today.induced_slot(slot, cls)


def test_module_view_equals_todays_unmerged_load(project: Project) -> None:
    resolved = ResolvedProject(project.main_schema)

    for module in project.modules:
        today = load_schema_view(module.schema, merge_imports=False)
        view = resolved.module(module.schema)
        assert _names(view) == _names(today), module.schema.name
        assert set(view.schema.classes or {}) == set(today.schema.classes or {}), module.schema.name


def test_views_are_loaded_once(project: Project, monkeypatch: pytest.MonkeyPatch) -> None:
    resolved = ResolvedProject(project.main_schema)
    merged = resolved.merged
    module = resolved.module(project.modules[1].schema)
    _forbid_loading(monkeypatch)

    assert resolved.merged is merged
    assert resolved.module(project.modules[1].schema) is module


def test_merged_and_module_view_of_the_main_schema_differ(project: Project) -> None:
    resolved = ResolvedProject(project.main_schema)

    assert resolved.module(project.main_schema) is not resolved.merged


def test_spec_sections_take_their_classes_from_resolved_project(
    project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert project.spec is not None
    sections = project.spec.sections
    expected = respec._classes_per_section(sections, project.spec.first_class, ResolvedProject(project.main_schema))
    resolved = ResolvedProject(project.main_schema)
    for section in sections:
        resolved.module(section.schema)
    _forbid_loading(monkeypatch)

    assert respec._classes_per_section(sections, project.spec.first_class, resolved) == expected

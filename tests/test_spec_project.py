"""The specification generator takes every project-specific setting from the manifest's ``spec`` section."""

from __future__ import annotations

import dataclasses
import json
import re
import shutil
from pathlib import Path
from types import MappingProxyType

import pytest

from wot_toolchain.config import Project, SpecConfig, load_project
from wot_toolchain.errors import GenerationError
from wot_toolchain.generators.respec import generate_respec_spec
from wot_toolchain.specgen.respec import process_snippet_placeholders

REPO_ROOT = Path(__file__).resolve().parent.parent
REPO_MANIFEST = REPO_ROOT / "wot-toolchain.yaml"

_CLASS_HEADING_RE = re.compile(r'<h3 id="[^"]*"><code>([A-Za-z]+)</code></h3>')


@pytest.fixture
def repo_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Project:
    """The repository project with spec outputs below ``tmp_path``, run from an unrelated working directory."""
    project = load_project(REPO_MANIFEST)
    assert project.spec is not None
    spec = dataclasses.replace(project.spec, output=tmp_path / "index.html", assertions_csv=None)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    return dataclasses.replace(project, spec=spec)


def _rendered_classes(spec: SpecConfig, main_schema: Path) -> list[str]:
    generate_respec_spec(spec, main_schema)
    return _CLASS_HEADING_RE.findall(spec.output.read_text(encoding="utf-8"))


def _spec(project: Project) -> SpecConfig:
    assert project.spec is not None
    return project.spec


def test_spec_does_not_depend_on_the_working_directory(repo_project: Project) -> None:
    classes = _rendered_classes(_spec(repo_project), repo_project.main_schema)

    assert classes[0] == "Thing"
    assert not list(Path.cwd().iterdir())


def test_first_class_comes_from_the_manifest(repo_project: Project) -> None:
    spec = dataclasses.replace(_spec(repo_project), first_class="VersionInfo")

    classes = _rendered_classes(spec, repo_project.main_schema)

    assert classes[0] == "VersionInfo"
    assert "Thing" in classes


def test_sections_come_from_the_manifest(repo_project: Project) -> None:
    security = next(s for s in _spec(repo_project).sections if s.id == "sec-security-vocabulary-definition")
    spec = dataclasses.replace(_spec(repo_project), sections=(security,), first_class=None)

    classes = _rendered_classes(spec, repo_project.main_schema)

    assert "SecurityScheme" in classes
    assert "Thing" not in classes


def test_snippet_manifest_edits_are_seen_by_the_next_generation(repo_project: Project, tmp_path: Path) -> None:
    spec = _spec(repo_project)
    snippets = tmp_path / "snippets"
    shutil.copytree(spec.snippets, snippets)
    manifest = snippets / "_snippets.yaml"
    placeholder = "%snippet('action-serialization')%"

    first = process_snippet_placeholders(placeholder, snippets)
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace("Sample of an Action serialization", "Edited title"),
        encoding="utf-8",
    )
    second = process_snippet_placeholders(placeholder, snippets)

    assert 'title="Sample of an Action serialization"' in first
    assert 'title="Edited title"' in second


def test_snippet_validation_schemas_come_from_the_manifest(repo_project: Project, tmp_path: Path) -> None:
    reject_all = tmp_path / "reject-all.json"
    reject_all.write_text(json.dumps({"not": {}}), encoding="utf-8")
    spec = dataclasses.replace(
        _spec(repo_project), snippet_validation_schemas=MappingProxyType({"td": reject_all, "tm": reject_all})
    )

    with pytest.raises(GenerationError, match="snippet"):
        generate_respec_spec(spec, repo_project.main_schema)


def test_unknown_first_class_is_rejected(repo_project: Project) -> None:
    spec = dataclasses.replace(_spec(repo_project), first_class="NoSuchClass")

    with pytest.raises(GenerationError, match="NoSuchClass"):
        generate_respec_spec(spec, repo_project.main_schema)

    assert not spec.output.exists()

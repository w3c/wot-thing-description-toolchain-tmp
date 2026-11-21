"""The CLI and the pipeline take every project-specific setting from the project manifest."""

from __future__ import annotations

import dataclasses
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from wot_toolchain.config import Project, load_project
from wot_toolchain.errors import GenerationError, ManifestError
from wot_toolchain.pipeline import run_pipeline

REPO_ROOT = Path(__file__).resolve().parent.parent
REPO_MANIFEST = REPO_ROOT / "wot-toolchain.yaml"
MINI_PROJECT = Path(__file__).resolve().parent / "fixtures" / "mini-project"
CLI_BIN = Path(sys.executable).parent / "wot-toolchain"


def _generate(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(CLI_BIN), "generate-wot-resources", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


@pytest.fixture
def specless_manifest(tmp_path: Path) -> Path:
    """A manifest without a ``spec`` section that reuses the repository schemas and writes below ``tmp_path``."""
    document = yaml.safe_load(REPO_MANIFEST.read_text(encoding="utf-8"))
    del document["spec"]
    document["main_schema"] = str(REPO_ROOT / document["main_schema"])
    document["output_dir"] = str(tmp_path / "out")
    for module in document["modules"]:
        module["schema"] = str(REPO_ROOT / module["schema"])
    manifest = tmp_path / "specless.yaml"
    manifest.write_text(yaml.safe_dump(document), encoding="utf-8")
    return manifest


def test_missing_manifest_exits_one_and_names_it(tmp_path: Path) -> None:
    result = _generate(tmp_path, "-c", "missing.yaml")
    assert result.returncode == 1, result.stderr
    assert str(tmp_path.resolve() / "missing.yaml") in result.stderr


def test_default_manifest_is_read_from_the_working_directory(tmp_path: Path) -> None:
    result = _generate(tmp_path)
    assert result.returncode == 1, result.stderr
    assert str(tmp_path.resolve() / "wot-toolchain.yaml") in result.stderr


def test_generate_docs_without_spec_exits_one_before_generating(tmp_path: Path, specless_manifest: Path) -> None:
    result = _generate(tmp_path, "-c", str(specless_manifest), "-d")
    assert result.returncode == 1, result.stderr
    assert "spec" in result.stderr
    assert not (tmp_path / "out").exists()


def test_input_schema_overrides_main_schema(tmp_path: Path, specless_manifest: Path) -> None:
    broken = tmp_path / "broken.yaml"
    broken.write_text("classes: [unclosed\n", encoding="utf-8")
    result = _generate(tmp_path, "-c", str(specless_manifest), "-i", str(broken))
    assert result.returncode == 1, result.stderr
    assert str(broken.resolve()) in result.stderr


@pytest.fixture
def repo_project(tmp_path: Path) -> Project:
    """The repository project, redirected to write below ``tmp_path``."""
    return dataclasses.replace(load_project(REPO_MANIFEST), output_dir=tmp_path / "out")


def test_run_pipeline_requires_spec_for_docs(repo_project: Project) -> None:
    project = dataclasses.replace(repo_project, spec=None)
    with pytest.raises(ManifestError, match="spec"):
        run_pipeline(project, generate_docs=True)
    assert not project.output_dir.exists()


def test_run_pipeline_writes_one_artifact_per_declared_module(repo_project: Project) -> None:
    project = dataclasses.replace(repo_project, generators=("owl", "jsonldcontext"))
    run_pipeline(project)

    out = project.output_dir
    assert sorted(path.name for path in out.iterdir()) == ["jsonldcontext", "owl"]
    ontologies = {module.ontology for module in project.modules if module.ontology}
    contexts = {module.context for module in project.modules if module.context}
    assert {path.name for path in (out / "owl").iterdir()} == ontologies
    assert {path.name for path in (out / "jsonldcontext").iterdir()} == contexts | {"context.jsonld"}


def test_merged_context_does_not_depend_on_module_order(repo_project: Project, tmp_path: Path) -> None:
    forward = dataclasses.replace(repo_project, generators=("jsonldcontext",), output_dir=tmp_path / "forward")
    backward = dataclasses.replace(forward, modules=tuple(reversed(forward.modules)), output_dir=tmp_path / "backward")
    run_pipeline(forward)
    run_pipeline(backward)

    merged = Path("jsonldcontext") / "context.jsonld"
    assert (forward.output_dir / merged).read_bytes() == (backward.output_dir / merged).read_bytes()


def test_linkml_source_file_is_relative_to_the_manifest(repo_project: Project) -> None:
    project = dataclasses.replace(repo_project, generators=("linkml",))
    run_pipeline(project)

    document = yaml.safe_load((project.output_dir / "linkml" / "linkml.yaml").read_text(encoding="utf-8"))
    assert document["source_file"] == project.main_schema.relative_to(REPO_ROOT).as_posix()


# --- snippets validated against the JSON Schema generated in the same run ---------------------------------------------


def _mini_project_with_spec(tmp_path: Path, sensor: dict[str, object]) -> Path:
    """A copy of the mini project whose spec validates one sensor snippet against the run's generated JSON Schema."""
    root = tmp_path / "mini-project"
    shutil.copytree(MINI_PROJECT, root)
    snippets = root / "spec" / "snippets"
    snippets.mkdir(parents=True)
    (snippets / "_snippets.yaml").write_text(
        yaml.safe_dump({"default_schema": "td", "snippets": {"sensor": {}}}), encoding="utf-8"
    )
    (snippets / "sensor.json").write_text(json.dumps(sensor), encoding="utf-8")
    (root / "spec" / "glossary.yaml").write_text(yaml.safe_dump({"terms": {}}), encoding="utf-8")
    (root / "spec" / "template.html").write_text(
        "<section id='sec-sensor'>%section('sec-sensor')%</section>\n", encoding="utf-8"
    )
    manifest = root / "wot-toolchain.yaml"
    document = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    document["spec"] = {
        "template": "spec/template.html",
        "output": "spec-out/index.html",
        "vocab_id_prefix": "sen",
        "sections": [{"id": "sec-sensor", "schema": "schemas/sensor.yaml"}],
        "snippets": "spec/snippets",
        "glossary": "spec/glossary.yaml",
        "snippet_validation_schemas": {"td": {"generated": "jsonschema"}},
    }
    manifest.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return manifest


def test_generated_validation_schema_requires_the_jsonschema_generator_in_the_run(tmp_path: Path) -> None:
    manifest = _mini_project_with_spec(tmp_path, {"serialNumber": "S-1"})
    project = dataclasses.replace(load_project(manifest), generators=("jsonldcontext",), output_dir=tmp_path / "out")

    with pytest.raises(ManifestError) as excinfo:
        run_pipeline(project, generate_docs=True)

    message = str(excinfo.value)
    assert str(manifest) in message
    assert "spec.snippet_validation_schemas.td" in message
    assert "'jsonschema'" in message
    assert "--only" in message
    assert not project.output_dir.exists()


def test_only_without_jsonschema_rejects_a_generated_validation_schema(tmp_path: Path) -> None:
    manifest = _mini_project_with_spec(tmp_path, {"serialNumber": "S-1"})

    result = _generate(tmp_path, "-c", str(manifest), "-d", "--only", "jsonldcontext", "--output-dir", "out")

    assert result.returncode == 1, result.stderr
    assert "spec.snippet_validation_schemas.td" in result.stderr
    assert not (tmp_path / "out").exists()


def test_snippets_pass_against_the_schema_generated_in_this_run(tmp_path: Path) -> None:
    manifest = _mini_project_with_spec(tmp_path, {"serialNumber": "S-1", "readings": [{"measuredValue": 1.5}]})
    project = dataclasses.replace(load_project(manifest), output_dir=tmp_path / "out")

    run_pipeline(project, generate_docs=True)

    assert project.spec is not None
    assert project.spec.output.is_file()


def test_snippets_fail_against_the_schema_generated_in_this_run(tmp_path: Path) -> None:
    # Only the generated schema knows that serialNumber is required; the output directory is not the manifest's.
    manifest = _mini_project_with_spec(tmp_path, {"unit": "K"})
    project = dataclasses.replace(load_project(manifest), output_dir=tmp_path / "out")

    with pytest.raises(GenerationError, match=r"sensor\.json: \(root\) — 'serialNumber' is a required property"):
        run_pipeline(project, generate_docs=True)

    assert (tmp_path / "out" / "jsonschema" / "jsonschema.json").is_file()
    assert not (manifest.parent / "gens").exists()

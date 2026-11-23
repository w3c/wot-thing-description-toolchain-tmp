"""The CLI and the pipeline take every project-specific setting from the project config file."""

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
from wot_toolchain.errors import ConfigError, GenerationError
from wot_toolchain.pipeline import run_pipeline

REPO_ROOT = Path(__file__).resolve().parent.parent
REPO_CONFIG = REPO_ROOT / "wot-toolchain.yaml"
MINI_PROJECT = Path(__file__).resolve().parent / "fixtures" / "mini-project"
CLI_BIN = Path(sys.executable).parent / "wot-toolchain"


def _generate(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(CLI_BIN), "generate-wot-resources", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


@pytest.fixture
def specless_config(tmp_path: Path) -> Path:
    """A config file without a ``spec`` section that reuses the repository schemas and writes below ``tmp_path``."""
    document = yaml.safe_load(REPO_CONFIG.read_text(encoding="utf-8"))
    del document["generators"]["spec"]
    document["root_schema"] = str(REPO_ROOT / document["root_schema"])
    document["output_dir"] = str(tmp_path / "out")
    for vocabulary in document["vocabularies"]:
        vocabulary["schema"] = str(REPO_ROOT / vocabulary["schema"])
    config = tmp_path / "specless.yaml"
    config.write_text(yaml.safe_dump(document), encoding="utf-8")
    return config


def test_missing_config_exits_one_and_names_it(tmp_path: Path) -> None:
    result = _generate(tmp_path, "-c", "missing.yaml")
    assert result.returncode == 1, result.stderr
    assert str(tmp_path.resolve() / "missing.yaml") in result.stderr


def test_default_config_is_read_from_the_working_directory(tmp_path: Path) -> None:
    result = _generate(tmp_path)
    assert result.returncode == 1, result.stderr
    assert str(tmp_path.resolve() / "wot-toolchain.yaml") in result.stderr


def test_input_schema_overrides_root_schema(tmp_path: Path, specless_config: Path) -> None:
    broken = tmp_path / "broken.yaml"
    broken.write_text("classes: [unclosed\n", encoding="utf-8")
    result = _generate(tmp_path, "-c", str(specless_config), "-i", str(broken))
    assert result.returncode == 1, result.stderr
    assert str(broken.resolve()) in result.stderr


@pytest.fixture
def repo_project(tmp_path: Path) -> Project:
    """The repository project, redirected to write below ``tmp_path``."""
    return dataclasses.replace(load_project(REPO_CONFIG), output_dir=tmp_path / "out")


def test_run_pipeline_writes_one_artifact_per_declared_module(repo_project: Project) -> None:
    project = dataclasses.replace(repo_project, generators=("owl", "jsonldcontext"))
    run_pipeline(project)

    out = project.output_dir
    assert sorted(path.name for path in out.iterdir()) == ["jsonldcontext", "owl"]
    ontologies = {file_name for vocabulary in project.vocabularies for file_name in vocabulary.ontology}
    contexts = {vocabulary.context for vocabulary in project.vocabularies if vocabulary.context}
    assert {path.name for path in (out / "owl").iterdir()} == ontologies
    assert {path.name for path in (out / "jsonldcontext").iterdir()} == contexts | {"context.jsonld"}


def test_ontology_file_that_is_not_turtle_is_rejected(repo_project: Project) -> None:
    first, *rest = repo_project.vocabularies
    vocabularies = (dataclasses.replace(first, ontology=("td.nt",)), *rest)
    project = dataclasses.replace(repo_project, generators=("owl",), vocabularies=vocabularies)

    with pytest.raises(GenerationError) as excinfo:
        run_pipeline(project)

    assert str(excinfo.value) == (
        f"Could not generate the ontology td.nt from {first.schema}: only the Turtle serialization (.ttl) is supported."
    )


def test_merged_context_does_not_depend_on_module_order(repo_project: Project, tmp_path: Path) -> None:
    forward = dataclasses.replace(repo_project, generators=("jsonldcontext",), output_dir=tmp_path / "forward")
    backward = dataclasses.replace(
        forward, vocabularies=tuple(reversed(forward.vocabularies)), output_dir=tmp_path / "backward"
    )
    run_pipeline(forward)
    run_pipeline(backward)

    merged = Path("jsonldcontext") / "context.jsonld"
    assert (forward.output_dir / merged).read_bytes() == (backward.output_dir / merged).read_bytes()


def test_linkml_source_file_is_relative_to_the_config(repo_project: Project) -> None:
    project = dataclasses.replace(repo_project, generators=("linkml",))
    run_pipeline(project)

    document = yaml.safe_load((project.output_dir / "linkml" / "linkml.yaml").read_text(encoding="utf-8"))
    assert document["source_file"] == project.root_schema.relative_to(REPO_ROOT).as_posix()


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
    config = root / "wot-toolchain.yaml"
    document = yaml.safe_load(config.read_text(encoding="utf-8"))
    document["generators"]["spec"] = {
        "template": "spec/template.html",
        "output": "spec-out/index.html",
        "vocab_id_prefix": "sen",
        "sections": [{"id": "sec-sensor", "schema": "schemas/sensor.yaml"}],
        "snippets": "spec/snippets",
        "glossary": "spec/glossary.yaml",
        "snippet_validation_schemas": {"td": {"generated": "jsonschema"}},
    }
    config.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return config


def test_spec_is_built_only_when_it_is_a_generator_of_the_run(tmp_path: Path) -> None:
    config = _mini_project_with_spec(tmp_path, {"serialNumber": "S-1"})
    project = dataclasses.replace(load_project(config), output_dir=tmp_path / "out")
    assert project.spec is not None

    run_pipeline(dataclasses.replace(project, generators=("jsonschema",)))
    assert not project.spec.output.exists()

    run_pipeline(dataclasses.replace(project, generators=("jsonschema", "spec")))
    assert project.spec.output.is_file()


def test_generated_validation_schema_requires_the_jsonschema_generator_in_the_run(tmp_path: Path) -> None:
    config = _mini_project_with_spec(tmp_path, {"serialNumber": "S-1"})
    project = dataclasses.replace(
        load_project(config), generators=("jsonldcontext", "spec"), output_dir=tmp_path / "out"
    )

    with pytest.raises(ConfigError) as excinfo:
        run_pipeline(project)

    message = str(excinfo.value)
    assert str(config) in message
    assert "generators.spec.snippet_validation_schemas.td" in message
    assert "'jsonschema'" in message
    assert "--only" in message
    assert not project.output_dir.exists()


def test_only_without_jsonschema_rejects_a_generated_validation_schema(tmp_path: Path) -> None:
    config = _mini_project_with_spec(tmp_path, {"serialNumber": "S-1"})

    result = _generate(tmp_path, "-c", str(config), "--only", "jsonldcontext", "--only", "spec", "--output-dir", "out")

    assert result.returncode == 1, result.stderr
    assert "generators.spec.snippet_validation_schemas.td" in result.stderr
    assert not (tmp_path / "out").exists()


def test_snippets_pass_against_the_schema_generated_in_this_run(tmp_path: Path) -> None:
    config = _mini_project_with_spec(tmp_path, {"serialNumber": "S-1", "readings": [{"measuredValue": 1.5}]})
    project = dataclasses.replace(load_project(config), output_dir=tmp_path / "out")

    run_pipeline(project)

    assert project.spec is not None
    assert project.spec.output.is_file()


def test_snippets_fail_against_the_schema_generated_in_this_run(tmp_path: Path) -> None:
    # Only the generated schema knows that serialNumber is required; the output directory is not the config file's.
    config = _mini_project_with_spec(tmp_path, {"unit": "K"})
    project = dataclasses.replace(load_project(config), output_dir=tmp_path / "out")

    with pytest.raises(GenerationError, match=r"sensor\.json: \(root\) — 'serialNumber' is a required property"):
        run_pipeline(project)

    assert (tmp_path / "out" / "jsonschema" / "jsonschema.json").is_file()
    assert not (config.parent / "gens").exists()

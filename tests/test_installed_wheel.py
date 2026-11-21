"""Acceptance test: the built wheel, installed into a fresh environment, generates the release artifacts.

Nothing from the repository checkout is importable in that environment, so a missing package asset, an
undeclared dependency or a path resolved against the source tree or the working directory makes it fail.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON_VERSION = "3.14"


@dataclass(frozen=True)
class Generation:
    """One run of the installed CLI on a private copy of the repository project."""

    project: Path
    working_dir: Path
    manifest: dict[str, Any]
    output_dir: Path
    result: subprocess.CompletedProcess[str]


def _run(command: list[str], cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    assert result.returncode == 0, f"{' '.join(command)} failed:\n{result.stdout}\n{result.stderr}"


@pytest.fixture(scope="session")
def installed_venv(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A fresh virtual environment with only the built wheel and its declared dependencies installed."""
    dist = tmp_path_factory.mktemp("dist")
    _run(["uv", "build", "--wheel", "--out-dir", str(dist)], cwd=REPO_ROOT)
    (wheel,) = dist.glob("wot_toolchain-*.whl")
    venv = tmp_path_factory.mktemp("venv") / "env"
    scratch = tmp_path_factory.mktemp("install-cwd")
    _run(["uv", "venv", "--python", PYTHON_VERSION, str(venv)], cwd=scratch)
    _run(["uv", "pip", "install", "--python", str(venv / "bin" / "python"), str(wheel)], cwd=scratch)
    return venv


@pytest.fixture(scope="session")
def generation(installed_venv: Path, tmp_path_factory: pytest.TempPathFactory) -> Generation:
    """The installed CLI run with all manifest generators and the specification, from an unrelated directory."""
    project = tmp_path_factory.mktemp("project")
    shutil.copy2(REPO_ROOT / "wot-toolchain.yaml", project / "wot-toolchain.yaml")
    shutil.copytree(REPO_ROOT / "resources", project / "resources", ignore=shutil.ignore_patterns("gens"))
    elsewhere = tmp_path_factory.mktemp("elsewhere")
    output_dir = tmp_path_factory.mktemp("generated") / "out"
    venv_bin = installed_venv / "bin"
    result = subprocess.run(
        [
            str(venv_bin / "wot-toolchain"),
            "generate-wot-resources",
            "-c",
            str(project / "wot-toolchain.yaml"),
            "--output-dir",
            str(output_dir),
            "-d",
        ],
        cwd=elsewhere,
        env={**os.environ, "PATH": _path_without_the_environment()},
        capture_output=True,
        text=True,
        check=False,
    )
    manifest = yaml.safe_load((project / "wot-toolchain.yaml").read_text(encoding="utf-8"))
    return Generation(project=project, working_dir=elsewhere, manifest=manifest, output_dir=output_dir, result=result)


def _path_without_the_environment() -> str:
    # Like `uv tool install`: only the entry point is exposed, the environment's bin directory is not on PATH.
    # bikeshed must therefore be found among the wheel's own dependencies. Graphviz is a system tool.
    dot = shutil.which("dot")
    assert dot is not None, "Graphviz 'dot' must be installed for the visualization generator"
    return str(Path(dot).parent)


def _assert_non_empty_file(path: Path) -> None:
    assert path.is_file(), f"{path} was not generated"
    assert path.stat().st_size > 0, f"{path} is empty"


def test_bikeshed_is_installed_with_the_wheel(installed_venv: Path) -> None:
    assert (installed_venv / "bin" / "bikeshed").is_file()


def test_installed_cli_exits_zero(generation: Generation) -> None:
    assert generation.result.returncode == 0, generation.result.stderr


def test_json_schema_is_generated(generation: Generation) -> None:
    path = generation.output_dir / "jsonschema" / "jsonschema.json"
    _assert_non_empty_file(path)
    assert json.loads(path.read_text(encoding="utf-8"))["properties"]


def test_merged_json_ld_context_is_generated(generation: Generation) -> None:
    path = generation.output_dir / "jsonldcontext" / "context.jsonld"
    _assert_non_empty_file(path)
    assert json.loads(path.read_text(encoding="utf-8"))["@context"]


def test_every_module_json_ld_context_is_generated(generation: Generation) -> None:
    contexts = [module["context"] for module in generation.manifest["modules"] if "context" in module]
    assert contexts
    for name in contexts:
        path = generation.output_dir / "jsonldcontext" / name
        _assert_non_empty_file(path)
        assert json.loads(path.read_text(encoding="utf-8"))["@context"], name


def test_every_module_ontology_is_generated(generation: Generation) -> None:
    ontologies = [module["ontology"] for module in generation.manifest["modules"] if "ontology" in module]
    assert ontologies
    for name in ontologies:
        _assert_non_empty_file(generation.output_dir / "owl" / name)


def test_shacl_shapes_are_generated(generation: Generation) -> None:
    _assert_non_empty_file(generation.output_dir / "shacl" / "shapes.shacl.ttl")


def test_every_module_diagram_is_generated(generation: Generation) -> None:
    diagrams = [module["diagram"] for module in generation.manifest["modules"] if "diagram" in module]
    assert diagrams
    for name in diagrams:
        _assert_non_empty_file(generation.output_dir / "visualization" / name)


def test_specification_html_is_generated(generation: Generation) -> None:
    # The spec paths come from the manifest and are resolved against its directory, not against --output-dir.
    path = generation.project / generation.manifest["spec"]["output"]
    _assert_non_empty_file(path)
    # An assertion id that only exists in thing_description.yaml proves the schema content reached the spec.
    assert 'id="td-context-ns-thing-mandatory"' in path.read_text(encoding="utf-8")


def test_assertions_csv_is_generated(generation: Generation) -> None:
    path = generation.project / generation.manifest["spec"]["assertions_csv"]
    _assert_non_empty_file(path)
    rows = path.read_text(encoding="utf-8").splitlines()
    assert rows[0] == '"ID","Status","Assertion"'
    assert len(rows) > 1


def test_nothing_is_written_to_the_working_directory(generation: Generation) -> None:
    assert list(generation.working_dir.iterdir()) == []

"""Options of ``generate-wot-resources`` that let another repository drive the toolchain."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner, Result

from wot_toolchain import cli
from wot_toolchain.config import Project

REPO_ROOT = Path(__file__).resolve().parent.parent
REPO_MANIFEST = REPO_ROOT / "wot-toolchain.yaml"
CLI_BIN = Path(sys.executable).parent / "wot-toolchain"
MANIFEST_GENERATORS = "jsonschema, shacl, jsonldcontext, owl, linkml, visualization"


@pytest.fixture(autouse=True)
def _restore_root_log_level() -> Iterator[None]:
    root = logging.getLogger()
    previous = root.level
    yield
    root.setLevel(previous)


@pytest.fixture
def recorded_runs(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Replace the pipeline with a recorder so option handling is observed without generating anything."""
    runs: list[dict[str, Any]] = []

    def record(project: Project, *, generate_docs: bool = False) -> None:
        runs.append({"project": project, "generate_docs": generate_docs})

    monkeypatch.setattr(cli, "run_pipeline", record)
    return runs


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A private copy of the project manifest and the input resources, without generated output."""
    root = tmp_path / "project"
    root.mkdir()
    shutil.copy2(REPO_MANIFEST, root / "wot-toolchain.yaml")
    shutil.copytree(REPO_ROOT / "resources", root / "resources", ignore=shutil.ignore_patterns("gens"))
    return root


def _specless_manifest(tmp_path: Path, *, generators: list[str] | None = None, diagrams: bool = True) -> Path:
    """A manifest without a spec section that reuses the repository schemas through absolute paths."""
    document = yaml.safe_load(REPO_MANIFEST.read_text(encoding="utf-8"))
    del document["spec"]
    document["main_schema"] = str(REPO_ROOT / document["main_schema"])
    document["output_dir"] = str(tmp_path / "manifest-out")
    if generators is not None:
        document["generators"] = generators
    for module in document["modules"]:
        module["schema"] = str(REPO_ROOT / module["schema"])
        if not diagrams:
            module.pop("diagram", None)
    manifest = tmp_path / "specless.yaml"
    manifest.write_text(yaml.safe_dump(document), encoding="utf-8")
    return manifest


def _invoke(*args: str | Path) -> Result:
    return CliRunner().invoke(cli.main, ["generate-wot-resources", *map(str, args)])


def test_output_dir_is_resolved_against_the_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, recorded_runs: list[dict[str, Any]]
) -> None:
    monkeypatch.chdir(tmp_path)
    result = _invoke("-c", REPO_MANIFEST, "--output-dir", "out")
    assert result.exit_code == 0, result.output
    assert recorded_runs[0]["project"].output_dir == tmp_path.resolve() / "out"


def test_only_runs_the_named_generators_in_manifest_order(recorded_runs: list[dict[str, Any]]) -> None:
    result = _invoke("-c", REPO_MANIFEST, "--only", "linkml", "--only", "jsonschema")
    assert result.exit_code == 0, result.output
    assert recorded_runs[0]["project"].generators == ("jsonschema", "linkml")


def test_only_leaves_spec_generation_to_the_docs_flag(recorded_runs: list[dict[str, Any]]) -> None:
    result = _invoke("-c", REPO_MANIFEST, "--only", "linkml", "-d")
    assert result.exit_code == 0, result.output
    assert recorded_runs[0]["generate_docs"] is True


def test_only_rejects_an_unknown_generator_naming_the_choices(recorded_runs: list[dict[str, Any]]) -> None:
    result = _invoke("-c", REPO_MANIFEST, "--only", "nope")
    assert result.exit_code == 2, result.output
    assert "'nope'" in result.output
    assert MANIFEST_GENERATORS in result.output
    assert recorded_runs == []


def test_only_rejects_a_generator_the_manifest_does_not_list(
    tmp_path: Path, recorded_runs: list[dict[str, Any]]
) -> None:
    manifest = _specless_manifest(tmp_path, generators=["jsonschema", "linkml"])
    result = _invoke("-c", manifest, "--only", "visualization")
    assert result.exit_code == 2, result.output
    assert "'visualization'" in result.output
    assert "jsonschema, linkml" in result.output
    assert recorded_runs == []


def test_missing_bikeshed_fails_before_any_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    # A None entry in sys.modules is how Python marks a module as not importable.
    monkeypatch.setitem(sys.modules, "bikeshed", None)
    out = tmp_path / "out"
    result = _invoke("-c", REPO_MANIFEST, "-d", "--only", "linkml", "--output-dir", out)
    assert result.exit_code == 1, result.output
    assert "bikeshed" in caplog.text
    assert "specification" in caplog.text
    assert not out.exists()


def test_missing_dot_fails_before_any_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("PATH", str(tmp_path / "empty-bin"))
    out = tmp_path / "out"
    result = _invoke("-c", REPO_MANIFEST, "--only", "linkml", "--only", "visualization", "--output-dir", out)
    assert result.exit_code == 1, result.output
    assert "'dot'" in caplog.text
    assert "diagram" in caplog.text
    assert not out.exists()


def test_dot_is_not_required_when_no_module_declares_a_diagram(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = _specless_manifest(tmp_path, diagrams=False)
    monkeypatch.setenv("PATH", str(tmp_path / "empty-bin"))
    result = _invoke("-c", manifest, "--only", "visualization", "--output-dir", tmp_path / "out")
    assert result.exit_code == 0, result.output


def test_external_repository_generates_one_artifact_into_its_own_directory(project: Path, tmp_path: Path) -> None:
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    # No bikeshed or dot on PATH: neither is needed when only the linkml generator runs.
    env = {**os.environ, "PATH": str(tmp_path / "empty-bin")}
    result = subprocess.run(
        [
            str(CLI_BIN),
            "generate-wot-resources",
            "-c",
            str(project / "wot-toolchain.yaml"),
            "--only",
            "linkml",
            "--output-dir",
            "out",
        ],
        cwd=elsewhere,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert sorted(path.name for path in (elsewhere / "out").iterdir()) == ["linkml"]
    assert (elsewhere / "out" / "linkml" / "linkml.yaml").is_file()
    assert not (project / "resources" / "gens").exists()

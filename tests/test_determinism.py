"""Generating the same project twice yields byte-identical release artifacts.

Release artifacts are the JSON Schema, the JSON-LD contexts, the specification HTML and the assertions CSV.
OWL, SHACL and the diagrams are experimental and not compared. Each run is a separate process, so hash
randomisation differs between runs and set-ordering leaks into the output are caught.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from wot_toolchain.config import Project, SpecConfig, load_project

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_BIN = Path(sys.executable).parent / "wot-toolchain"
RELEASE_GENERATORS = ("jsonschema", "jsonldcontext")


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """A private copy of the project config file and the input resources, without generated output."""
    shutil.copy2(REPO_ROOT / "wot-toolchain.yaml", tmp_path / "wot-toolchain.yaml")
    shutil.copytree(REPO_ROOT / "resources", tmp_path / "resources", ignore=shutil.ignore_patterns("gens"))
    return tmp_path


def _release_paths(project: Project) -> list[Path]:
    """Every release artifact file the run wrote: the release generators' files, the spec and the assertions CSV."""
    spec = _spec(project)
    assert spec.assertions_csv is not None
    generated: list[Path] = []
    for generator in RELEASE_GENERATORS:
        files = [path for path in (project.output_dir / generator).rglob("*") if path.is_file()]
        assert files, f"generator {generator!r} wrote no files below {project.output_dir}"
        generated.extend(files)
    return sorted([*generated, spec.output, spec.assertions_csv])


def _generate_release_artifacts(project_root: Path, project: Project) -> dict[str, bytes]:
    """Run the CLI with ``-d`` once, then collect and remove its release artifacts, keyed by relative path."""
    result = subprocess.run(
        [str(CLI_BIN), "generate-wot-resources"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    artifacts = {path.relative_to(project_root).as_posix(): path.read_bytes() for path in _release_paths(project)}
    _remove_outputs(project)
    return artifacts


def _remove_outputs(project: Project) -> None:
    """Delete everything a run wrote, so a file the next run fails to write cannot survive from this one."""
    for path in _release_paths(project):
        path.unlink()
    shutil.rmtree(project.output_dir)


def _spec(project: Project) -> SpecConfig:
    assert project.spec is not None
    return project.spec


def test_release_artifacts_are_byte_identical_across_runs(project_root: Path) -> None:
    project = load_project(project_root / "wot-toolchain.yaml")

    first = _generate_release_artifacts(project_root, project)
    second = _generate_release_artifacts(project_root, project)

    assert sorted(second) == sorted(first), "the two runs wrote different release artifact files"
    differing = sorted(name for name in first if first[name] != second[name])
    assert not differing, f"release artifacts differ between two runs: {', '.join(differing)}"

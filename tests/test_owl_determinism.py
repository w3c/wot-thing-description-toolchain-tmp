"""The OWL route (preprocess, gen-owl, post passes, serializer) writes identical text on every run."""

import os
import subprocess
import sys
from pathlib import Path

from wot_toolchain import pipeline
from wot_toolchain.config import load_project
from wot_toolchain.schema_utils import load_schema_view

CONFIG = Path(__file__).resolve().parent.parent / "wot-toolchain.yaml"

_GENERATE_IN_CHILD = """
import sys
from pathlib import Path
from wot_toolchain import pipeline
from wot_toolchain.config import load_project
from wot_toolchain.schema_utils import load_schema_view
project = load_project(Path(sys.argv[1]))
pipeline._gen_owl(project, load_schema_view(project.root_schema, merge_imports=True), Path(sys.argv[2]))
"""


def _read_outputs(output_dir: Path) -> dict[str, str]:
    """Return every file the OWL route wrote, keyed by file name."""
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(output_dir.iterdir())}


def _generate_in_process(output_dir: Path) -> dict[str, str]:
    """Run the pipeline's OWL route with a fresh schema view and fresh generators."""
    project = load_project(CONFIG)
    output_dir.mkdir()
    pipeline._gen_owl(project, load_schema_view(project.root_schema, merge_imports=True), output_dir)
    return _read_outputs(output_dir)


def _generate_in_subprocess(output_dir: Path, hash_seed: str) -> dict[str, str]:
    """Run the pipeline's OWL route in a new interpreter with the given ``PYTHONHASHSEED``."""
    output_dir.mkdir()
    env = {**os.environ, "PYTHONHASHSEED": hash_seed}
    result = subprocess.run(
        [sys.executable, "-c", _GENERATE_IN_CHILD, str(CONFIG), str(output_dir)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return _read_outputs(output_dir)


def _differing(first: dict[str, str], second: dict[str, str]) -> list[str]:
    """Return the names of files whose text differs between the two runs."""
    return sorted(name for name in first if first[name] != second.get(name))


def _expected_files() -> set[str]:
    """Return the ontology file names the config file asks for."""
    return {file_name for vocabulary in load_project(CONFIG).vocabularies for file_name in vocabulary.ontology}


def test_owl_route_is_identical_twice_in_one_process(tmp_path: Path) -> None:
    first = _generate_in_process(tmp_path / "first")
    second = _generate_in_process(tmp_path / "second")

    assert set(first) == _expected_files()
    assert set(second) == set(first)
    assert not _differing(first, second), f"OWL differs between two runs: {_differing(first, second)}"


def test_owl_route_is_identical_across_processes_with_different_hash_seeds(tmp_path: Path) -> None:
    first = _generate_in_subprocess(tmp_path / "seed-0", "0")
    second = _generate_in_subprocess(tmp_path / "seed-1", "1")

    assert set(first) == _expected_files()
    assert set(second) == set(first)
    assert not _differing(first, second), f"OWL differs between hash seeds: {_differing(first, second)}"

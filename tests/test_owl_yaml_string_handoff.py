"""The preprocessed schema reaches OwlSchemaGenerator as a YAML string, with output identical to a file."""

import tempfile
import warnings
from pathlib import Path
from typing import Any

import pytest
from linkml.generators.owlgen import OwlSchemaGenerator

from wot_toolchain import pipeline
from wot_toolchain.config import GEN_OWL_OPTIONS, load_project
from wot_toolchain.preprocessors.owl_preprocessor import preprocess_for_gen_owl

MANIFEST = Path(__file__).resolve().parent.parent / "wot-toolchain.yaml"


def _schema_path(prefix: str) -> Path:
    """Return the schema path of the module with ``prefix`` in the repository manifest."""
    return next(module.schema for module in load_project(MANIFEST).modules if module.prefix == prefix)


def _serialize(schema: str) -> str:
    """Return raw OWL from a fresh generator, since a second serialize() on one instance differs."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return OwlSchemaGenerator(schema, **GEN_OWL_OPTIONS).serialize()


@pytest.mark.parametrize("prefix", ["td", "hctl"])
def test_yaml_string_output_equals_temp_file_output(prefix: str, tmp_path: Path) -> None:
    """Raw gen-owl output from the YAML string equals output from the same YAML in a temp file."""
    yaml_str = preprocess_for_gen_owl(str(_schema_path(prefix)))
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", dir=tmp_path, delete=False) as f:
        f.write(yaml_str)
    assert _serialize(yaml_str) == _serialize(f.name)


def test_run_gen_owl_hands_over_yaml_string(monkeypatch: pytest.MonkeyPatch) -> None:
    """_run_gen_owl passes the preprocessed YAML itself, not a temp file path, to the generator."""
    received: list[object] = []

    def spy(schema: object, **kwargs: Any) -> OwlSchemaGenerator:
        received.append(schema)
        return OwlSchemaGenerator(schema, **kwargs)

    monkeypatch.setattr(pipeline, "OwlSchemaGenerator", spy)
    schema_path = _schema_path("hctl")
    pipeline._run_gen_owl(schema_path)
    assert received == [preprocess_for_gen_owl(str(schema_path))]

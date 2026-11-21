"""Tests for the artifact registry, the single source of artifact generator names and their callables."""

from pathlib import Path

import pytest

from wot_toolchain import pipeline
from wot_toolchain.artifacts.registry import Artifact, ArtifactRegistry, artifact_names
from wot_toolchain.config import load_project
from wot_toolchain.errors import ManifestError

# Captured from config.KNOWN_GENERATORS and pipeline._DISPATCH before the registry existed.
NAMES_BEFORE_REGISTRY = ("jsonschema", "shacl", "jsonldcontext", "owl", "linkml", "visualization")
CALLABLES_BEFORE_REGISTRY = {
    "jsonschema": "_gen_jsonschema",
    "shacl": "_gen_shacl",
    "owl": "_gen_owl",
    "jsonldcontext": "_gen_jsonldcontext",
    "linkml": "_gen_linkml",
    "visualization": "_gen_visualization",
}


def _noop(*_: object) -> None:
    return None


def test_artifact_names_are_the_known_generator_names_in_order() -> None:
    assert artifact_names() == NAMES_BEFORE_REGISTRY
    assert all(type(name) is str for name in artifact_names())


@pytest.mark.parametrize(("name", "function_name"), CALLABLES_BEFORE_REGISTRY.items())
def test_pipeline_registry_returns_the_generator_function_run_today(name: str, function_name: str) -> None:
    assert pipeline.ARTIFACT_REGISTRY.generator(name) is getattr(pipeline, function_name)


def test_pipeline_registry_raises_key_error_for_unknown_name() -> None:
    with pytest.raises(KeyError) as excinfo:
        pipeline.ARTIFACT_REGISTRY.generator("bogus")
    assert excinfo.value.args == ("bogus",)


def test_config_validation_and_pipeline_dispatch_accept_the_same_names() -> None:
    assert set(pipeline.ARTIFACT_REGISTRY.generators) == set(artifact_names())


def test_registry_rejects_missing_generator() -> None:
    generators = {name: _noop for name in artifact_names() if name != Artifact.OWL}
    with pytest.raises(ValueError, match="'owl'"):
        ArtifactRegistry(generators)


def test_registry_rejects_unknown_generator() -> None:
    generators = {**dict.fromkeys(artifact_names(), _noop), "pdf": _noop}
    with pytest.raises(ValueError, match="'pdf'"):
        ArtifactRegistry(generators)


def test_manifest_with_unknown_generator_reports_the_registered_names(tmp_path: Path) -> None:
    (tmp_path / "main.yaml").write_text("", encoding="utf-8")
    manifest = tmp_path / "wot-toolchain.yaml"
    manifest.write_text(
        "main_schema: main.yaml\noutput_dir: out\ngenerators: [pdf]\nmodules: [{schema: main.yaml, prefix: m}]\n",
        encoding="utf-8",
    )
    with pytest.raises(ManifestError) as excinfo:
        load_project(manifest)
    assert str(excinfo.value) == (
        f"{manifest.resolve()}: generators[0]: unknown generator 'pdf'. "
        "Use one of: jsonschema, shacl, jsonldcontext, owl, linkml, visualization."
    )

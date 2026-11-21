"""The snippet manifest, not the snippet content, picks the JSON Schema each snippet is validated against."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from wot_toolchain.errors import GenerationError
from wot_toolchain.specgen.snippets import validate_all_snippets

REQUIRES_NAME = {"type": "object", "required": ["name"]}
ACCEPTS_ALL: dict[str, object] = {}


def _write_schemas(tmp_path: Path) -> dict[str, Path]:
    schemas = {}
    for kind, schema in (("strict", REQUIRES_NAME), ("loose", ACCEPTS_ALL)):
        path = tmp_path / f"{kind}.json"
        path.write_text(json.dumps(schema), encoding="utf-8")
        schemas[kind] = path
    return schemas


def _write_snippets(tmp_path: Path, manifest: dict[str, object]) -> Path:
    snippets_dir = tmp_path / "snippets"
    snippets_dir.mkdir()
    (snippets_dir / "_snippets.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    (snippets_dir / "nameless.json").write_text(json.dumps({"title": "x"}), encoding="utf-8")
    return snippets_dir


def test_default_schema_selects_the_validator(tmp_path: Path) -> None:
    snippets_dir = _write_snippets(tmp_path, {"default_schema": "strict", "snippets": {"nameless": {}}})

    errors = validate_all_snippets(snippets_dir, _write_schemas(tmp_path))

    assert len(errors) == 1
    assert errors[0].startswith("nameless.json: (root) — 'name' is a required property")


def test_snippet_schema_overrides_default_schema(tmp_path: Path) -> None:
    manifest = {"default_schema": "strict", "snippets": {"nameless": {"schema": "loose"}}}
    snippets_dir = _write_snippets(tmp_path, manifest)

    assert validate_all_snippets(snippets_dir, _write_schemas(tmp_path)) == []


def test_snippet_schema_works_without_default_schema(tmp_path: Path) -> None:
    snippets_dir = _write_snippets(tmp_path, {"snippets": {"nameless": {"schema": "strict"}}})

    errors = validate_all_snippets(snippets_dir, _write_schemas(tmp_path))

    assert len(errors) == 1


def test_snippet_without_schema_and_without_default_schema_is_rejected(tmp_path: Path) -> None:
    snippets_dir = _write_snippets(tmp_path, {"snippets": {"nameless": {}}})

    with pytest.raises(GenerationError) as excinfo:
        validate_all_snippets(snippets_dir, _write_schemas(tmp_path))

    message = str(excinfo.value)
    assert str(snippets_dir / "_snippets.yaml") in message
    assert "snippets.nameless" in message
    assert "'default_schema'" in message
    assert "'schema'" in message


def test_unconfigured_schema_kind_is_rejected(tmp_path: Path) -> None:
    snippets_dir = _write_snippets(tmp_path, {"default_schema": "absent", "snippets": {"nameless": {}}})

    with pytest.raises(GenerationError) as excinfo:
        validate_all_snippets(snippets_dir, _write_schemas(tmp_path))

    message = str(excinfo.value)
    assert "nameless.json" in message
    assert "'absent'" in message
    assert "spec.snippet_validation_schemas" in message


def test_non_string_schema_kind_is_rejected(tmp_path: Path) -> None:
    snippets_dir = _write_snippets(tmp_path, {"snippets": {"nameless": {"schema": ["strict"]}}})

    with pytest.raises(GenerationError) as excinfo:
        validate_all_snippets(snippets_dir, _write_schemas(tmp_path))

    message = str(excinfo.value)
    assert str(snippets_dir / "_snippets.yaml") in message
    assert "snippets.nameless.schema" in message


def test_unvalidated_snippet_needs_no_schema_kind(tmp_path: Path) -> None:
    snippets_dir = _write_snippets(tmp_path, {"snippets": {"nameless": {"validate": False}}})

    assert validate_all_snippets(snippets_dir, _write_schemas(tmp_path)) == []

"""Validate _snippets.yaml manifest against the LinkML snippet schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft7Validator

REPO_ROOT = Path(__file__).resolve().parent.parent
SNIPPET_SCHEMA = REPO_ROOT / "resources" / "schemas" / "snippet_schema.yaml"
MANIFEST_PATH = REPO_ROOT / "resources" / "snippets" / "_snippets.yaml"


def _generate_json_schema() -> dict:
    from linkml.generators.jsonschemagen import JsonSchemaGenerator

    gen = JsonSchemaGenerator(str(SNIPPET_SCHEMA))
    raw = gen.serialize()
    return json.loads(raw)


@pytest.fixture(scope="module")
def manifest_validator() -> Draft7Validator:
    schema = _generate_json_schema()
    return Draft7Validator(schema)


@pytest.fixture(scope="module")
def manifest() -> dict:
    return yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_manifest_valid(manifest: dict, manifest_validator: Draft7Validator):
    errors = list(manifest_validator.iter_errors(manifest))
    assert not errors, (
        f"Manifest validation errors:\n"
        + "\n".join(f"  {e.json_path}: {e.message}" for e in errors)
    )


def test_hide_show_mutually_exclusive(manifest: dict):
    """No snippet should have both hide_paths and show_paths."""
    violations = [
        name for name, meta in manifest.get("snippets", {}).items()
        if meta.get("hide_paths") and meta.get("show_paths")
    ]
    assert not violations, (
        f"Snippets with both hide_paths and show_paths: {', '.join(violations)}"
    )


def test_snippet_json_files_exist(manifest: dict):
    """Every snippet in manifest must have a corresponding .json file."""
    snippets_dir = MANIFEST_PATH.parent
    missing = [
        name for name in manifest.get("snippets", {})
        if not (snippets_dir / f"{name}.json").exists()
    ]
    assert not missing, f"Missing .json files: {', '.join(missing)}"


def test_group_snippet_refs_exist(manifest: dict):
    """All snippet references in groups must exist in the snippets section."""
    snippet_names = set(manifest.get("snippets", {}).keys())
    errors = []
    for gname, group in manifest.get("groups", {}).items():
        for field in ("compact", "expanded"):
            ref = group.get(field)
            if ref and ref not in snippet_names:
                errors.append(f"{gname}.{field}: '{ref}' not in snippets")
        for tab in group.get("tabs", []):
            ref = tab.get("snippet")
            if ref and ref not in snippet_names:
                errors.append(f"{gname}.tabs: '{ref}' not in snippets")
    assert not errors, "Broken group references:\n" + "\n".join(f"  {e}" for e in errors)

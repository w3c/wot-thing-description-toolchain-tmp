"""Validate generated JSON Schema against valid and invalid TD samples."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import validators
from jsonschema.exceptions import best_match

from .rejections import defined_at, main_rejection, rejection_details

TESTS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = TESTS_DIR.parent
SCHEMA_PATH = REPO_ROOT / "resources" / "gens" / "jsonschema" / "jsonschema.json"
DATA_DIR = TESTS_DIR / "resources" / "td"


@pytest.fixture(scope="session")
def validator():
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Generated schema not found at {SCHEMA_PATH}; run `wot-toolchain generate-wot-resources` first.")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    cls = validators.validator_for(schema)
    cls.check_schema(schema)
    return cls(schema)


def _samples():
    return [
        pytest.param(path, id=path.relative_to(DATA_DIR).as_posix())
        for path in sorted(DATA_DIR.rglob("*.jsonld"))
    ]


@pytest.mark.parametrize("td_path", _samples())
def test_td_instance(validator, rejections, td_path: Path):
    verdict_dir = td_path.parent.name
    assert verdict_dir in ("valid", "invalid"), f"{td_path}: must be in a valid/ or invalid/ directory"
    expected_valid = verdict_dir == "valid"
    instance = json.loads(td_path.read_text(encoding="utf-8"))
    errors = list(validator.iter_errors(instance))
    if expected_valid:
        for _, spath, msg in rejection_details(errors):
            entry = rejections.setdefault(spath, {"count": 0, "example": msg})
            entry["count"] += 1
        error = best_match(errors)
        assert error is None, f"expected VALID but schema rejected {td_path.name}: {error and error.message}"
    else:
        assert errors, f"expected INVALID but schema accepted {td_path.name}"

"""Validate generated JSON Schema against valid and invalid TD samples."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import validators
from jsonschema.exceptions import best_match

from .baselines import TD_VERSIONS, as_td20
from .rejections import defined_at, main_rejection, rejection_details

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
SCHEMA_PATH = REPO_ROOT / "resources" / "gens" / "jsonschema" / "jsonschema.json"
DATA_DIR = TESTS_DIR / "data"


@pytest.fixture(scope="session")
def validator():
    if not SCHEMA_PATH.exists():
        pytest.skip(f"Generated schema not found at {SCHEMA_PATH}; run `wotis generate-wot-resources` first.")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    cls = validators.validator_for(schema)
    cls.check_schema(schema)
    return cls(schema)


def _samples():
    params = []
    for version in TD_VERSIONS:
        for path in sorted(DATA_DIR.rglob("*.jsonld")):
            sample = f"{version}/{path.relative_to(DATA_DIR).as_posix()}"
            params.append(pytest.param(path, version, id=sample))
    return params


@pytest.mark.parametrize("td_path, version", _samples())
def test_td_instance(validator, rejections, td_path: Path, version: str):
    expected_valid = "invalid" not in td_path.name.lower()
    instance = json.loads(td_path.read_text(encoding="utf-8"))
    if version == "td20":
        instance = as_td20(instance)
    errors = list(validator.iter_errors(instance))
    if expected_valid:
        sample = f"{version}/{td_path.relative_to(DATA_DIR).as_posix()}"
        for _, spath, msg in rejection_details(errors):
            entry = rejections.setdefault((version, spath), {"count": 0, "example": msg})
            entry["count"] += 1
        error = best_match(errors)
        assert error is None, f"expected VALID but schema rejected {td_path.name}: {error and error.message}"
    else:
        assert errors, f"expected INVALID but schema accepted {td_path.name}"

"""TD-instance gate.

The generated JSON Schema must accept every ``*-valid`` sample and reject every
``*-invalid`` one, for both TD 1.1 and TD 2.0. The samples on disk are the TD 1.1
ones; the TD 2.0 variant is derived per test by rewriting @context (as_td20 in
baselines.py). Valid samples the schema wrongly rejects (known fidelity gaps) are
listed in the known-failures file and marked xfail(strict): a fix that makes one
pass forces removing it there, so the list can only shrink.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import validators
from jsonschema.exceptions import best_match

from .baselines import TD_VERSIONS, as_td20, load_baseline
from .rejections import defined_at, main_rejection, rejection_details

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
SCHEMA_PATH = REPO_ROOT / "resources" / "gens" / "jsonschema" / "jsonschema.json"
DATA_DIR = TESTS_DIR / "data"
KNOWN_FAILURES = TESTS_DIR / "known_failures" / "td_gate.txt"


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
    known_failures = load_baseline(KNOWN_FAILURES)
    for version in TD_VERSIONS:
        for path in sorted(DATA_DIR.rglob("*.jsonld")):
            sample = f"{version}/{path.relative_to(DATA_DIR).as_posix()}"
            marks = [pytest.mark.xfail(strict=True, reason="known fidelity gap")] if sample in known_failures else []
            params.append(pytest.param(path, version, sample in known_failures, id=sample, marks=marks))
    return params


@pytest.mark.parametrize("td_path, version, baselined", _samples())
def test_td_instance(validator, rejections, new_failures, td_path: Path, version: str, baselined):
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
        if errors and not baselined:
            where, spath, msg = main_rejection(errors)
            src = defined_at(spath)
            schema_where = f"{spath}, defined at {src}" if src else spath
            new_failures.append(f"gate {sample}: at {where} (schema: {schema_where}): {msg}")
        error = best_match(errors)
        assert error is None, f"expected VALID but schema rejected {td_path.name}: {error and error.message}"
    else:
        assert errors, f"expected INVALID but schema accepted {td_path.name}"


def test_known_failures_are_valid_samples():
    known_failures = load_baseline(KNOWN_FAILURES)
    bad = sorted(p for p in known_failures if "invalid" in Path(p).name.lower())
    assert not bad, f"known-failures must list only valid samples, found: {bad}"


def test_known_failures_entries_resolve():
    known_failures = load_baseline(KNOWN_FAILURES)
    missing = sorted(
        p for p in known_failures
        if p.split("/", 1)[0] not in TD_VERSIONS or not (DATA_DIR / p.split("/", 1)[1]).exists()
    )
    assert not missing, f"known-failures entries do not match <version>/<existing sample>: {missing}"

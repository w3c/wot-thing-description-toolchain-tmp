"""Cross-check the generated schema against the W3C ground-truth schemas.

For every sample, the generated schema's accept/reject verdict must match the
ground-truth schema's. The samples on disk are the TD 1.1 ones; the TD 2.0
variant is derived per test by rewriting @context (as_td20 in baselines.py).
Known divergences are listed with a version prefix and marked xfail(strict),
so the list can only shrink.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
from jsonschema import validators

from .baselines import TD_VERSIONS, as_td20, load_baseline
from .rejections import defined_at, main_rejection

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
SCHEMA_PATH = REPO_ROOT / "resources" / "gens" / "jsonschema" / "jsonschema.json"
GROUND_TRUTH = REPO_ROOT / "resources" / "upstream" / "schemas"
DATA_DIR = TESTS_DIR / "data"
DIVERGENCES = TESTS_DIR / "known_failures" / "td_crosscheck.txt"

GROUND_TRUTH_SCHEMAS = {
    "td11": GROUND_TRUTH / "td11-json-schema-validation.json",
    "td20": GROUND_TRUTH / "td20-json-schema-validation.json",
}


def _make_validator(schema_path: Path):
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    cls = validators.validator_for(schema)
    cls.check_schema(schema)
    return cls(schema)


def _accepts(validator, instance) -> bool:
    try:
        validator.validate(instance)
        return True
    except jsonschema.ValidationError:
        return False


def _samples():
    params = []
    known = load_baseline(DIVERGENCES)
    for version in TD_VERSIONS:
        if not GROUND_TRUTH_SCHEMAS[version].exists():
            continue
        for path in sorted(DATA_DIR.rglob("*.jsonld")):
            sample = f"{version}/{path.relative_to(DATA_DIR).as_posix()}"
            marks = [pytest.mark.xfail(strict=True, reason="known divergence from W3C schema")] if sample in known else []
            params.append(pytest.param(path, version, sample in known, id=sample, marks=marks))
    return params


@pytest.fixture(scope="session")
def generated_validator():
    if not SCHEMA_PATH.exists():
        pytest.skip("Generated schema not found; run `wotis generate-wot-resources` first.")
    return _make_validator(SCHEMA_PATH)


@pytest.fixture(scope="session")
def golden_validators():
    cache: dict[str, object] = {}

    def get(version: str):
        if version not in cache:
            cache[version] = _make_validator(GROUND_TRUTH_SCHEMAS[version])
        return cache[version]

    return get


@pytest.mark.parametrize("td_path, version, baselined", _samples())
def test_generated_agrees_with_ground_truth(
    generated_validator, golden_validators, new_failures, td_path: Path, version: str, baselined
):
    instance = json.loads(td_path.read_text(encoding="utf-8"))
    if version == "td20":
        instance = as_td20(instance)
    gen_errors = list(generated_validator.iter_errors(instance))
    generated = not gen_errors
    golden = _accepts(golden_validators(version), instance)
    if generated != golden and not baselined:
        sample = f"{version}/{td_path.relative_to(DATA_DIR).as_posix()}"
        if golden:
            where, spath, msg = main_rejection(gen_errors)
            src = defined_at(spath)
            schema_where = f"{spath}, defined at {src}" if src else spath
            new_failures.append(
                f"crosscheck {sample}: generated rejects, W3C accepts: "
                f"at {where} (schema: {schema_where}): {msg}"
            )
        else:
            new_failures.append(f"crosscheck {sample}: generated accepts, W3C rejects")
    assert generated == golden, (
        f"verdict mismatch on {td_path.name}: "
        f"generated={'accept' if generated else 'reject'}, golden={'accept' if golden else 'reject'}"
    )

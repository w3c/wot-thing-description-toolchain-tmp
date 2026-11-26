"""Compare generated JSON Schema verdicts with the W3C td-next JSON Schema."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
import yaml
from jsonschema import validators


TESTS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = TESTS_DIR.parent
SCHEMA_PATH = REPO_ROOT / "resources" / "gens" / "jsonschema" / "jsonschema.json"
GROUND_TRUTH_PATH = REPO_ROOT / "resources" / "upstream" / "schemas" / "td20-json-schema-validation.json"
DATA_DIR = TESTS_DIR / "resources" / "td"
APPROVED_PATH = TESTS_DIR / "resources" / "approved_divergences" / "jsonschema.yaml"


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
    return [
        pytest.param(path, id=path.relative_to(DATA_DIR).as_posix())
        for path in sorted(DATA_DIR.rglob("*.jsonld"))
    ]


@pytest.fixture(scope="session")
def generated_validator():
    if not SCHEMA_PATH.exists():
        pytest.fail("Generated schema not found; run `wot-toolchain generate-wot-resources` first.")
    return _make_validator(SCHEMA_PATH)


@pytest.fixture(scope="session")
def golden_validator():
    return _make_validator(GROUND_TRUTH_PATH)


@pytest.fixture(scope="session")
def approved_verdicts() -> dict[str, str]:
    """Map each instance with an approved divergence from upstream to its expected generated verdict."""
    entries = yaml.safe_load(APPROVED_PATH.read_text(encoding="utf-8"))["divergences"]
    return {entry["upstream_locator"]["instance"]: entry["expected_generated"]["verdict"] for entry in entries}


def test_approved_divergences_name_existing_instances(approved_verdicts):
    missing = sorted(name for name in approved_verdicts if not (DATA_DIR / name).is_file())
    assert not missing, f"approved divergences without an instance: {missing}"


@pytest.mark.parametrize("td_path", _samples())
def test_generated_agrees_with_ground_truth(generated_validator, golden_validator, approved_verdicts, td_path: Path):
    instance = json.loads(td_path.read_text(encoding="utf-8"))
    gen_errors = list(generated_validator.iter_errors(instance))
    generated = not gen_errors
    golden = _accepts(golden_validator, instance)
    approved = approved_verdicts.get(td_path.relative_to(DATA_DIR).as_posix())
    if approved is not None:
        assert ("accept" if generated else "reject") == approved, (
            f"approved divergence on {td_path.name} no longer has its expected generated verdict '{approved}'"
        )
        assert generated != golden, f"approved divergence on {td_path.name} is stale because upstream now agrees"
        return
    assert generated == golden, (
        f"verdict mismatch on {td_path.name}: "
        f"generated={'accept' if generated else 'reject'}, golden={'accept' if golden else 'reject'}"
    )

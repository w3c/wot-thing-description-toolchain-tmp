"""The generated SHACL shapes accept every ``*-valid`` sample and reject every ``*-invalid`` one."""

import json
from pathlib import Path
from typing import Any

import pytest
from pyshacl import validate
from rdflib import SH, Graph

from .baselines import TD11_CONTEXT_URLS, load_baseline

TESTS_DIR = Path(__file__).resolve().parent
GENS_DIR = TESTS_DIR.parent / "resources" / "gens"
CONTEXT_PATH = GENS_DIR / "jsonldcontext" / "context.jsonld"
SHAPES_PATH = GENS_DIR / "shacl" / "shapes.shacl.ttl"
DATA_DIR = TESTS_DIR / "data"
KNOWN_FAILURES = TESTS_DIR / "known_failures" / "shacl_gate.txt"
BASE = "https://td.example.com/td.jsonld"
SAMPLE_METADATA_KEYS = ("$title", "$description")


@pytest.fixture(scope="session")
def generated_context() -> Any:
    if not CONTEXT_PATH.exists():
        pytest.skip(f"Generated context not found at {CONTEXT_PATH}; run `wot-toolchain generate-wot-resources`.")
    return json.loads(CONTEXT_PATH.read_text(encoding="utf-8"))["@context"]


@pytest.fixture(scope="session")
def shapes() -> Graph:
    if not SHAPES_PATH.exists():
        pytest.skip(f"Generated shapes not found at {SHAPES_PATH}; run `wot-toolchain generate-wot-resources`.")
    return Graph().parse(SHAPES_PATH, format="turtle")


def _with_generated_context(document: dict[str, Any], generated_context: Any) -> dict[str, Any]:
    """Return ``document`` without sample metadata and with the TD context URLs replaced by the generated context."""
    declared = document.get("@context", [])
    entries = declared if isinstance(declared, list) else [declared]
    localised: list[Any] = []
    for entry in entries:
        if isinstance(entry, str) and entry in TD11_CONTEXT_URLS:
            if generated_context not in localised:
                localised.append(generated_context)
        else:
            localised.append(entry)
    content = {key: value for key, value in document.items() if key not in SAMPLE_METADATA_KEYS}
    return {**content, "@context": localised}


def _violations(report: Graph) -> list[str]:
    lines = set()
    for result in report.subjects(SH.resultSeverity, SH.Violation):
        component = str(report.value(result, SH.sourceConstraintComponent)).rsplit("#", 1)[-1]
        lines.add(f"{component} on {report.value(result, SH.resultPath)} at {report.value(result, SH.focusNode)}")
    return sorted(lines)


def _samples() -> list[Any]:
    known_failures = load_baseline(KNOWN_FAILURES)
    params = []
    for path in sorted(DATA_DIR.rglob("*.jsonld")):
        sample = path.relative_to(DATA_DIR).as_posix()
        marks = [pytest.mark.xfail(strict=True, reason="known SHACL gap")] if sample in known_failures else []
        params.append(pytest.param(path, id=sample, marks=marks))
    return params


@pytest.mark.parametrize("td_path", _samples())
def test_td_instance_against_shapes(generated_context: Any, shapes: Graph, td_path: Path) -> None:
    expected_valid = "invalid" not in td_path.name.lower()
    document = _with_generated_context(json.loads(td_path.read_text(encoding="utf-8")), generated_context)
    data = Graph().parse(data=json.dumps(document), format="json-ld", base=BASE)

    conforms, report, _ = validate(data, shacl_graph=shapes, inference="none")

    if expected_valid:
        assert conforms, "\n".join(_violations(report)[:20])
    else:
        assert not conforms, "an invalid sample conforms to the shapes"

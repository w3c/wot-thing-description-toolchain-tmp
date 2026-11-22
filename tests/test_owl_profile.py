"""OWL 2 DL profile check of every generated ontology, via ROBOT ``validate-profile``."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

OWL_DIR = Path(__file__).resolve().parent.parent / "resources" / "gens" / "owl"
ONTOLOGIES = sorted(OWL_DIR.glob("*.ttl"))
REPORT_HEADER = "OWL 2 DL Profile Report:"
SHOWN_VIOLATIONS = 10
ROBOT_TIMEOUT_SECONDS = 300

KNOWN_DL_VIOLATIONS: dict[str, str] = {
    "hctl": "owl:ObjectProperty with xsd range (hctl:hasAnchor, hctl:hasAdditionalOutputSchema)",
    "wotsec": "owl:ObjectProperty with xsd range (wotsec:proxy, authorization, token, refresh, oneOf, allOf)",
}


def _robot_binary() -> str:
    """Return the ROBOT executable from ``ROBOT_BIN`` or PATH; skip locally, fail on CI when absent."""
    configured = os.environ.get("ROBOT_BIN")
    if configured:
        if not Path(configured).is_file():
            pytest.fail(f"ROBOT_BIN={configured!r} does not point to a file")
        return configured
    found = shutil.which("robot")
    if found:
        return found
    message = "ROBOT not found: set ROBOT_BIN or put 'robot' on PATH (http://robot.obolibrary.org, needs Java)"
    if os.environ.get("CI"):
        pytest.fail(message)
    pytest.skip(message)


def _case(ontology: Path) -> object:
    reason = KNOWN_DL_VIOLATIONS.get(ontology.stem)
    marks = [pytest.mark.xfail(strict=True, raises=AssertionError, reason=reason)] if reason else []
    return pytest.param(ontology, id=ontology.stem, marks=marks)


def test_ontologies_present() -> None:
    """The glob finds generated ontologies and every known-violation entry names one of them."""
    stems = {path.stem for path in ONTOLOGIES}
    assert stems, f"no generated ontologies in {OWL_DIR}"
    stale = set(KNOWN_DL_VIOLATIONS) - stems
    assert not stale, f"KNOWN_DL_VIOLATIONS entries without an ontology file: {sorted(stale)}"


@pytest.mark.parametrize("ontology", [_case(path) for path in ONTOLOGIES])
def test_owl2_dl_profile(ontology: Path, tmp_path: Path) -> None:
    """ROBOT reports the ontology inside the OWL 2 DL profile."""
    robot = _robot_binary()
    report = tmp_path / f"{ontology.stem}.dl-profile.txt"
    result = subprocess.run(
        [robot, "validate-profile", "--input", str(ontology), "--profile", "DL", "--output", str(report)],
        capture_output=True,
        text=True,
        timeout=ROBOT_TIMEOUT_SECONDS,
        check=False,
    )
    if not report.is_file() or not report.read_text(encoding="utf-8").startswith(REPORT_HEADER):
        pytest.fail(f"ROBOT produced no profile report (exit {result.returncode}):\n{result.stdout}\n{result.stderr}")
    violations = report.read_text(encoding="utf-8").splitlines()[1:]
    shown = "\n".join(line[:300] for line in violations[:SHOWN_VIOLATIONS])
    assert result.returncode == 0 and not violations, (
        f"{ontology.name}: {len(violations)} OWL 2 DL violations (exit {result.returncode}), first "
        f"{min(len(violations), SHOWN_VIOLATIONS)}:\n{shown}"
    )

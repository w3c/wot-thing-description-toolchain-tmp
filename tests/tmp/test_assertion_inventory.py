"""Compare the generated assertion inventory with the upstream inventory."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest
import yaml

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent
OUR_CSV = REPO_ROOT / "resources" / "gens" / "assertions" / "assertions.csv"
UPSTREAM_CSV = REPO_ROOT / "resources" / "upstream" / "assertions.csv"
APPROVED_DIVERGENCES = TESTS_DIR.parent / "approved_divergences" / "html.yaml"


def assertion_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return {row["ID"]: row for row in csv.DictReader(fh) if row.get("ID")}


def approved_assertion_divergences() -> dict[str, str]:
    with APPROVED_DIVERGENCES.open(encoding="utf-8") as divergence_file:
        divergences = yaml.safe_load(divergence_file)["divergences"]
    return {
        entry["upstream_locator"]["assertion_id"]: entry["expected_generated"]["text"]
        for entry in divergences
        if entry["upstream_locator"]["kind"] == "assertion"
    }


def test_assertion_ids_vs_upstream() -> None:
    if not OUR_CSV.exists():
        pytest.skip(f"Assertion CSV not found at {OUR_CSV}; run `wotis generate-wot-resources -d` first.")

    ours = assertion_rows(OUR_CSV)
    upstream = assertion_rows(UPSTREAM_CSV)
    assert ours, "our assertion inventory is empty"
    assert upstream, "upstream assertion inventory is empty"
    assert len(ours) == len(upstream), f"assertion count differs: {len(ours)} ours, {len(upstream)} upstream"

    missing = sorted(set(upstream) - set(ours))
    extra = sorted(set(ours) - set(upstream))
    assert not missing and not extra, (
        "assertion IDs differ from upstream:\n"
        f"  missing ({len(missing)}): {', '.join(missing) or '-'}\n"
        f"  extra ({len(extra)}): {', '.join(extra) or '-'}"
    )

    approved = approved_assertion_divergences()
    for assertion_id, expected_text in approved.items():
        assert assertion_id in ours, f"approved assertion divergence '{assertion_id}' is not generated"
        assert assertion_id in upstream, f"approved assertion divergence '{assertion_id}' is not upstream"
        assert ours[assertion_id]["Status"] == upstream[assertion_id]["Status"], (
            f"approved assertion divergence '{assertion_id}' changed status"
        )
        assert ours[assertion_id]["Assertion"] == expected_text, (
            f"approved assertion divergence '{assertion_id}' no longer has its expected correction"
        )
        assert upstream[assertion_id]["Assertion"] != expected_text, (
            f"approved assertion divergence '{assertion_id}' is stale because upstream now matches"
        )

    status_differences = [
        assertion_id
        for assertion_id in sorted(ours)
        if ours[assertion_id]["Status"] != upstream[assertion_id]["Status"]
    ]
    assert not status_differences, (
        "assertion status differences: "
        + ", ".join(status_differences)
    )

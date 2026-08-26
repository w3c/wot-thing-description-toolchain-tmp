"""Snapshot diff: the generated artifacts must match the committed snapshots
under tests/snapshots/. A snapshot is our own last output, so this says whether
the output changed without us noticing, not whether it is correct. If a change
is intended, update the snapshots with:

    uv run pytest tests/test_golden_diff.py --update-goldens
"""
from __future__ import annotations

import difflib
import json
import os
from pathlib import Path

import pytest

from .tmp.spec_html_compare import generated_sections_html

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
GOLDENS_DIR = TESTS_DIR / "snapshots"

def _normalize_json(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    return json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


# name, generated file, function that turns it into the compared text
ARTIFACTS = [
    ("jsonschema.json", REPO_ROOT / "resources" / "gens" / "jsonschema" / "jsonschema.json", _normalize_json),
    ("context.jsonld", REPO_ROOT / "resources" / "gens" / "jsonldcontext" / "context.jsonld", _normalize_json),
    ("spec-sections.html", REPO_ROOT / "resources" / "gens" / "index.html", generated_sections_html),
]


@pytest.mark.parametrize("name, gen_path, normalize", ARTIFACTS, ids=[n for n, _, _ in ARTIFACTS])
def test_golden_matches_generated(request, name: str, gen_path: Path, normalize):
    if not gen_path.exists():
        pytest.skip(f"Generated artifact not found: {gen_path}")
    current = normalize(gen_path)
    golden_path = GOLDENS_DIR / name

    if request.config.getoption("--update-goldens"):
        GOLDENS_DIR.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(current, encoding="utf-8")
        pytest.skip(f"Golden updated: {golden_path}")

    assert golden_path.exists(), f"Golden missing: {golden_path}; run with --update-goldens to create it."
    golden = golden_path.read_text(encoding="utf-8")
    if current == golden:
        return

    diff = list(difflib.unified_diff(
        golden.splitlines(), current.splitlines(), f"snapshots/{name}", f"generated {name}", lineterm=""
    ))
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as fh:
            fh.write(f"### Golden diff: {name} ({len(diff)} changed lines)\n\n```diff\n")
            fh.write("\n".join(diff[:60]))
            if len(diff) > 60:
                fh.write(f"\n... {len(diff) - 60} more lines, run the test locally for the full diff")
            fh.write("\n```\n")
    pytest.fail(
        f"Generated {name} differs from the golden snapshot, first diff lines:\n"
        + "\n".join(diff[:15])
        + "\n\nif the change is intended, update with --update-goldens."
    )

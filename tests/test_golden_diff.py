"""Check generated artifacts against committed snapshots."""
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


def _walk(old, new, path: list, changes: list) -> None:
    if isinstance(old, dict) and isinstance(new, dict):
        for key in sorted(set(old) | set(new)):
            if key not in old:
                changes.append(("added", path + [key]))
            elif key not in new:
                changes.append(("removed", path + [key]))
            else:
                _walk(old[key], new[key], path + [key], changes)
    elif isinstance(old, list) and isinstance(new, list) and len(old) == len(new):
        for index, (old_item, new_item) in enumerate(zip(old, new)):
            _walk(old_item, new_item, path + [index], changes)
    elif old != new:
        changes.append(("changed", path))


def _pattern(path: list) -> str:
    # names become *: entries of $defs and properties, terms of the root @context, list indexes
    parts = []
    for parent, part in zip([None] + path, path):
        if isinstance(part, int):
            parts.append("[*]")
        elif parent in ("$defs", "properties") or (parent == "@context" and len(parts) == 1):
            parts.append(".*")
        else:
            parts.append(f".{part}")
    return "$" + "".join(parts)


def _json_change_summary(golden: str, current: str) -> list[str]:
    """Changes grouped by JSON path pattern, with a count and one example each."""
    changes = []
    _walk(json.loads(golden), json.loads(current), [], changes)
    groups = {}
    for kind, path in changes:
        group = groups.setdefault((kind, _pattern(path)), [0, path])
        group[0] += 1
    lines = [f"{len(changes)} changes, {len(groups)} patterns"]
    for (kind, pattern), (count, example) in sorted(groups.items(), key=lambda item: -item[1][0]):
        lines.append(f"{count:5}  {kind:8} {pattern}   e.g. $.{'.'.join(map(str, example))}")
    return lines


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

    summary = _json_change_summary(golden, current) if name.endswith(".json") or name.endswith(".jsonld") else []
    diff = list(difflib.unified_diff(
        golden.splitlines(), current.splitlines(), f"snapshots/{name}", f"generated {name}", lineterm=""
    ))
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as fh:
            fh.write(f"### Golden diff: {name} ({len(diff)} changed lines)\n\n")
            if summary:
                fh.write("```\n" + "\n".join(summary) + "\n```\n\n")
            fh.write("```diff\n" + "\n".join(diff[:60]))
            if len(diff) > 60:
                fh.write(f"\n... {len(diff) - 60} more lines, run the test locally for the full diff")
            fh.write("\n```\n")
    pytest.fail(
        f"Generated {name} differs from the golden snapshot:\n"
        + "\n".join(summary + ["", "first diff lines:"] + diff[:15])
        + "\n\nif the change is intended, update with --update-goldens."
    )

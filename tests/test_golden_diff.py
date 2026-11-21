"""Check generated artifacts against committed snapshots."""

from __future__ import annotations

import difflib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from .spec_html_compare import generated_sections_html

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
GOLDENS_DIR = TESTS_DIR / "snapshots"


@pytest.fixture(scope="session", autouse=True)
def regenerate_artifacts():
    venv_bin = Path(sys.executable).parent
    cli_bin = venv_bin / "wot-toolchain"
    subprocess.run(
        [str(cli_bin), "generate-wot-resources", "-d"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )


def _normalize_json(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    return json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def _read_text(path: Path) -> str:
    return "\n".join(line.rstrip() for line in path.read_text(encoding="utf-8").splitlines()) + "\n"


# name, generated file, function that turns it into the compared text
ARTIFACTS = [
    ("jsonschema.json", REPO_ROOT / "resources" / "gens" / "jsonschema" / "jsonschema.json", _normalize_json),
    ("context.jsonld", REPO_ROOT / "resources" / "gens" / "jsonldcontext" / "context.jsonld", _normalize_json),
    ("spec-sections.html", REPO_ROOT / "resources" / "gens" / "index.html", generated_sections_html),
    ("owl/td.ttl", REPO_ROOT / "resources" / "gens" / "owl" / "td.ttl", _read_text),
    ("owl/hctl.ttl", REPO_ROOT / "resources" / "gens" / "owl" / "hctl.ttl", _read_text),
    ("owl/wotsec.ttl", REPO_ROOT / "resources" / "gens" / "owl" / "wotsec.ttl", _read_text),
    ("owl/jsonschema.ttl", REPO_ROOT / "resources" / "gens" / "owl" / "jsonschema.ttl", _read_text),
    ("owl/tm.ttl", REPO_ROOT / "resources" / "gens" / "owl" / "tm.ttl", _read_text),
    ("shapes.shacl.ttl", REPO_ROOT / "resources" / "gens" / "shacl" / "shapes.shacl.ttl", _read_text),
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
        for index, (old_item, new_item) in enumerate(zip(old, new, strict=True)):
            _walk(old_item, new_item, path + [index], changes)
    elif old != new:
        changes.append(("changed", path))


def _pattern(path: list) -> str:
    # names become *: entries of $defs and properties, terms of the root @context, list indexes
    parts = []
    # the shifted copy is one longer, its last element has no part to pair with
    for parent, part in zip([None] + path, path, strict=False):
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
        golden_path.parent.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(current, encoding="utf-8")
        pytest.skip(f"Golden updated: {golden_path}")

    assert golden_path.exists(), f"Golden missing: {golden_path}; run with --update-goldens to create it."
    golden = golden_path.read_text(encoding="utf-8")
    if current == golden:
        return

    is_json = name.endswith(".json") or name.endswith(".jsonld")
    summary = _json_change_summary(golden, current) if is_json else []
    diff = list(
        difflib.unified_diff(
            golden.splitlines(), current.splitlines(), f"snapshots/{name}", f"generated {name}", lineterm=""
        )
    )
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with Path(step_summary).open("a", encoding="utf-8") as fh:
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

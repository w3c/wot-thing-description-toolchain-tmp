#!/usr/bin/env python3
"""One-shot migration: extract JSONC frontmatter + hide markers → _snippets.yaml manifest.

Run from repo root:
    python scripts/migrate_snippets_to_manifest.py [--dry-run]

What it does:
1. Reads all JSONC frontmatter → builds snippets: section
2. Analyzes @hide-start/@hide-end blocks → converts to hide_paths or show_paths
3. Reads all group YAMLs → builds groups: section
4. Writes resources/snippets/_snippets.yaml
5. Strips JSONC files → pure JSON (no frontmatter, no hide markers, no comments)
6. Renames .jsonc → .json

Idempotent: skips files already migrated (no frontmatter found).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SNIPPETS_DIR = REPO_ROOT / "resources" / "snippets"
GROUPS_DIR = SNIPPETS_DIR / "groups"
MANIFEST_PATH = SNIPPETS_DIR / "_snippets.yaml"

FM_RE = re.compile(r"^\s*/\*\s*\n---\n(.*?)\n---\s*\n\*/\s*\n?", re.DOTALL)
HIDE_START_RE = re.compile(r"^\s*//\s*@hide-start\s*$")
HIDE_END_RE = re.compile(r"^\s*//\s*@hide-end\s*$")
JSONC_COMMENT_RE = re.compile(
    r'"(?:[^"\\]|\\.)*"'
    r"|/\*.*?\*/"
    r"|//[^\n]*",
    re.DOTALL,
)

# Non-structural files that need show_paths instead of hide_paths.
# Manually determined — these split objects mid-property.
SHOW_PATHS_OVERRIDES: dict[str, list[str]] = {
    "dataschema-serialization": [
        "properties.lampState.type",
        "properties.lampState.properties",
    ],
    "form-content-type": [
        "properties.status.forms.contentType",
    ],
    "form-serialization": [
        "properties.temperature.forms",
    ],
}

# Files that hide contents of nested keys (not top-level keys).
# Pattern: keep key visible, hide its children → {// ...} or [// ...]
NESTED_HIDE_OVERRIDES: dict[str, list[str]] = {
    "security-nosec": [
        "properties.*",
        "actions.*",
        "events.*",
        "links.*",
    ],
    "thing-serialization": [
        "titles.*",
        "descriptions.*",
        "version.*",
        "securityDefinitions.*",
        "security",
        "properties.*",
        "actions.*",
        "events.*",
        "links.*",
        "forms.*",
    ],
}


def _strip_jsonc_comments(text: str) -> str:
    def _repl(m: re.Match[str]) -> str:
        return m.group(0) if m.group(0).startswith('"') else ""
    return JSONC_COMMENT_RE.sub(_repl, text)


def _extract_frontmatter(text: str) -> tuple[dict, str]:
    m = FM_RE.match(text)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    return meta, text[m.end():]


def _get_hide_line_ranges(lines: list[str]) -> list[tuple[int, int]]:
    ranges = []
    start = None
    for i, line in enumerate(lines):
        if HIDE_START_RE.match(line):
            start = i
        elif HIDE_END_RE.match(line) and start is not None:
            ranges.append((start, i))
            start = None
    return ranges


def _find_top_level_keys_in_range(
    json_text: str, lines: list[str], hide_ranges: list[tuple[int, int]]
) -> list[str]:
    """Find top-level JSON keys that fall within hide ranges."""
    try:
        obj = json.loads(_strip_jsonc_comments(json_text))
    except json.JSONDecodeError:
        return []

    if not isinstance(obj, dict):
        return []

    hidden_keys = []
    key_re = re.compile(r'^\s*"([^"]+)"\s*:')

    brace_depth = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        in_hide = any(start <= i <= end for start, end in hide_ranges)

        if brace_depth == 1 and in_hide:
            km = key_re.match(stripped)
            if km:
                key = km.group(1)
                if key in obj:
                    hidden_keys.append(key)

        for ch in stripped:
            if ch == '{':
                brace_depth += 1
            elif ch == '}':
                brace_depth -= 1

    return hidden_keys


def _analyze_hide_blocks(stem: str, body: str) -> dict:
    """Determine hide_paths or show_paths for a snippet."""
    if stem in SHOW_PATHS_OVERRIDES:
        return {"show_paths": SHOW_PATHS_OVERRIDES[stem]}

    if stem in NESTED_HIDE_OVERRIDES:
        return {"hide_paths": NESTED_HIDE_OVERRIDES[stem]}

    lines = body.split("\n")
    hide_ranges = _get_hide_line_ranges(lines)
    if not hide_ranges:
        return {}

    keys = _find_top_level_keys_in_range(body, lines, hide_ranges)
    if keys:
        return {"hide_paths": keys}

    print(f"  WARNING: {stem} — could not determine hide paths, needs manual review")
    return {}


def _strip_to_pure_json(body: str) -> str:
    """Remove hide markers and JSONC comments, return pure JSON."""
    lines = body.split("\n")
    clean_lines = []
    for line in lines:
        if HIDE_START_RE.match(line) or HIDE_END_RE.match(line):
            continue
        clean_lines.append(line)

    text = "\n".join(clean_lines)
    stripped = _strip_jsonc_comments(text)

    try:
        parsed = json.loads(stripped)
        return json.dumps(parsed, indent=4, ensure_ascii=False) + "\n"
    except json.JSONDecodeError:
        print(f"  WARNING: could not re-serialize as JSON, keeping cleaned text")
        return text


def _process_snippets(dry_run: bool) -> dict[str, dict]:
    """Process all JSONC snippets → manifest entries + strip files."""
    snippets: dict[str, dict] = {}

    for path in sorted(SNIPPETS_DIR.glob("*.jsonc")):
        if path.stem == "TEMPLATE":
            continue

        text = path.read_text(encoding="utf-8")
        meta, body = _extract_frontmatter(text)

        if not meta and "---" not in text[:50]:
            print(f"  SKIP {path.stem} (already migrated or no frontmatter)")
            continue

        entry: dict = {}
        if meta.get("id"):
            entry["id"] = meta["id"]
        if meta.get("title"):
            entry["title"] = meta["title"]
        if meta.get("layout", "aside") != "aside":
            entry["layout"] = meta["layout"]
        if meta.get("validate") is False:
            entry["validate"] = False

        hide_info = _analyze_hide_blocks(path.stem, body)
        entry.update(hide_info)

        snippets[path.stem] = entry

        if not dry_run:
            pure_json = _strip_to_pure_json(body)
            json_path = path.with_suffix(".json")
            json_path.write_text(pure_json, encoding="utf-8")
            path.unlink()
            print(f"  {path.stem}: .jsonc → .json")
        else:
            print(f"  {path.stem}: would convert .jsonc → .json")

    return snippets


def _process_groups(dry_run: bool) -> dict[str, dict]:
    """Process all group YAMLs → manifest entries."""
    groups: dict[str, dict] = {}

    if not GROUPS_DIR.is_dir():
        return groups

    for path in sorted(GROUPS_DIR.glob("*.yaml")):
        if path.stem == "TEMPLATE":
            continue

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        groups[path.stem] = data

        if not dry_run:
            path.unlink()
            print(f"  group {path.stem}: deleted")
        else:
            print(f"  group {path.stem}: would delete")

    if not dry_run and GROUPS_DIR.is_dir():
        template = GROUPS_DIR / "TEMPLATE.yaml"
        if template.exists():
            template.unlink()
        try:
            GROUPS_DIR.rmdir()
            print("  groups/ directory removed")
        except OSError:
            print("  groups/ directory not empty, kept")

    return groups


def _write_manifest(snippets: dict, groups: dict, dry_run: bool) -> None:
    manifest = OrderedDict()
    manifest["snippets"] = snippets
    manifest["groups"] = groups

    content = yaml.dump(
        dict(manifest),
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )

    if dry_run:
        print(f"\n--- _snippets.yaml preview (first 80 lines) ---")
        for i, line in enumerate(content.split("\n")[:80]):
            print(line)
        print("...")
    else:
        MANIFEST_PATH.write_text(content, encoding="utf-8")
        print(f"\nWrote {MANIFEST_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    print("=== Processing snippets ===")
    snippets = _process_snippets(args.dry_run)
    print(f"\n{len(snippets)} snippets processed")

    print("\n=== Processing groups ===")
    groups = _process_groups(args.dry_run)
    print(f"\n{len(groups)} groups processed")

    print("\n=== Writing manifest ===")
    _write_manifest(snippets, groups, args.dry_run)

    # Handle TEMPLATE.jsonc
    template_jsonc = SNIPPETS_DIR / "TEMPLATE.jsonc"
    if template_jsonc.exists() and not args.dry_run:
        template_jsonc.unlink()
        print("Deleted TEMPLATE.jsonc")

    print("\nDone." if not args.dry_run else "\nDry run complete. No files changed.")


if __name__ == "__main__":
    main()

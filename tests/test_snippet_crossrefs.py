"""Validate that cross-references in the template resolve to known IDs.

Checks two directions:
1. Every [[[#X]]] ReSpec cross-reference in the template resolves to either
   a snippet/group id or an inline id="X" in the template HTML.
2. All snippet IDs in the manifest are unique.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = REPO_ROOT / "resources" / "index.template.html"
MANIFEST_PATH = REPO_ROOT / "resources" / "snippets" / "_snippets.yaml"

CROSSREF_RE = re.compile(r"\[\[\[#([^\]]+)\]\]\]")
INLINE_ID_RE = re.compile(r'id="([^"]+)"')

RENDER_TIME_ID_PREFIXES = ("bib-", "dfn-", "table-", "fig-")


def _snippet_ids() -> dict[str, str]:
    """Return {id: source_key} for all snippet and group IDs in manifest."""
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    ids: dict[str, str] = {}
    for name, meta in manifest.get("snippets", {}).items():
        sid = meta.get("id")
        if sid:
            ids[sid] = name
    for name, group in manifest.get("groups", {}).items():
        gid = group.get("id")
        if gid:
            ids[gid] = f"group:{name}"
    return ids


def _template_inline_ids(html: str) -> set[str]:
    return set(INLINE_ID_RE.findall(html))


def _template_crossrefs(html: str) -> list[tuple[int, str]]:
    refs = []
    for i, line in enumerate(html.splitlines(), 1):
        for m in CROSSREF_RE.finditer(line):
            refs.append((i, m.group(1)))
    return refs


def test_template_crossrefs_resolve():
    """Every [[[#X]]] in the template must resolve to a known ID."""
    html = TEMPLATE.read_text(encoding="utf-8")
    snippet_ids = _snippet_ids()
    inline_ids = _template_inline_ids(html)
    all_known = set(snippet_ids.keys()) | inline_ids

    unresolved = []
    for line_no, target in _template_crossrefs(html):
        if target in all_known:
            continue
        if any(target.startswith(p) for p in RENDER_TIME_ID_PREFIXES):
            continue
        unresolved.append(f"  line {line_no}: [[[#{target}]]]")

    assert not unresolved, (
        f"{len(unresolved)} cross-reference(s) do not resolve to any known ID:\n"
        + "\n".join(unresolved)
    )


def test_no_duplicate_snippet_ids():
    """All snippet IDs in manifest must be unique."""
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    id_to_sources: dict[str, list[str]] = {}

    for name, meta in manifest.get("snippets", {}).items():
        sid = meta.get("id")
        if sid:
            id_to_sources.setdefault(sid, []).append(name)
    for name, group in manifest.get("groups", {}).items():
        gid = group.get("id")
        if gid:
            id_to_sources.setdefault(gid, []).append(f"group:{name}")

    duplicates = {sid: srcs for sid, srcs in id_to_sources.items() if len(srcs) > 1}
    assert not duplicates, (
        "Duplicate IDs:\n"
        + "\n".join(f"  {sid}: {', '.join(srcs)}" for sid, srcs in duplicates.items())
    )

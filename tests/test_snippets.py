"""Tests for snippet metadata integrity.

Verifies that:
- Every snippet referenced directly in the template has an ``id:`` in its frontmatter.
- All snippet ids are globally unique across the snippets directory.
"""
from __future__ import annotations

import re
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
TEMPLATE_PATH = REPO_ROOT / "resources" / "index.template.html"
SNIPPETS_DIR = REPO_ROOT / "resources" / "snippets"

_SNIPPET_CALL_RE = re.compile(r"snippet\('([^']+)'\)")


def _standalone_snippet_names() -> set[str]:
    """Return all snippet names called via snippet('name') in the template."""
    content = TEMPLATE_PATH.read_text(encoding="utf-8")
    return set(_SNIPPET_CALL_RE.findall(content))


def _snippet_id(snippet_path: Path) -> str | None:
    """Return the id value from a snippet's frontmatter, or None if absent."""
    content = snippet_path.read_text(encoding="utf-8")
    m = re.search(r"^id:\s*(\S+)", content, re.MULTILINE)
    return m.group(1) if m else None


def test_all_standalone_snippets_have_ids():
    """Every snippet called directly in the template must have an id in its frontmatter."""
    standalone_names = _standalone_snippet_names()
    missing = []
    for name in sorted(standalone_names):
        snippet_path = SNIPPETS_DIR / f"{name}.jsonc"
        if not snippet_path.exists():
            missing.append(f"{name}: file not found at {snippet_path}")
            continue
        snippet_id = _snippet_id(snippet_path)
        if not snippet_id:
            missing.append(f"{name}: no id in frontmatter")
    assert not missing, (
        f"{len(missing)} standalone snippet(s) are missing an id:\n"
        + "\n".join(f"  - {m}" for m in missing)
    )


def test_no_duplicate_snippet_ids():
    """All snippet ids across resources/snippets/*.jsonc must be unique."""
    id_to_files: dict[str, list[str]] = {}
    for snippet_path in sorted(SNIPPETS_DIR.glob("*.jsonc")):
        snippet_id = _snippet_id(snippet_path)
        if snippet_id:
            id_to_files.setdefault(snippet_id, []).append(snippet_path.name)
    duplicates = {sid: files for sid, files in id_to_files.items() if len(files) > 1}
    assert not duplicates, (
        f"{len(duplicates)} duplicate snippet id(s) found:\n"
        + "\n".join(
            f"  - '{sid}': {', '.join(files)}"
            for sid, files in sorted(duplicates.items())
        )
    )

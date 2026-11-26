"""Compare generated snippets with upstream inline examples."""
from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

import pytest
import yaml
from lxml.html import HtmlElement

from .spec_html_compare import normalize_text, parse_html

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent
UPSTREAM_PATH = REPO_ROOT / "resources" / "upstream" / "html" / "index.html"
GENERATED_PATH = REPO_ROOT / "resources" / "gens" / "index.html"
APPROVED_DIVERGENCES_PATH = TESTS_DIR.parent / "resources" / "approved_divergences" / "snippets.yaml"
EXAMPLE_SELECTOR = "aside.example, pre.example"
_MISSING = object()

_JSON_STRING_RE = re.compile(r'"(?:[^"\\]|\\.)*"')
_JSONC_COMMENT_RE = re.compile(
    _JSON_STRING_RE.pattern + r"|/\*.*?\*/" r"|//[^\n]*", re.DOTALL
)
_ELLIPSIS_OBJECT_RE = re.compile(
    r"\{\s*(?://\s*\.\.\.\s*|/\*\s*\.\.\.\s*\*/\s*)\}", re.MULTILINE
)
_ELLIPSIS_ARRAY_RE = re.compile(r"\[\s*(?://\s*\.\.\.\s*|\.\.\.\s*)\]", re.MULTILINE)
_ELLIPSIS_BLOCK_VALUE_RE = re.compile(r":\s*/\*\s*\.\.\.\s*\*/")
_ELLIPSIS_LINE_VALUE_RE = re.compile(
    r":\s*//\s*\.\.\.\s*,?\s*(?=\n)", re.MULTILINE
)
_ELLIPSIS_LINE_RE = re.compile(r"^\s*(?://\s*)?\.\.\.\s*$", re.MULTILINE)
_TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")


def _strip_jsonc(text: str) -> str:
    def _keep_strings(m: re.Match[str]) -> str:
        return m.group(0) if m.group(0).startswith('"') else ""
    return _JSONC_COMMENT_RE.sub(_keep_strings, text)


def _transform_outside_json_strings(text: str, transform: Callable[[str], str]) -> str:
    """Apply a JSONC syntax transform without changing string literals."""
    parts: list[str] = []
    start = 0
    for match in _JSON_STRING_RE.finditer(text):
        parts.append(transform(text[start:match.start()]))
        parts.append(match.group())
        start = match.end()
    parts.append(transform(text[start:]))
    return "".join(parts)


def _normalize_illustrative_tokens(text: str) -> str:
    text = _ELLIPSIS_OBJECT_RE.sub("{}", text)
    text = _ELLIPSIS_ARRAY_RE.sub("[]", text)
    text = _ELLIPSIS_BLOCK_VALUE_RE.sub(": null", text)
    text = _ELLIPSIS_LINE_VALUE_RE.sub(": null,", text)
    return _ELLIPSIS_LINE_RE.sub("", text)


def _normalize_illustrative_jsonc(text: str) -> str:
    """Make upstream's ellipsis notation comparable as JSONC placeholders."""
    normalized = _transform_outside_json_strings(text, _normalize_illustrative_tokens)
    normalized = _strip_jsonc(normalized)
    return _transform_outside_json_strings(
        normalized, lambda chunk: _TRAILING_COMMA_RE.sub(r"\1", chunk)
    )


def _try_parse_json(text: str) -> object | None:
    cleaned = _normalize_illustrative_jsonc(text).strip()
    if not cleaned:
        return None
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def test_illustrative_jsonc_normalization_preserves_string_literals() -> None:
    source = """
    {
      "literal_trailing": "example,}",
      "literal_line_comment": "// ...",
      "literal_block_comment": "/*...*/",
      "literal_array": "[...]",
      "object_placeholder": {/*...*/},
      "array_placeholder": [// ...],
      "value_placeholder": /*...*/,
    }
    """

    assert _try_parse_json(source) == {
        "literal_trailing": "example,}",
        "literal_line_comment": "// ...",
        "literal_block_comment": "/*...*/",
        "literal_array": "[...]",
        "object_placeholder": {},
        "array_placeholder": [],
        "value_placeholder": None,
    }


def _path_value(document: object, path: str) -> object:
    value = document
    for segment in path.split("."):
        if isinstance(value, dict):
            value = value.get(segment, _MISSING)
        elif isinstance(value, list) and segment.isdigit():
            index = int(segment)
            value = value[index] if index < len(value) else _MISSING
        else:
            return _MISSING
        if value is _MISSING:
            return _MISSING
    return value


def _difference_paths(upstream: object, generated: object, path: str = "") -> list[str]:
    """Return the precise JSON paths that differ between two examples."""
    if isinstance(upstream, dict) and isinstance(generated, dict):
        differences: list[str] = []
        for key in sorted(set(upstream) | set(generated)):
            child_path = f"{path}.{key}" if path else key
            if key not in upstream or key not in generated:
                differences.append(child_path)
            else:
                differences.extend(_difference_paths(upstream[key], generated[key], child_path))
        return differences
    if upstream != generated:
        return [path]
    return []


class Snippet(NamedTuple):
    """One `pre` of a spec example, addressed by its place in the document."""

    section_id: str
    position: int
    pre: int
    pre_count: int
    example_id: str | None
    text: str

    @property
    def place(self) -> tuple[str, int, int]:
        return self.section_id, self.position, self.pre

    @property
    def locator(self) -> dict[str, object]:
        """Return the `upstream_locator` an approved divergence uses for this snippet."""
        example = (
            {"example_id": self.example_id}
            if self.example_id
            else {"section_id": self.section_id, "position": self.position}
        )
        return {"kind": "example"} | example | ({"pre": self.pre} if self.pre_count > 1 else {})

    def __str__(self) -> str:
        name = self.example_id or f"{self.section_id}#{self.position}"
        return f"{name}/pre{self.pre}" if self.pre_count > 1 else name


def _snippets(tree: HtmlElement) -> list[Snippet]:
    """Return every `pre` of every example, numbered within its section and its example."""
    examples_per_section: Counter[str] = Counter()
    snippets: list[Snippet] = []
    for example in tree.cssselect(EXAMPLE_SELECTOR):
        section_id = example.xpath("ancestor::section[@id][1]/@id")[0]
        examples_per_section[section_id] += 1
        pres = example.cssselect("pre")
        snippets.extend(
            Snippet(section_id, examples_per_section[section_id], index, len(pres), example.get("id"), pre.text_content())
            for index, pre in enumerate(pres, start=1)
        )
    return snippets


def _comparable(text: str) -> object:
    """Return the parsed JSONC of a snippet, or its normalized text when it is not JSON."""
    parsed = _try_parse_json(text)
    return normalize_text(text) if parsed is None else parsed


def _show(value: object) -> str:
    return value if isinstance(value, str) else json.dumps(value, sort_keys=True, indent=2)


UPSTREAM_TREE = parse_html(UPSTREAM_PATH)
UPSTREAM_SNIPPETS = _snippets(UPSTREAM_TREE)


@pytest.fixture(scope="module")
def generated_tree() -> HtmlElement:
    if not GENERATED_PATH.exists():
        pytest.fail(f"Generated HTML not found at {GENERATED_PATH}; run `wot-toolchain generate-wot-resources` first.")
    return parse_html(GENERATED_PATH)


@pytest.fixture(scope="module")
def generated_snippets(generated_tree: HtmlElement) -> dict[tuple[str, int, int], Snippet]:
    return {snippet.place: snippet for snippet in _snippets(generated_tree)}


@pytest.fixture(scope="module")
def snippet_divergences() -> list[dict]:
    with APPROVED_DIVERGENCES_PATH.open(encoding="utf-8") as divergence_file:
        return yaml.safe_load(divergence_file)["divergences"]


@pytest.mark.parametrize("upstream", UPSTREAM_SNIPPETS, ids=str)
def test_example_matches_upstream(
    upstream: Snippet,
    generated_snippets: dict[tuple[str, int, int], Snippet],
    snippet_divergences: list[dict],
) -> None:
    """Every upstream example `pre` equals the generated one at the same place, or is a recorded divergence."""
    generated = generated_snippets.get(upstream.place)
    assert generated is not None, f"[{upstream}] no generated example at {upstream.place}"
    assert generated.pre_count == upstream.pre_count, f"[{upstream}] number of `pre` blocks differs"
    if upstream.example_id:
        assert generated.example_id == upstream.example_id, f"[{upstream}] generated example has another id"

    upstream_value, generated_value = _comparable(upstream.text), _comparable(generated.text)
    entry = next((e for e in snippet_divergences if e["upstream_locator"] == upstream.locator), None)
    if upstream_value == generated_value:
        assert entry is None, f"snippet divergence '{entry and entry['id']}' is stale"
        return

    assert entry is not None, (
        f"[{upstream}] differs from upstream; locator {upstream.locator}\n"
        f"--- UPSTREAM ---\n{_show(upstream_value)}\n"
        f"--- GENERATED ---\n{_show(generated_value)}"
    )
    assert _difference_paths(upstream_value, generated_value) == entry["expected_difference_paths"], (
        f"snippet divergence '{entry['id']}' no longer has the expected semantic differences"
    )
    for path, expected in entry["expected_generated"]["json_paths"].items():
        actual = _path_value(generated_value, path)
        assert actual == expected, (
            f"snippet divergence '{entry['id']}' no longer has the expected generated value "
            f"at '{path}': expected {expected!r}, got {actual!r}"
        )


def test_every_snippet_divergence_locates_an_upstream_example(snippet_divergences: list[dict]) -> None:
    locators = [snippet.locator for snippet in UPSTREAM_SNIPPETS]
    unlocated = [entry["id"] for entry in snippet_divergences if entry["upstream_locator"] not in locators]
    assert not unlocated, f"snippet divergences that match no upstream example: {unlocated}"


def test_example_count_parity(generated_tree: HtmlElement) -> None:
    upstream_count = len(UPSTREAM_TREE.cssselect(EXAMPLE_SELECTOR))
    generated_count = len(generated_tree.cssselect(EXAMPLE_SELECTOR))
    assert upstream_count == generated_count, (
        f"Example count differs: upstream={upstream_count}, generated={generated_count}"
    )

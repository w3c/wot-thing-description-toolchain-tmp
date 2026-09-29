"""Compare generated snippets with upstream inline examples."""
from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path

import lxml.html
import pytest
import yaml
from lxml.html import HtmlElement

from .spec_html_compare import normalize_text, parse_html

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent
UPSTREAM_PATH = REPO_ROOT / "resources" / "upstream" / "html" / "index.html"
GENERATED_PATH = REPO_ROOT / "resources" / "gens" / "index.html"
APPROVED_DIVERGENCES_PATH = TESTS_DIR.parent / "approved_divergences" / "snippets.yaml"
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


def _canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, indent=2)


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


def _extract_pre_text(element: HtmlElement) -> str:
    pres = element.cssselect("pre")
    if pres:
        return pres[0].text_content()
    return element.text_content()


def _examples_by_id(tree: HtmlElement) -> dict[str, HtmlElement]:
    result: dict[str, HtmlElement] = {}
    for el in tree.cssselect('aside.example[id], pre.example[id]'):
        eid = el.get("id")
        if eid:
            result[eid] = el
    return result


def _tabbed_groups_by_title(tree: HtmlElement) -> dict[str, HtmlElement]:
    result: dict[str, HtmlElement] = {}
    for aside in tree.cssselect("aside.example.ds-selector-tabs"):
        spans = aside.cssselect("span.example-title")
        if spans:
            title = normalize_text(spans[0].text_content())
            result[title] = aside
    return result


def _tab_contents(group: HtmlElement) -> list[str]:
    return [pre.text_content().strip() for pre in group.cssselect("pre")]


@pytest.fixture(scope="module")
def upstream_tree():
    if not UPSTREAM_PATH.exists():
        pytest.skip(f"Upstream HTML not found at {UPSTREAM_PATH}")
    return parse_html(UPSTREAM_PATH)


@pytest.fixture(scope="module")
def generated_tree():
    if not GENERATED_PATH.exists():
        pytest.skip(f"Generated HTML not found at {GENERATED_PATH}; run generation first")
    return parse_html(GENERATED_PATH)


@pytest.fixture(scope="module")
def approved_snippet_divergences() -> dict[str, dict]:
    with APPROVED_DIVERGENCES_PATH.open(encoding="utf-8") as divergence_file:
        divergences = yaml.safe_load(divergence_file)["divergences"]
    return {entry["upstream_locator"]["example_id"]: entry for entry in divergences}


def _compare_example_json(example_id: str, upstream_el: HtmlElement, generated_el: HtmlElement) -> list[str]:
    upstream_text = _extract_pre_text(upstream_el)
    generated_text = _extract_pre_text(generated_el)

    upstream_json = _try_parse_json(upstream_text)
    generated_json = _try_parse_json(generated_text)

    diffs: list[str] = []

    if upstream_json is None and generated_json is None:
        up_norm = normalize_text(upstream_text)
        gen_norm = normalize_text(generated_text)
        if up_norm != gen_norm:
            diffs.append(
                f"[{example_id}] text content differs (non-JSON)\n"
                f"--- UPSTREAM ---\n{upstream_text.strip()}\n"
                f"--- GENERATED ---\n{generated_text.strip()}"
            )
        return diffs

    if upstream_json is None:
        diffs.append(
            f"[{example_id}] upstream not valid JSON, generated is\n"
            f"--- UPSTREAM ---\n{upstream_text.strip()}\n"
            f"--- GENERATED ---\n{generated_text.strip()}"
        )
        return diffs
    if generated_json is None:
        diffs.append(
            f"[{example_id}] generated not valid JSON, upstream is\n"
            f"--- UPSTREAM ---\n{upstream_text.strip()}\n"
            f"--- GENERATED ---\n{generated_text.strip()}"
        )
        return diffs

    if _canonical_json(upstream_json) != _canonical_json(generated_json):
        diffs.append(
            f"[{example_id}] JSON content differs semantically\n"
            f"--- UPSTREAM ---\n{_canonical_json(upstream_json)}\n"
            f"--- GENERATED ---\n{_canonical_json(generated_json)}"
        )
    return diffs


@pytest.mark.parametrize("example_id", [
    "simple-thing-description-sample",
    "thing-description-full-serialization",
    "td-model-example-lamp",
    "thing-serialization-sample",
    "security-basic-example",
    "multiple-security-definitions1",
    "multiple-security-definitions2a",
    "multiple-security-definitions2b",
    "example-oauth2-scopes",
    "property-serialization-sample",
    "action-serialization-sample",
    "event-serialization-sample",
    "link-serialization-sample",
    "form-serialization-sample",
    "td-forms-readall-example",
    "td-forms-urivariables-thing-example",
    "dataschema-serialization-sample",
    "saref-state-annotation-example",
    "saref-geolocation-annotation-example",
    "saref-geolocation-annotation-example-2",
    "saref-geolocation-annotation-example-3",
    "example-payload-binding",
    "td-model-example-basic-on-off",
    "td-model-example-smart-lamp-control",
    "td-model-example-tmRef",
])
def test_example_json_matches_upstream(
    upstream_tree, generated_tree, approved_snippet_divergences, example_id
):
    upstream_examples = _examples_by_id(upstream_tree)
    generated_examples = _examples_by_id(generated_tree)

    if example_id not in upstream_examples:
        pytest.fail(f"[{example_id}] not found in upstream")
    if example_id not in generated_examples:
        pytest.fail(f"[{example_id}] not found in generated output")

    upstream_el = upstream_examples[example_id]
    generated_el = generated_examples[example_id]
    diffs = _compare_example_json(example_id, upstream_el, generated_el)
    entry = approved_snippet_divergences.get(example_id)
    if not diffs:
        assert entry is None, f"approved snippet divergence '{example_id}' is stale"
        return

    assert entry is not None, "\n".join(diffs)
    upstream_json = _try_parse_json(_extract_pre_text(upstream_el))
    generated_json = _try_parse_json(_extract_pre_text(generated_el))
    assert upstream_json is not None, f"[{example_id}] expected upstream JSONC to parse"
    assert generated_json is not None, f"[{example_id}] expected generated JSONC to parse"
    assert _difference_paths(upstream_json, generated_json) == entry["expected_difference_paths"], (
        f"approved snippet divergence '{example_id}' no longer has the expected semantic differences"
    )
    for path, expected in entry["expected_generated"]["json_paths"].items():
        actual = _path_value(generated_json, path)
        assert actual == expected, (
            f"approved snippet divergence '{example_id}' no longer has the expected generated value "
            f"at '{path}': expected {expected!r}, got {actual!r}"
        )


TABBED_GROUP_TITLES = [
    "Top level/parent Smart Ventilator Thing Model",
    "Thing Descriptions of the Smart Ventilator",
    "Thing Description generation from Thing Model",
    "Linking Thing Description to a Thing Model Definition",
    "Temperature Sensor with a Temperature Event with subscription and cancellation",
]


@pytest.mark.parametrize("group_title", TABBED_GROUP_TITLES)
def test_tabbed_group_matches_upstream(upstream_tree, generated_tree, group_title):
    upstream_groups = _tabbed_groups_by_title(upstream_tree)
    generated_groups = _tabbed_groups_by_title(generated_tree)

    if group_title not in upstream_groups:
        pytest.fail(f"[{group_title}] tabbed group not found in upstream")
    if group_title not in generated_groups:
        pytest.fail(f"[{group_title}] tabbed group not found in generated output")

    upstream_tabs = _tab_contents(upstream_groups[group_title])
    generated_tabs = _tab_contents(generated_groups[group_title])

    if len(upstream_tabs) != len(generated_tabs):
        pytest.fail(
            f"[{group_title}] tab count differs: upstream={len(upstream_tabs)}, generated={len(generated_tabs)}"
        )

    for i, (up_text, gen_text) in enumerate(zip(upstream_tabs, generated_tabs)):
        up_json = _try_parse_json(up_text)
        gen_json = _try_parse_json(gen_text)
        if up_json is not None and gen_json is not None:
            assert _canonical_json(up_json) == _canonical_json(gen_json), (
                f"[{group_title}] tab {i} JSON content differs\n"
                f"--- UPSTREAM ---\n{_canonical_json(up_json)}\n"
                f"--- GENERATED ---\n{_canonical_json(gen_json)}"
            )
        else:
            assert normalize_text(up_text) == normalize_text(gen_text), (
                f"[{group_title}] tab {i} text content differs\n"
                f"--- UPSTREAM ---\n{up_text.strip()}\n"
                f"--- GENERATED ---\n{gen_text.strip()}"
            )


def test_example_count_parity(upstream_tree, generated_tree):
    upstream_count = len(upstream_tree.cssselect("aside.example, pre.example"))
    generated_count = len(generated_tree.cssselect("aside.example, pre.example"))
    assert upstream_count == generated_count, (
        f"Example count differs: upstream={upstream_count}, generated={generated_count}"
    )

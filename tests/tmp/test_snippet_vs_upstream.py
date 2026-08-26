"""Compare generated snippet HTML against upstream inline examples.

Matches examples by their ``id`` attribute and tabbed groups by their
``example-title`` text.  JSON content is parsed and compared semantically
so formatting differences (indentation, key ordering) are ignored.

All differences produce **warnings**, never assertion failures — the
upstream snippet examples do not all have an ID while the snippets in the toolchain MUST have an ID.
"""
from __future__ import annotations

import json
import re
import warnings
from pathlib import Path

import lxml.html
import pytest
from lxml.html import HtmlElement

from .spec_html_compare import normalize_text, parse_html

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent
UPSTREAM_PATH = REPO_ROOT / "resources" / "upstream" / "html" / "index.html"
GENERATED_PATH = REPO_ROOT / "resources" / "gens" / "index.html"

_JSONC_COMMENT_RE = re.compile(
    r'"(?:[^"\\]|\\.)*"'
    r"|/\*.*?\*/"
    r"|//[^\n]*",
    re.DOTALL,
)


def _strip_jsonc(text: str) -> str:
    def _keep_strings(m: re.Match[str]) -> str:
        return m.group(0) if m.group(0).startswith('"') else ""
    return _JSONC_COMMENT_RE.sub(_keep_strings, text)


def _try_parse_json(text: str) -> object | None:
    cleaned = _strip_jsonc(text).strip()
    if not cleaned:
        return None
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def _canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, indent=2)


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
def shared_example_ids(upstream_tree, generated_tree):
    upstream_ids = set(_examples_by_id(upstream_tree))
    generated_ids = set(_examples_by_id(generated_tree))
    shared = sorted(upstream_ids & generated_ids)
    only_upstream = upstream_ids - generated_ids
    only_generated = generated_ids - upstream_ids
    if only_upstream:
        warnings.warn(
            f"Examples only in upstream (no generated match): {sorted(only_upstream)}",
            stacklevel=1,
        )
    if only_generated:
        warnings.warn(
            f"Examples only in generated (not in upstream): {sorted(only_generated)}",
            stacklevel=1,
        )
    return shared


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
def test_example_json_matches_upstream(upstream_tree, generated_tree, example_id):
    upstream_examples = _examples_by_id(upstream_tree)
    generated_examples = _examples_by_id(generated_tree)

    if example_id not in upstream_examples:
        warnings.warn(f"[{example_id}] not found in upstream")
        return
    if example_id not in generated_examples:
        warnings.warn(f"[{example_id}] not found in generated output")
        return

    diffs = _compare_example_json(example_id, upstream_examples[example_id], generated_examples[example_id])
    for d in diffs:
        warnings.warn(d)


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
        warnings.warn(f"[{group_title}] tabbed group not found in upstream")
        return
    if group_title not in generated_groups:
        warnings.warn(f"[{group_title}] tabbed group not found in generated output")
        return

    upstream_tabs = _tab_contents(upstream_groups[group_title])
    generated_tabs = _tab_contents(generated_groups[group_title])

    if len(upstream_tabs) != len(generated_tabs):
        warnings.warn(
            f"[{group_title}] tab count differs: upstream={len(upstream_tabs)}, generated={len(generated_tabs)}"
        )
        return

    for i, (up_text, gen_text) in enumerate(zip(upstream_tabs, generated_tabs)):
        up_json = _try_parse_json(up_text)
        gen_json = _try_parse_json(gen_text)
        if up_json is not None and gen_json is not None:
            if _canonical_json(up_json) != _canonical_json(gen_json):
                warnings.warn(
                    f"[{group_title}] tab {i} JSON content differs\n"
                    f"--- UPSTREAM ---\n{_canonical_json(up_json)}\n"
                    f"--- GENERATED ---\n{_canonical_json(gen_json)}"
                )
        elif normalize_text(up_text) != normalize_text(gen_text):
            warnings.warn(
                f"[{group_title}] tab {i} text content differs\n"
                f"--- UPSTREAM ---\n{up_text.strip()}\n"
                f"--- GENERATED ---\n{gen_text.strip()}"
            )


def test_example_count_parity(upstream_tree, generated_tree):
    upstream_count = len(upstream_tree.cssselect("aside.example, pre.example"))
    generated_count = len(generated_tree.cssselect("aside.example, pre.example"))
    if upstream_count != generated_count:
        warnings.warn(
            f"Example count differs: upstream={upstream_count}, generated={generated_count}"
        )

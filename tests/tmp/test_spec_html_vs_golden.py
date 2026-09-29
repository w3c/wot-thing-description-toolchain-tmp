"""Compare generated vocabulary sections with upstream specification HTML."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from urllib.parse import unquote

import pytest
import yaml

from .spec_html_compare import (
    GENERATED_SECTION_IDS,
    assertion_texts,
    compare_tables,
    heading_texts,
    normalize_text,
    parse_html,
    row_key,
    section_by_id,
    table_rows,
    tables_by_caption,
)

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent
GOLDEN_PATH = REPO_ROOT / "resources" / "upstream" / "html" / "index.html"
GENERATED_PATH = REPO_ROOT / "resources" / "gens" / "index.html"
DIVERGENCES_PATH = TESTS_DIR.parent / "approved_divergences" / "html.yaml"

@pytest.fixture(scope="module")
def golden_tree():
    if not GOLDEN_PATH.exists():
        pytest.skip(f"Golden HTML not found at {GOLDEN_PATH}")
    return parse_html(GOLDEN_PATH)


@pytest.fixture(scope="module")
def generated_tree():
    if not GENERATED_PATH.exists():
        pytest.skip(f"Generated HTML not found at {GENERATED_PATH}; run `wotis generate-wot-resources -d` first.")
    return parse_html(GENERATED_PATH)


@pytest.fixture(scope="module")
def approved_html_divergences() -> list[dict]:
    return yaml.safe_load(DIVERGENCES_PATH.read_text(encoding="utf-8"))["divergences"]


def _sections_or_fail(golden_tree, generated_tree, section_id):
    golden_section = section_by_id(golden_tree, section_id)
    generated_section = section_by_id(generated_tree, section_id)
    assert golden_section is not None, f"section '{section_id}' missing in golden file"
    assert generated_section is not None, f"section '{section_id}' missing in generated file"
    return golden_section, generated_section


def _fail_on_findings(spec_html_findings: list[str], findings: list[str]) -> None:
    """Hand the differences to the report in conftest.py, then fail.

    The detail goes into the report, not into the assertion message, otherwise
    every failing section prints its own wall of text.
    """
    spec_html_findings.extend(findings)
    assert not findings, f"{len(findings)} difference(s), see the report at the end of the run"


def _assertions_in_scope(tree) -> dict[str, str]:
    """Assertion spans of all four sections, collected into one mapping."""
    found: dict[str, str] = {}
    for section_id in GENERATED_SECTION_IDS:
        section = section_by_id(tree, section_id)
        if section is not None:
            found.update(assertion_texts(section))
    return found


def _table_cell_text(tables, table_name: str, row_id: str, column: int) -> str:
    table = tables.get(table_name)
    assert table is not None, f"approved divergence table '{table_name}' not found"
    rows = {row_key(row): row for row in table_rows(table)}
    row = rows.get(row_id)
    assert row is not None, f"approved divergence row '{row_id}' not found"
    cells = row.cssselect("td")
    assert column < len(cells), f"approved divergence column {column} not found in row '{row_id}'"
    return normalize_text(cells[column].text_content())


def _approved_table_divergences(
    golden_tables, generated_tables, divergences: list[dict], section_id: str
) -> set[tuple[str, int]]:
    approved = set()
    for divergence in divergences:
        locator = divergence["upstream_locator"]
        if locator["kind"] != "table_cell" or locator["section_id"] != section_id:
            continue
        row_id = locator["row_id"]
        column = locator["column"]
        expected = divergence["expected_generated"]["text"]
        generated = _table_cell_text(generated_tables, locator["table"], row_id, column)
        golden = _table_cell_text(golden_tables, locator["table"], row_id, column)
        assert generated == expected, f"approved divergence '{divergence['id']}' no longer has its expected correction"
        assert golden != expected, f"approved divergence '{divergence['id']}' is stale because upstream now matches"
        approved.add((row_id, column))
    return approved


def _is_approved_table_finding(finding: str, approved: set[tuple[str, int]]) -> bool:
    return any(f"row '{row_id}', column {column}:" in finding for row_id, column in approved)


@pytest.mark.parametrize("section_id", GENERATED_SECTION_IDS)
def test_section_headings_match(golden_tree, generated_tree, spec_html_findings, section_id) -> None:
    golden_section, generated_section = _sections_or_fail(golden_tree, generated_tree, section_id)
    golden_headings = heading_texts(golden_section)
    generated_headings = heading_texts(generated_section)
    findings = []
    if golden_headings != generated_headings:
        findings.append(
            f"section '{section_id}': headings differ\n"
            f"    golden:    {golden_headings}\n"
            f"    generated: {generated_headings}"
        )
    _fail_on_findings(spec_html_findings, findings)


@pytest.mark.parametrize("section_id", GENERATED_SECTION_IDS)
def test_tables_present_in_both(golden_tree, generated_tree, spec_html_findings, section_id) -> None:
    golden_section, generated_section = _sections_or_fail(golden_tree, generated_tree, section_id)
    golden_tables = tables_by_caption(golden_section)
    generated_tables = tables_by_caption(generated_section)
    findings = []
    for caption in sorted(golden_tables.keys() - generated_tables.keys()):
        findings.append(f"section '{section_id}': table '{caption}' missing in generated file")
    for caption in sorted(generated_tables.keys() - golden_tables.keys()):
        findings.append(f"section '{section_id}': table '{caption}' only in generated file")
    _fail_on_findings(spec_html_findings, findings)


@pytest.mark.parametrize("section_id", GENERATED_SECTION_IDS)
def test_table_content_matches(
    golden_tree, generated_tree, spec_html_findings, approved_html_divergences, section_id
) -> None:
    golden_section, generated_section = _sections_or_fail(golden_tree, generated_tree, section_id)
    golden_tables = tables_by_caption(golden_section)
    generated_tables = tables_by_caption(generated_section)
    approved = _approved_table_divergences(
        golden_tables,
        generated_tables,
        approved_html_divergences,
        section_id,
    )
    findings = []
    for caption in golden_tables:
        if caption not in generated_tables:
            continue  # reported by test_tables_present_in_both
        table_findings = compare_tables(
            f"section '{section_id}', table '{caption}'",
            golden_tables[caption],
            generated_tables[caption],
        )
        findings.extend(finding for finding in table_findings if not _is_approved_table_finding(finding, approved))
    _fail_on_findings(spec_html_findings, findings)


def test_assertion_spans_match(golden_tree, generated_tree, spec_html_findings, approved_html_divergences) -> None:
    golden_assertions = _assertions_in_scope(golden_tree)
    generated_assertions = _assertions_in_scope(generated_tree)
    approved_assertions = {
        entry["upstream_locator"]["assertion_id"]: entry
        for entry in approved_html_divergences
        if entry["upstream_locator"]["kind"] == "assertion"
    }
    for assertion_id, divergence in approved_assertions.items():
        expected = divergence["expected_generated"]["text"]
        assert generated_assertions[assertion_id] == expected, (
            f"approved divergence '{assertion_id}' no longer has its expected correction"
        )
        assert golden_assertions[assertion_id] != expected, (
            f"approved divergence '{assertion_id}' is stale because upstream now matches"
        )

    findings = []
    for assertion_id in sorted(golden_assertions.keys() - generated_assertions.keys()):
        findings.append(f"assertion '{assertion_id}' is in the golden but not in the generated file")
    for assertion_id in sorted(generated_assertions.keys() - golden_assertions.keys()):
        findings.append(f"assertion '{assertion_id}' is in the generated but not in the golden file")
    for assertion_id in sorted(golden_assertions.keys() & generated_assertions.keys()):
        if assertion_id in approved_assertions:
            continue
        if golden_assertions[assertion_id] != generated_assertions[assertion_id]:
            findings.append(
                f"assertion '{assertion_id}': text differs\n"
                f"    golden:    {golden_assertions[assertion_id]}\n"
                f"    generated: {generated_assertions[assertion_id]}"
            )
    _fail_on_findings(spec_html_findings, findings)


# The two tests below need no golden, they check the generated file on its
# own. They keep the checks the removed tests/validators/html_validator.py had
# and the golden comparison above does not: duplicate ids and broken links.

# These ids do not exist in the ReSpec source, ReSpec creates them at render
RENDER_TIME_ID_PREFIXES = ("bib-", "dfn-")
RENDER_TIME_IDS = {"class-definitions", "namespaces", "semantic-annotations"}


def test_ids_are_unique(generated_tree) -> None:
    ids = [el.get("id") for el in generated_tree.cssselect("[id]") if el.get("id")]
    duplicated = sorted(value for value, count in Counter(ids).items() if count > 1)
    assert not duplicated, f"duplicate ids in the generated file: {', '.join(duplicated)}"


def test_internal_links_resolve(generated_tree) -> None:
    defined_ids = {el.get("id") for el in generated_tree.cssselect("[id]")}
    broken = set()
    for link in generated_tree.cssselect('a[href^="#"]'):
        target = unquote((link.get("href") or "")[1:])
        if not target or target in defined_ids:
            continue
        if target.startswith(RENDER_TIME_ID_PREFIXES) or target in RENDER_TIME_IDS:
            continue
        broken.add(target)
    assert not broken, (
        f"{len(broken)} link target(s) missing in the generated file: "
        + ", ".join(sorted(broken))
    )

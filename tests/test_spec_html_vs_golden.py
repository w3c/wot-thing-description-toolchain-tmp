"""Compare the generated spec HTML against the manual golden HTML.

Scope: the four sections the pipeline generates. resources/index.template.html
holds exactly four "%s" placeholders and each one sits inside one of these, so
their content comes from the LinkML schema. The other sections are hand-written
in the template and pass through unchanged. The golden file
tests/manual_goldens/html/index.html is the hand-verified reference, any
difference inside the four sections is an error.

The two integrity tests at the end check the generated file on its own and
do not need the golden.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from urllib.parse import unquote

import pytest

from .spec_html_compare import (
    GENERATED_SECTION_IDS,
    assertion_texts,
    compare_tables,
    heading_texts,
    parse_html,
    section_by_id,
    tables_by_caption,
)

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
GOLDEN_PATH = TESTS_DIR / "manual_goldens" / "html" / "index.html"
GENERATED_PATH = REPO_ROOT / "resources" / "gens" / "index.html"

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
def test_table_content_matches(golden_tree, generated_tree, spec_html_findings, section_id) -> None:
    golden_section, generated_section = _sections_or_fail(golden_tree, generated_tree, section_id)
    golden_tables = tables_by_caption(golden_section)
    generated_tables = tables_by_caption(generated_section)
    findings = []
    for caption in golden_tables:
        if caption not in generated_tables:
            continue  # reported by test_tables_present_in_both
        findings.extend(
            compare_tables(
                f"section '{section_id}', table '{caption}'",
                golden_tables[caption],
                generated_tables[caption],
            )
        )
    _fail_on_findings(spec_html_findings, findings)


def test_assertion_spans_match(golden_tree, generated_tree, spec_html_findings) -> None:
    golden_assertions = _assertions_in_scope(golden_tree)
    generated_assertions = _assertions_in_scope(generated_tree)
    findings = []
    for assertion_id in sorted(golden_assertions.keys() - generated_assertions.keys()):
        findings.append(f"assertion '{assertion_id}' is in the golden but not in the generated file")
    for assertion_id in sorted(generated_assertions.keys() - golden_assertions.keys()):
        findings.append(f"assertion '{assertion_id}' is in the generated but not in the golden file")
    for assertion_id in sorted(golden_assertions.keys() & generated_assertions.keys()):
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
RENDER_TIME_IDS = {"class-definitions", "namespaces"}


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

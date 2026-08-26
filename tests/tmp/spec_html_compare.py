"""Helpers to compare the generated spec HTML with the manual golden HTML.

Both files are ReSpec sources but serialized differently, so a plain text diff
only reports formatting noise. The comparison works on the parsed DOM instead:
sections by id, tables by caption, rows by their ``tr`` id. A table cell is
compared as plain text with whitespace collapsed, inline markup is not compared
because both files leave many links unresolved for ReSpec.
"""
from __future__ import annotations

from pathlib import Path

import lxml.etree
import lxml.html
from lxml.html import HtmlElement

# The sections the pipeline generates: resources/index.template.html holds
# exactly four "%s" placeholders and each one sits inside one of these.
GENERATED_SECTION_IDS = [
    "sec-core-vocabulary-definition",
    "sec-data-schema-vocabulary-definition",
    "sec-security-vocabulary-definition",
    "sec-hypermedia-vocabulary-definition",
]


def parse_html(path: Path) -> HtmlElement:
    return lxml.html.parse(str(path)).getroot()


def generated_sections_html(path: Path) -> str:
    """The four generated sections, serialized the same way every run.

    Used as the snapshot in test_golden_diff.py. Only the four sections are
    taken, so hand-written parts of the template do not end up in the snapshot.
    """
    tree = parse_html(path)
    parts = []
    for section_id in GENERATED_SECTION_IDS:
        section = section_by_id(tree, section_id)
        if section is None:
            parts.append(f"<!-- section {section_id} is missing -->\n")
            continue
        parts.append(lxml.etree.tostring(section, pretty_print=True, encoding="unicode"))
    # The template contains carriage returns and lxml writes them out as &#13;,
    # which only makes the snapshot diff harder to read.
    return "".join(parts).replace("&#13;", "")


def normalize_text(text: str | None) -> str:
    return " ".join((text or "").split())


def section_by_id(tree: HtmlElement, section_id: str) -> HtmlElement | None:
    sections = tree.cssselect(f'section[id="{section_id}"]')
    return sections[0] if sections else None


def heading_texts(section: HtmlElement) -> list[str]:
    return [normalize_text(h.text_content()) for h in section.cssselect("h2, h3, h4")]


def tables_by_caption(section: HtmlElement) -> dict[str, HtmlElement]:
    tables: dict[str, HtmlElement] = {}
    for table in section.cssselect("table"):
        captions = table.cssselect("caption")
        if captions:
            tables[normalize_text(captions[0].text_content())] = table
    return tables


def table_rows(table: HtmlElement) -> list[HtmlElement]:
    body_rows = table.cssselect("tbody tr")
    if body_rows:
        return body_rows
    return [row for row in table.cssselect("tr") if row.cssselect("td")]


def row_key(row: HtmlElement) -> str:
    if row.get("id"):
        return row.get("id")
    cells = row.cssselect("td")
    return normalize_text(cells[0].text_content()) if cells else "(empty row)"


def compare_tables(context: str, golden_table: HtmlElement, generated_table: HtmlElement) -> list[str]:
    findings = []

    golden_headers = [normalize_text(th.text_content()) for th in golden_table.cssselect("th")]
    generated_headers = [normalize_text(th.text_content()) for th in generated_table.cssselect("th")]
    if golden_headers != generated_headers:
        findings.append(
            f"{context}: header row differs - golden {golden_headers} | generated {generated_headers}"
        )

    golden_rows = {row_key(r): r for r in table_rows(golden_table)}
    generated_rows = {row_key(r): r for r in table_rows(generated_table)}
    for key in sorted(golden_rows.keys() - generated_rows.keys()):
        findings.append(f"{context}: row '{key}' is in the golden but not in the generated file")
    for key in sorted(generated_rows.keys() - golden_rows.keys()):
        findings.append(f"{context}: row '{key}' is in the generated but not in the golden file")

    golden_order = [k for k in golden_rows if k in generated_rows]
    generated_order = [k for k in generated_rows if k in golden_rows]
    if golden_order != generated_order:
        findings.append(f"{context}: rows are in a different order")

    for key in golden_order:
        golden_cells = golden_rows[key].cssselect("td")
        generated_cells = generated_rows[key].cssselect("td")
        if len(golden_cells) != len(generated_cells):
            findings.append(
                f"{context}, row '{key}': {len(golden_cells)} cells in golden, "
                f"{len(generated_cells)} in generated"
            )
            continue
        for column, (golden_cell, generated_cell) in enumerate(zip(golden_cells, generated_cells)):
            golden_text = normalize_text(golden_cell.text_content())
            generated_text = normalize_text(generated_cell.text_content())
            if golden_text != generated_text:
                findings.append(
                    f"{context}, row '{key}', column {column}: text differs\n"
                    f"    golden:    {golden_text}\n"
                    f"    generated: {generated_text}"
                )
    return findings


def assertion_texts(section: HtmlElement) -> dict[str, str]:
    """Map assertion span id -> normalized plain text (markup is not compared here)."""
    spans = section.cssselect("span.rfc2119-assertion[id]")
    return {span.get("id"): normalize_text(span.text_content()) for span in spans}

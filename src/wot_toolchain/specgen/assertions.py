"""
assertions.py – Generate stable assertion IDs from LinkML schemas and
produce assertions.csv, mirroring what extractFile.js does for the
SPARQL/STTL-based WoT TD pipeline.

How assertions work in the WoT TD spec HTML:
    The spec has three assertion CSS classes that extractFile.js selects:

      .rfc2119-assertion          – standalone paragraphs / spans
      .rfc2119-default-assertion  – standalone paragraphs / spans (default values)
      .rfc2119-table-assertion    – <tr> rows in vocabulary tables

Every vocabulary-term row in every generated <table class="def numbered">
already carries class="rfc2119-table-assertion".  What is missing is the
stable `id` attribute on those <tr> elements.

Stable ID convention (table rows)
──────────────────────────────────
  td-vocab-<slot-name>--<ClassName>

Special LinkML escape names are normalized to the historical TD anchors:
  @context  →  at-context
  @type     →  at-type
  @name     →  name

Examples:
  Thing.@context                 →  td-vocab-at-context--Thing
  Thing.@type                    →  td-vocab-at-type--Thing
  DataSchema.type                →  td-vocab-type--DataSchema

The IDs are guaranteed stable as long as the schema class/slot names
do not change – the same contract the SPARQL pipeline gave via ontology IRIs.
"""

from __future__ import annotations

import csv
import re
import logging

from dataclasses import dataclass
from lxml import html
from pathlib import Path
from typing import List, Optional

from ..errors import GenerationError


ASSERTION_TABLE = "rfc2119-table-assertion"
ASSERTION_INLINE = "rfc2119-assertion"
ASSERTION_DEFAULT = "rfc2119-default-assertion"


@dataclass
class Assertion:
    """One assertion extracted from a LinkML schema element."""

    id: str  # stable HTML id, e.g. "td-thing-id"
    source_class: str  # LinkML class name
    source_slot: Optional[str]  # slot name (None → class-level inline assertion)
    text: str  # description text (for CSV "Assertion" column)
    assertion_type: str = ASSERTION_TABLE
    schema_prefix: str = ""

    @property
    def clean_text(self) -> str:
        """Whitespace-normalised assertion text (mirrors cleanAssertionText in JS)."""
        t = re.sub(r"<[^>]+>", " ", self.text)
        t = re.sub(r"[\r\n]+", " ", t)
        t = re.sub(r"[ \t]+", " ", t).strip()
        return t


def _normalize_slot_name(slot_name: str) -> str:
    """
    Normalize a slot name for use in an assertion ID.
    """

    if slot_name == "@name":
        return "name"
    if slot_name in {"@context", "@type"}:
        return "at-" + slot_name[1:]
    return slot_name


def make_slot_assertion_id(prefix: str, class_name: str, slot_name: str) -> str:
    """
    Return the stable assertion ID for a vocabulary-term table row.

    Format:  td-vocab-<slot-normalized>--<ClassName>

    This is the single source of truth, called by tables.py when it emits a <tr>.
    """

    return f"td-vocab-{_normalize_slot_name(slot_name)}--{class_name}"


def extract_html_assertions(html_path: Path) -> List[Assertion]:
    """
    Extract the assertion inventory from final generated index.html.
    """
    doc = html.fromstring(html_path.read_text(encoding="utf-8", errors="replace"))
    selectors = [
        f".{ASSERTION_INLINE}",
        f"tr.{ASSERTION_DEFAULT}",
        f"tr.{ASSERTION_TABLE}",
    ]
    assertions: List[Assertion] = []
    seen: set[str] = set()

    for selector in selectors:
        for element in doc.cssselect(selector):
            assertion_id = element.get("id")
            if not assertion_id:
                logging.warning("Skipping assertion without id in %s: %s", html_path, selector)
                continue
            if assertion_id in seen:
                logging.warning("Skipping duplicate assertion id %s in %s", assertion_id, html_path)
                continue
            seen.add(assertion_id)
            assertion_type = element.get("class") or selector.lstrip(".")
            assertions.append(
                Assertion(
                    id=assertion_id,
                    source_class="",
                    source_slot=None,
                    text=element.text_content(),
                    assertion_type=assertion_type,
                    schema_prefix="",
                )
            )

    assertions.sort(key=lambda a: a.id)
    logging.info("Extracted %d HTML assertions from %s", len(assertions), html_path)
    return assertions


def html_assertions_to_csv(
    html_path: Path,
    out_path: Path,
    extra_asserts_path: Optional[Path] = None,
) -> None:
    """Extract assertions from final HTML (and optional extra-asserts.html) and write CSV."""
    assertions = extract_html_assertions(html_path)
    extra_ids: set[str] = set()
    if extra_asserts_path and extra_asserts_path.exists():
        extra = extract_html_assertions(extra_asserts_path)
        extra_ids = {a.id for a in extra}
        seen = {a.id for a in assertions}
        for a in extra:
            if a.id not in seen:
                seen.add(a.id)
                assertions.append(a)
        assertions.sort(key=lambda a: a.id)
        logging.info("Merged %d extra assertions from %s", len(extra), extra_asserts_path)
    assertions_to_csv(assertions, out_path)
    problems = validate_html_assertion_inventory(html_path, out_path, extra_ids=extra_ids)
    if problems:
        raise GenerationError(f"{html_path}: assertion inventory is inconsistent:\n" + "\n".join(problems))


def _assertion_elements(doc) -> list:
    selectors = [
        f".{ASSERTION_INLINE}",
        f"tr.{ASSERTION_DEFAULT}",
        f"tr.{ASSERTION_TABLE}",
    ]
    elements = []
    for selector in selectors:
        elements.extend(doc.cssselect(selector))
    return elements


def _csv_assertion_ids(csv_path: Path) -> set[str]:
    with csv_path.open(newline="", encoding="utf-8") as fh:
        return {row["ID"] for row in csv.DictReader(fh) if row.get("ID")}


def validate_html_assertion_inventory(
    html_path: Path,
    csv_path: Optional[Path] = None,
    extra_ids: Optional[set[str]] = None,
) -> List[str]:
    """Return compatibility problems for the final HTML assertion inventory."""
    doc = html.fromstring(html_path.read_text(encoding="utf-8", errors="replace"))
    elements = _assertion_elements(doc)
    ids = [element.get("id") for element in elements if element.get("id")]
    problems: List[str] = []

    missing = len(elements) - len(ids)
    if missing:
        problems.append(f"{missing} assertion element(s) are missing id attributes")

    duplicate_ids = sorted({assertion_id for assertion_id in ids if ids.count(assertion_id) > 1})
    if duplicate_ids:
        problems.append(f"duplicate assertion ids: {', '.join(duplicate_ids[:20])}")

    foreign_prefix_ids = sorted(
        assertion_id
        for assertion_id in ids
        if assertion_id.startswith(("jsonschema-vocab-", "wotsec-vocab-", "hctl-vocab-"))
    )
    if foreign_prefix_ids:
        problems.append(f"foreign table assertion prefixes: {', '.join(foreign_prefix_ids[:20])}")

    if csv_path is not None:
        html_ids = set(ids)
        csv_ids = _csv_assertion_ids(csv_path)
        missing_from_csv = sorted(html_ids - csv_ids)
        extra_in_csv = sorted(csv_ids - html_ids - (extra_ids or set()))
        if missing_from_csv:
            problems.append(f"csv missing html assertion ids: {', '.join(missing_from_csv[:20])}")
        if extra_in_csv:
            problems.append(f"csv has ids not present in html: {', '.join(extra_in_csv[:20])}")

    return problems


def assertions_to_csv(assertions: List[Assertion], out_path: Path) -> None:
    """
    Write assertions.csv with columns "ID","Status","Assertion".
    Matches the format produced by extractFile.js.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, quoting=csv.QUOTE_ALL)
        writer.writerow(["ID", "Status", "Assertion"])
        for a in assertions:
            writer.writerow([a.id, "null", a.clean_text])
    logging.info("Wrote %d assertions to %s", len(assertions), out_path)

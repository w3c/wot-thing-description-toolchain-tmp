"""Generate stable assertion IDs from LinkML schemas and produce assertions.csv.

Mirrors what extractFile.js does for the SPARQL/STTL-based WoT TD pipeline.

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
  <vocab_id_prefix>-vocab-<slot-name>--<ClassName>

``vocab_id_prefix`` is the manifest key ``spec.vocab_id_prefix``; it is the same for every section.

Special LinkML escape names are normalized to the historical TD anchors:
  @context  →  at-context
  @type     →  at-type
  @name     →  name

Examples with vocab_id_prefix "sen":
  Sensor.@context                →  sen-vocab-at-context--Sensor
  Sensor.@type                   →  sen-vocab-at-type--Sensor
  Sensor.unit                    →  sen-vocab-unit--Sensor

The IDs are guaranteed stable as long as the schema class/slot names
do not change – the same contract the SPARQL pipeline gave via ontology IRIs.
"""

from __future__ import annotations

import csv
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lxml import html

from ..errors import GenerationError
from ..schema_utils import load_schema_view

ASSERTION_TABLE = "rfc2119-table-assertion"
ASSERTION_INLINE = "rfc2119-assertion"
ASSERTION_DEFAULT = "rfc2119-default-assertion"


@dataclass
class Assertion:
    """One assertion extracted from a LinkML schema element."""

    id: str  # stable HTML id, e.g. "td-thing-id"
    source_class: str  # LinkML class name
    source_slot: str | None  # slot name (None → class-level inline assertion)
    text: str  # description text (for CSV "Assertion" column)
    assertion_type: str = ASSERTION_TABLE
    schema_prefix: str = ""

    @property
    def clean_text(self) -> str:
        """Whitespace-normalised assertion text (mirrors cleanAssertionText in JS)."""
        t = re.sub(r"<[^>]+>", " ", self.text)
        t = re.sub(r"[\r\n]+", " ", t)
        return re.sub(r"[ \t]+", " ", t).strip()


def _normalize_slot_name(slot_name: str) -> str:
    """Normalize a slot name for use in an assertion ID."""
    if slot_name == "@name":
        return "name"
    if slot_name in {"@context", "@type"}:
        return "at-" + slot_name[1:]
    return slot_name


def make_slot_assertion_id(vocab_id_prefix: str, class_name: str, slot_name: str) -> str:
    """Return the stable assertion ID for a vocabulary-term table row.

    Format:  <vocab_id_prefix>-vocab-<slot-normalized>--<ClassName>

    This is the single source of truth called by both tables.py (emitting <tr>)
    and extract_all_table_assertions() (building the CSV).

    Args:
        vocab_id_prefix: The manifest's ``spec.vocab_id_prefix``.
        class_name: Name of the class whose table holds the row.
        slot_name: Serialized name of the slot, i.e. its alias or else its name.

    Returns:
        The ID for the row's ``<tr id="...">`` attribute.
    """
    return f"{vocab_id_prefix}-vocab-{_normalize_slot_name(slot_name)}--{class_name}"


def make_class_assertion_id(prefix: str, class_name: str) -> str:
    """Return the stable assertion ID for a class-level inline assertion."""
    return f"{prefix}-vocab--{class_name}"


# RFC 2119 detection (inline/paragraph assertions only)
_RFC2119_RE = re.compile(
    r"\b(MUST(?:\s+NOT)?|SHALL(?:\s+NOT)?|SHOULD(?:\s+NOT)?|"
    r"REQUIRED|RECOMMENDED|MAY|OPTIONAL)\b"
)


def _has_rfc2119(text: str) -> bool:
    return bool(_RFC2119_RE.search(text or ""))


def _get_annotation_str(annotations: dict[str, Any], key: str) -> str | None:
    ann = annotations.get(key)
    if ann is None:
        return None
    return str(getattr(ann, "value", ann))


def _is_inline_assertion(annotations: dict[str, Any], description: str) -> bool:
    explicit = _get_annotation_str(annotations, "is_assertion")
    if explicit and explicit.lower() == "true":
        return True
    return _has_rfc2119(description or "")


def _inline_assertion_type(annotations: dict[str, Any]) -> str:
    val = _get_annotation_str(annotations, "assertion_type")
    if val in (ASSERTION_TABLE, ASSERTION_INLINE, ASSERTION_DEFAULT):
        return val
    return ASSERTION_INLINE


def extract_all_table_assertions(
    section_schemas: dict[str, Path],
    prefix_map: dict[str, str],
    vocab_id_prefix: str,
) -> list[Assertion]:
    """Walk every section schema and return one Assertion per (class, slot) pair.

    That is, one per vocabulary-term table row.

    ALL table rows are assertions regardless of whether their description
    contains RFC 2119 keywords.

    section_schemas:
        Ordered dict of section_id → schema Path (from Config.section_schemas).
    prefix_map:
        Maps schema file stem → short ID prefix (e.g. "thing_description" → "td").
    vocab_id_prefix:
        The manifest's ``spec.vocab_id_prefix``, shared by the IDs of all sections.

    Raises:
        SchemaError: A section schema is not a file or is not valid YAML.
    """
    assertions: list[Assertion] = []
    seen: set[str] = set()

    for _section_id, schema_path in section_schemas.items():
        prefix = prefix_map.get(schema_path.stem, schema_path.stem)

        # merge_imports=False: only classes defined in THIS file,
        # matching how generators.respec builds file_to_classes.
        sv = load_schema_view(schema_path, merge_imports=False)

        for class_name, class_def in sv.all_classes().items():
            slot_names = list(getattr(class_def, "slots", None) or [])
            slot_names.extend((getattr(class_def, "attributes", None) or {}).keys())

            seen_slots: set[str] = set()
            for slot_name in slot_names:
                if slot_name in seen_slots:
                    continue
                seen_slots.add(slot_name)
                aid = make_slot_assertion_id(vocab_id_prefix, class_name, slot_name)
                if aid in seen:
                    continue
                seen.add(aid)

                try:
                    slot_def = sv.induced_slot(slot_name, class_name)
                except ValueError:
                    # A module may list a slot that only the schema importing it defines.
                    desc = ""
                else:
                    desc = getattr(slot_def, "description", "") or ""

                assertions.append(
                    Assertion(
                        id=aid,
                        source_class=class_name,
                        source_slot=slot_name,
                        text=desc,
                        assertion_type=ASSERTION_TABLE,
                        schema_prefix=prefix,
                    )
                )

    assertions.sort(key=lambda a: a.id)
    logging.info("Extracted %d table assertions across all section schemas", len(assertions))
    return assertions


def extract_inline_assertions(
    section_schemas: dict[str, Path],
    prefix_map: dict[str, str],
) -> list[Assertion]:
    """Extract class-level *inline* assertions (.rfc2119-assertion / .rfc2119-default-assertion).

    That is, text that appears in the prose outside of vocabulary tables and contains RFC 2119 language
    or is explicitly annotated with ``is_assertion: true``.

    Raises:
        SchemaError: A section schema is not a file or is not valid YAML.
    """
    assertions: list[Assertion] = []
    seen: set[str] = set()

    for _section_id, schema_path in section_schemas.items():
        prefix = prefix_map.get(schema_path.stem, schema_path.stem)
        sv = load_schema_view(schema_path, merge_imports=False)

        for class_name, class_def in sv.all_classes().items():
            annotations = getattr(class_def, "annotations", None) or {}
            raw_desc = getattr(class_def, "description", "") or ""
            if _is_inline_assertion(annotations, raw_desc):
                aid = make_class_assertion_id(prefix, class_name)
                if aid not in seen:
                    seen.add(aid)
                    assertions.append(
                        Assertion(
                            id=aid,
                            source_class=class_name,
                            source_slot=None,
                            text=raw_desc,
                            assertion_type=_inline_assertion_type(annotations),
                            schema_prefix=prefix,
                        )
                    )

    assertions.sort(key=lambda a: a.id)
    return assertions


def extract_html_assertions(html_path: Path) -> list[Assertion]:
    """Extract the assertion inventory from final generated index.html."""
    doc = html.fromstring(html_path.read_text(encoding="utf-8", errors="replace"))
    selectors = [
        f".{ASSERTION_INLINE}",
        f"tr.{ASSERTION_DEFAULT}",
        f"tr.{ASSERTION_TABLE}",
    ]
    assertions: list[Assertion] = []
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
    extra_asserts_path: Path | None = None,
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
    pending_path = out_path.with_name(out_path.name + ".pending")
    assertions_to_csv(assertions, pending_path)
    try:
        problems = validate_html_assertion_inventory(html_path, pending_path, extra_ids=extra_ids)
        if problems:
            raise GenerationError(f"Assertion inventory of {html_path} is invalid:\n" + "\n".join(problems))
        pending_path.replace(out_path)
    finally:
        pending_path.unlink(missing_ok=True)


def _assertion_elements(doc: html.HtmlElement) -> list[html.HtmlElement]:
    selectors = [
        f".{ASSERTION_INLINE}",
        f"tr.{ASSERTION_DEFAULT}",
        f"tr.{ASSERTION_TABLE}",
    ]
    elements: list[html.HtmlElement] = []
    for selector in selectors:
        elements.extend(doc.cssselect(selector))
    return elements


def _csv_assertion_ids(csv_path: Path) -> set[str]:
    with csv_path.open(newline="", encoding="utf-8") as fh:
        return {row["ID"] for row in csv.DictReader(fh) if row.get("ID")}


def validate_html_assertion_inventory(
    html_path: Path,
    csv_path: Path | None = None,
    extra_ids: set[str] | None = None,
) -> list[str]:
    """Return compatibility problems for the final HTML assertion inventory."""
    doc = html.fromstring(html_path.read_text(encoding="utf-8", errors="replace"))
    elements = _assertion_elements(doc)
    ids = [element.get("id") for element in elements if element.get("id")]
    problems: list[str] = []

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


def assertions_to_csv(assertions: list[Assertion], out_path: Path) -> None:
    """Write assertions.csv with columns "ID","Status","Assertion".

    Matches the format produced by extractFile.js.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, quoting=csv.QUOTE_ALL)
        writer.writerow(["ID", "Status", "Assertion"])
        for a in assertions:
            writer.writerow([a.id, "null", a.clean_text])
    logging.info("Wrote %d assertions to %s", len(assertions), out_path)

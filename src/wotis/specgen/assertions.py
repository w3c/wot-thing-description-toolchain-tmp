"""
assertions.py – Generate stable assertion IDs from LinkML schemas and
produce assertions.csv, mirroring what extractFile.js does for the
SPARQL/STTL-based WoT TD pipeline.

How assertions work in the WoT TD spec HTML
────────────────────────────────────────────
The spec has three assertion CSS classes that extractFile.js selects:

  .rfc2119-assertion          – standalone paragraphs / spans
  .rfc2119-default-assertion  – standalone paragraphs / spans (default values)
  .rfc2119-table-assertion    – <tr> rows in vocabulary tables

Every vocabulary-term row in every generated <table class="def numbered">
already carries class="rfc2119-table-assertion".  What was missing is the
stable `id` attribute on those <tr> elements.

Stable ID convention (table rows)
───────────────────────────────────
  <schema-prefix>-<ClassName-kebab>-<slot-name-kebab>

Special characters in slot names are stripped:
  @context  →  context
  @type     →  type

Examples (thing_description.yaml, prefix "td"):
  Thing.@context   →  td-thing-context
  Thing.@type      →  td-thing-type
  Thing.id         →  td-thing-id
  Thing.title      →  td-thing-title

The IDs are guaranteed stable as long as the schema class/slot names
do not change – the same contract the SPARQL pipeline gave via ontology IRIs.

Public API
──────────
  make_slot_assertion_id(prefix, class_name, slot_name) -> str
      Pure function; used by tables.py when rendering each <tr>.

  extract_all_table_assertions(section_schemas, prefix_map) -> list[Assertion]
      Walks all section schemas and returns every (class, slot) pair as an
      Assertion, regardless of RFC 2119 keywords in the description.

  assertions_to_csv(assertions, out_path)
      Writes "ID","Status","Assertion" CSV compatible with extractFile.js output.
"""

from __future__ import annotations

import csv
import re
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from linkml_runtime.utils.schemaview import SchemaView


ASSERTION_TABLE   = "rfc2119-table-assertion"
ASSERTION_INLINE  = "rfc2119-assertion"
ASSERTION_DEFAULT = "rfc2119-default-assertion"


@dataclass
class Assertion:
    """One assertion extracted from a LinkML schema element."""

    id: str                          # stable HTML id, e.g. "td-thing-id"
    source_class: str                # LinkML class name
    source_slot: Optional[str]       # slot name (None → class-level inline assertion)
    text: str                        # description text (for CSV "Assertion" column)
    assertion_type: str = ASSERTION_TABLE
    schema_prefix: str = ""

    @property
    def clean_text(self) -> str:
        """CSV-safe, whitespace-normalised assertion text (mirrors cleanAssertionText in JS)."""
        t = re.sub(r"<[^>]+>", " ", self.text)
        t = re.sub(r"[\r\n]+", " ", t)
        t = re.sub(r"[ \t]+", " ", t).strip()
        t = t.replace('"', '""')
        return t


# ID generation
def _normalize_slot_name(slot_name: str) -> str:
    """
    Normalize a slot name for use in an assertion ID.

    Rules:
      - Leading '@' → 'at-'   (@type → at-type, @context → at-context)
      - All other characters left as-is (camelCase preserved, no kebab conversion)

    Examples:
      @type            → at-type
      @context         → at-context
      uriVariables     → uriVariables
      securityDefinitions → securityDefinitions
    """
    if slot_name.startswith("@"):
        return "at-" + slot_name[1:]
    return slot_name


def make_slot_assertion_id(prefix: str, class_name: str, slot_name: str) -> str:
    """
    Return the stable assertion ID for a vocabulary-term table row.

    Format:  <prefix>-vocab-<slot-normalized>--<ClassName>

    e.g.:
      make_slot_assertion_id("td", "Thing", "uriVariables")
          → "td-vocab-uriVariables--Thing"
      make_slot_assertion_id("td", "InteractionAffordance", "@type")
          → "td-vocab-at-type--InteractionAffordance"
      make_slot_assertion_id("td", "Thing", "@context")
          → "td-vocab-at-context--Thing"
      make_slot_assertion_id("wotsec", "SecurityScheme", "scheme")
          → "wotsec-vocab-scheme--SecurityScheme"

    This is the single source of truth called by both tables.py (emitting <tr>)
    and extract_all_table_assertions() (building the CSV).
    """
    return f"{prefix}-vocab-{_normalize_slot_name(slot_name)}--{class_name}"


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


def _get_annotation_str(annotations: dict, key: str) -> Optional[str]:
    ann = annotations.get(key)
    if ann is None:
        return None
    return str(getattr(ann, "value", ann))


def _is_inline_assertion(annotations: dict, description: str) -> bool:
    explicit = _get_annotation_str(annotations, "is_assertion")
    if explicit and explicit.lower() == "true":
        return True
    return _has_rfc2119(description or "")


def _inline_assertion_type(annotations: dict) -> str:
    val = _get_annotation_str(annotations, "assertion_type")
    if val in (ASSERTION_TABLE, ASSERTION_INLINE, ASSERTION_DEFAULT):
        return val
    return ASSERTION_INLINE



def extract_all_table_assertions(
    section_schemas: Dict[str, Path],
    prefix_map: Dict[str, str],
) -> List[Assertion]:
    """
    Walk every section schema and return one Assertion per (class, slot) pair –
    i.e. one per vocabulary-term table row.

    ALL table rows are assertions regardless of whether their description
    contains RFC 2119 keywords.  This matches how extractFile.js works:
    it selects ALL .rfc2119-table-assertion elements unconditionally.

    Parameters
    ----------
    section_schemas:
        Ordered dict of section_id → schema Path (from Config.section_schemas).
    prefix_map:
        Maps schema file stem → short ID prefix (e.g. "thing_description" → "td").
    """
    assertions: List[Assertion] = []
    seen: set[str] = set()

    for _section_id, schema_path in section_schemas.items():
        if not schema_path.exists():
            logging.warning("Skipping missing schema for assertions: %s", schema_path)
            continue

        prefix = prefix_map.get(schema_path.stem, schema_path.stem)

        try:
            # merge_imports=False: only classes defined in THIS file,
            # matching how respec_doc_generator builds file_to_classes.
            sv = SchemaView(str(schema_path), merge_imports=False)
        except Exception as exc:
            logging.error("Cannot load %s for assertion extraction: %s", schema_path, exc)
            continue

        for class_name in sv.all_classes():
            for slot_name in (sv.all_slots(class_name) or {}):
                aid = make_slot_assertion_id(prefix, class_name, slot_name)
                if aid in seen:
                    continue
                seen.add(aid)

                try:
                    slot_def = sv.induced_slot(slot_name, class_name)
                    desc = getattr(slot_def, "description", "") or ""
                except Exception:
                    desc = ""

                assertions.append(Assertion(
                    id=aid,
                    source_class=class_name,
                    source_slot=slot_name,
                    text=desc,
                    assertion_type=ASSERTION_TABLE,
                    schema_prefix=prefix,
                ))

    assertions.sort(key=lambda a: a.id)
    logging.info("Extracted %d table assertions across all section schemas", len(assertions))
    return assertions


def extract_inline_assertions(
    section_schemas: Dict[str, Path],
    prefix_map: Dict[str, str],
) -> List[Assertion]:
    """
    Extract class-level *inline* assertions (.rfc2119-assertion /
    .rfc2119-default-assertion) – text that appears in the prose outside of
    vocabulary tables and contains RFC 2119 language or is explicitly annotated
    with ``is_assertion: true``.
    """
    assertions: List[Assertion] = []
    seen: set[str] = set()

    for _section_id, schema_path in section_schemas.items():
        if not schema_path.exists():
            continue
        prefix = prefix_map.get(schema_path.stem, schema_path.stem)
        try:
            sv = SchemaView(str(schema_path), merge_imports=False)
        except Exception as exc:
            logging.error("Cannot load %s for inline assertion extraction: %s", schema_path, exc)
            continue

        for class_name, class_def in sv.all_classes().items():
            annotations = getattr(class_def, "annotations", None) or {}
            raw_desc = getattr(class_def, "description", "") or ""
            if _is_inline_assertion(annotations, raw_desc):
                aid = make_class_assertion_id(prefix, class_name)
                if aid not in seen:
                    seen.add(aid)
                    assertions.append(Assertion(
                        id=aid,
                        source_class=class_name,
                        source_slot=None,
                        text=raw_desc,
                        assertion_type=_inline_assertion_type(annotations),
                        schema_prefix=prefix,
                    ))

    assertions.sort(key=lambda a: a.id)
    return assertions


def extract_all_assertions(
    section_schemas: Dict[str, Path],
    prefix_map: Dict[str, str],
) -> List[Assertion]:
    """Combined, deduplicated, sorted list of table + inline assertions."""
    combined = (
        extract_all_table_assertions(section_schemas, prefix_map)
        + extract_inline_assertions(section_schemas, prefix_map)
    )
    seen: set[str] = set()
    unique: List[Assertion] = []
    for a in sorted(combined, key=lambda x: x.id):
        if a.id not in seen:
            seen.add(a.id)
            unique.append(a)
    return unique


# CSV output

def assertions_to_csv(assertions: List[Assertion], out_path: Path) -> None:
    """
    Write assertions.csv with columns "ID","Status","Assertion".
    Matches the format produced by extractFile.js exactly.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, quoting=csv.QUOTE_ALL)
        writer.writerow(["ID", "Status", "Assertion"])
        for a in assertions:
            writer.writerow([a.id, "null", a.clean_text])
    logging.info("Wrote %d assertions to %s", len(assertions), out_path)


# ── Schema prefix map

DEFAULT_PREFIX_MAP: Dict[str, str] = {
    "thing_description": "td",
    "hypermedia":        "hctl",
    "jsonschema":        "jsonschema",
    "wot_security":      "wotsec",
    "tm":                "tm",
}
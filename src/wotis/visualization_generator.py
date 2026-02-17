from __future__ import annotations

import logging
import shutil
import subprocess
import textwrap

from pathlib import Path
from typing import Optional

from linkml_runtime.utils.schemaview import SchemaView


def _normalize_range(rng: Optional[str]) -> str:
    """Map LinkML internal range names to the display form used in the TD spec."""
    if not rng:
        return ""
    mapping = {
        "Any":                "any type",
        "linkml:Any":         "any type",
        "uri":                "anyURI",
        "datetime":           "dateTime",
        "NonNegativeInteger": "unsignedInt",
        "decimal":            "double",
    }
    return mapping.get(rng, rng)


def _slot_assignment(slot_name: str, class_def, slot_def) -> str:
    """Return 'mandatory' or 'optional' following the same rules as tables.py."""
    usage = (class_def.slot_usage or {}).get(slot_name)
    if getattr(slot_def, "required", False) or (usage and getattr(usage, "required", False)):
        return "mandatory"
    min_value = getattr(slot_def, "minimum_value", None)
    if usage and getattr(usage, "minimum_value", None) is not None:
        min_value = usage.minimum_value
    try:
        if min_value is not None and float(min_value) > 0:
            return "mandatory"
    except Exception:
        pass
    return "optional"


def _slot_type_text(slot_name: str, slot_def, class_def, sv: SchemaView,
                    effective_range: Optional[str] = None) -> str:
    """
    Build the human-readable type string for a slot.
    Mirrors all rules from specgen/tables.py slot_type_text().
    """
    raw_rng = effective_range if effective_range else getattr(slot_def, "range", None)

    # 1. exactly_one_of / any_of on slot_usage
    usage = (getattr(class_def, "slot_usage", None) or {}).get(slot_name)
    choices = None
    if usage:
        choices = getattr(usage, "exactly_one_of", None) or getattr(usage, "any_of", None)
    if choices:
        pretty, seen = [], set()
        for alt in choices:
            alt_rng_raw = getattr(alt, "range", None) or raw_rng
            rng = _normalize_range(alt_rng_raw)
            mv = bool(getattr(alt, "multivalued", False))
            if mv:
                p = ("Array" if (not getattr(alt, "range", None) and slot_name == "@context")
                     else (f"Array of {rng}" if rng else "Array"))
            else:
                p = rng or ""
            if p and p not in seen:
                seen.add(p)
                pretty.append(p)
        return " or ".join(pretty)

    # 2. Enum range
    all_enums = sv.all_enums()
    if raw_rng in all_enums:
        enum_def = all_enums[raw_rng]
        pv_names = list(enum_def.permissible_values.keys())
        if pv_names:
            formatted = (f"{', '.join(pv_names[:-1])}, or {pv_names[-1]}"
                         if len(pv_names) > 1 else pv_names[0])
            is_uri_enum = (
                getattr(enum_def, "enum_uri", None) in ["linkml:uri", "anyURI"]
                or (raw_rng or "").lower() == "uri"
            )
            return (f"anyURI (one of {formatted})" if is_uri_enum
                    else f"string (e.g., {formatted})")
        return "string"

    # 3. Standard fallback
    rng = _normalize_range(raw_rng)
    if not rng:
        return ""
    if getattr(slot_def, "inlined", False):
        return f"Map of {rng}"
    if getattr(slot_def, "multivalued", False):
        return f"Array of {rng}"
    return rng


def _require_dot() -> bool:
    """Return True if Graphviz 'dot' is available; otherwise warn once."""
    if shutil.which("dot"):
        return True
    logging.warning("Graphviz 'dot' not found on PATH. Skipping UML diagram generation.")
    return False


def _dot_to_svg(dot_source: str, out_svg: Path) -> None:
    """Write DOT source to a temporary file and convert to SVG via Graphviz."""
    out_svg.parent.mkdir(parents=True, exist_ok=True)
    tmp_dot = out_svg.with_suffix(out_svg.suffix + ".dot")
    tmp_dot.write_text(dot_source, encoding="utf-8")
    subprocess.run(["dot", "-Tsvg", str(tmp_dot), "-o", str(out_svg)], check=True)


def _escape_dot(text: str) -> str:
    """Escape characters that are special in DOT HTML-like labels."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _build_dot_from_schema_view(sv: SchemaView) -> str:
    """
    Build a Graphviz DOT string from a SchemaView object.

    Uses SchemaView directly instead of DotGenerator / SchemaLoader to avoid:
      - "Conflicting URIs" errors when schemas redefine linkml built-in types
        under a different namespace URI.
      - "unknown slot" errors when sub-schemas reference slots that are only
        defined in an imported parent schema.

    Rendering rules:
      - Slots whose range is a primitive type  shown as a row in the class table.
      - Slots whose range is another class     shown as a labelled edge only,
        NOT as a table row (avoids duplication between table and graph).
      - Inheritance (is_a)                     open-arrowhead edge (grey).
      - Association                            open-arrowhead edge (orange).
    """
    all_classes = sv.all_classes()

    lines = [
        'digraph schema {',
        '  graph [rankdir=BT, fontname="Helvetica", fontsize=11, bgcolor="white"];',
        '  node  [fontname="Helvetica", fontsize=10, shape=none, margin=0];',
        '  edge  [fontname="Helvetica", fontsize=9, color="#555555"];',
        '',
    ]

    # 1. One HTML-like table node per class
    for class_name, class_def in all_classes.items():
        try:
            class_def = sv.get_class(class_name)
            slot_names = list(class_def.slots or []) + list(
                (class_def.attributes or {}).keys()
            )
        except Exception:
            class_def = all_classes[class_name]
            slot_names = []

        attr_rows = ""
        for sname in slot_names:
            try:
                slot = sv.get_slot(sname) or (class_def.attributes or {}).get(sname)
                if slot is None:
                    continue

                # Resolve effective range: slot_usage overrides slot_def
                usage = (class_def.slot_usage or {}).get(sname)
                effective_range = (
                    getattr(usage, "range", None) or getattr(slot, "range", None)
                )

                # Slots whose range is another class -> edge only, not a table row
                if effective_range and effective_range in all_classes:
                    continue

                # Respect spec_exclude annotation
                ann = dict(getattr(slot, "annotations", None) or {})
                if sname in (class_def.attributes or {}):
                    ann.update(getattr(class_def.attributes[sname], "annotations", None) or {})
                spec_exclude = ann.get("spec_exclude")
                if spec_exclude and str(getattr(spec_exclude, "value", spec_exclude)).lower() == "true":
                    continue

                type_text = _escape_dot(_slot_type_text(
                    slot_name=sname,
                    slot_def=slot,
                    class_def=class_def,
                    sv=sv,
                    effective_range=effective_range,
                ))
                assignment = _slot_assignment(sname, class_def, slot)
                mandatory_marker = " <I>(mandatory)</I>" if assignment == "mandatory" else ""
                display_name = "name" if sname == "@name" else sname

                attr_rows += (
                    f'<TR><TD ALIGN="LEFT">'
                    f'{_escape_dot(display_name)}&nbsp;:&nbsp;{type_text}'
                    f'{mandatory_marker}'
                    f'</TD></TR>\n'
                )
            except Exception as e:
                logging.debug("Skipping slot %s on %s: %s", sname, class_name, e)
                continue

        is_abstract = getattr(class_def, "abstract", False)
        header_bg = "white" if is_abstract else "#add8e6"

        label = textwrap.dedent(f"""\
            <<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2" BGCOLOR="white">
              <TR><TD BGCOLOR="{header_bg}"><B><FONT COLOR="black">{_escape_dot(class_name)}</FONT></B></TD></TR>
              {attr_rows}</TABLE>>""")

        lines.append(f'  "{class_name}" [label={label}];')

    lines.append('')

    # 2. Edges
    # 2a. Inheritance (is_a)
    for class_name, class_def in all_classes.items():
        if class_def.is_a:
            lines.append(
                f'  "{class_name}" -> "{class_def.is_a}" '
                f'[arrowhead=empty, style=solid, color="#555555"];'
            )

    # 2b. Association edges for slots whose range is another class
    emitted_edges: set[tuple[str, str, str]] = set()
    for class_name, class_def in all_classes.items():
        slot_names = list(class_def.slots or []) + list(
            (class_def.attributes or {}).keys()
        )
        for sname in slot_names:
            try:
                slot = sv.get_slot(sname) or (class_def.attributes or {}).get(sname)
                if slot is None:
                    continue
                usage = (class_def.slot_usage or {}).get(sname)
                effective_range = (
                    getattr(usage, "range", None) or getattr(slot, "range", None)
                )
                if effective_range and effective_range in all_classes:
                    mult = "0..*" if getattr(slot, "multivalued", False) else "0..1"
                    edge_key = (class_name, effective_range, sname)
                    if edge_key not in emitted_edges:
                        emitted_edges.add(edge_key)
                        lines.append(
                            f'  "{class_name}" -> "{effective_range}" '
                            f'[label="{_escape_dot(sname)} {mult}", '
                            f'arrowhead=open, style=solid, color="#cc6600"];'
                        )
            except Exception:
                continue

    lines.append('}')
    return '\n'.join(lines)


# ── Public entry point ────────────────────────────────────────────────────────

def generate_visualizations(schemas_dir: Path, visualization_dir: Path) -> None:
    """
    Generate one SVG UML diagram per LinkML schema file.

    Output mapping:
      schemas/thing_description.yaml -> visualization/td.svg
      schemas/jsonschema.yaml        -> visualization/jsonschema.svg
      schemas/wot_security.yaml      -> visualization/wotsec.svg
      schemas/hypermedia.yaml        -> visualization/hctl.svg
    """
    if not _require_dot():
        return

    mapping = {
        "thing_description.yaml": ("td.svg",        "TD core vocabulary"),
        "jsonschema.yaml":        ("jsonschema.svg", "Data schema vocabulary"),
        "wot_security.yaml":      ("wotsec.svg",     "WoT security vocabulary"),
        "hypermedia.yaml":        ("hctl.svg",       "Hypermedia controls vocabulary"),
    }

    visualization_dir.mkdir(parents=True, exist_ok=True)

    for filename, (target_svg, label) in mapping.items():
        schema_path = schemas_dir / filename
        out_svg = visualization_dir / target_svg

        if not schema_path.exists():
            logging.warning(
                "Schema not found for diagram (%s). Skipping %s.", schema_path, target_svg
            )
            continue

        try:
            logging.info(
                "Generating UML diagram for %s -> %s (%s)", filename, out_svg.name, label
            )
            sv = SchemaView(str(schema_path), merge_imports=True)
            dot_source = _build_dot_from_schema_view(sv)
            _dot_to_svg(dot_source, out_svg)
            logging.info("Saved %s", out_svg)
        except Exception as e:
            logging.error(
                "Failed to generate %s from %s: %s",
                out_svg.name, schema_path, e,
                exc_info=True,
            )
from __future__ import annotations

import logging
import shutil
import subprocess
import textwrap
from pathlib import Path
from collections import defaultdict
from typing import Dict, Iterable, Optional, Set, Tuple

from linkml_runtime.utils.schemaview import SchemaView

# Always render these classes as header-only (no attribute/slot rows) even if they are local to the schema.
HIDE_DETAILS_FOR: Set[str] = {"MultiLanguage"}

HEADER_BLUE = "#8ECBF0"
ROW_BLUE = "#DDEEFE"
EXTERNAL_GRAY = "#f2f2f2"
TYPE_ORANGE = "#CE7B63"


def _normalize_range(rng: Optional[str]) -> str:
    """Map LinkML internal range names to the display form used in the TD spec."""
    if not rng:
        return ""
    mapping = {
        "Any": "any type",
        "linkml:Any": "any type",
        "uri": "anyURI",
        "datetime": "dateTime",
        "NonNegativeInteger": "unsignedInt",
        "decimal": "double",
    }
    return mapping.get(rng, rng)


def _slot_assignment(slot_name: str, class_def, slot_def) -> str:
    """Return 'mandatory' or 'optional' following the same rules as spec generation."""
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


def _slot_type_text(
    slot_name: str,
    slot_def,
    class_def,
    sv: SchemaView,
    effective_range: Optional[str] = None,
) -> str:
    """
    Build the human-readable type string for a slot.
    Mirrors rules from specgen/tables.py slot_type_text().
    """
    raw_rng = effective_range if effective_range else getattr(slot_def, "range", None)

    # exactly_one_of / any_of on slot_usage
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
                p = (
                    "Array"
                    if (not getattr(alt, "range", None) and slot_name == "@context")
                    else (f"Array of {rng}" if rng else "Array")
                )
            else:
                p = rng or ""
            if p and p not in seen:
                seen.add(p)
                pretty.append(p)
        return " or ".join(pretty)

    # Enum range
    all_enums = sv.all_enums()
    if raw_rng in all_enums:
        enum_def = all_enums[raw_rng]
        pv_names = list(enum_def.permissible_values.keys())
        if pv_names:
            formatted = (
                f"{', '.join(pv_names[:-1])}, or {pv_names[-1]}"
                if len(pv_names) > 1
                else pv_names[0]
            )
            is_uri_enum = (
                getattr(enum_def, "enum_uri", None) in ["linkml:uri", "anyURI"]
                or (raw_rng or "").lower() == "uri"
            )
            return (
                f"anyURI (one of {formatted})"
                if is_uri_enum
                else f"string (e.g., {formatted})"
            )
        return "string"

    # Standard fallback
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
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _build_children_index(all_classes: Dict[str, object]) -> Dict[str, Set[str]]:
    """Build parent -> children index based on is_a."""
    children: Dict[str, Set[str]] = {}
    for cname, cdef in all_classes.items():
        parent = getattr(cdef, "is_a", None)
        if parent:
            children.setdefault(parent, set()).add(cname)
    return children


def _descendants_of(roots: Iterable[str], children_index: Dict[str, Set[str]]) -> Set[str]:
    """Return transitive descendants of given roots (excluding roots themselves)."""
    roots = set(roots)
    out: Set[str] = set()
    stack = list(roots)
    while stack:
        r = stack.pop()
        for ch in children_index.get(r, set()):
            if ch not in out and ch not in roots:
                out.add(ch)
                stack.append(ch)
    return out


def _collapse_to_visible_ancestor(
    target: str,
    all_classes: Dict[str, object],
    *,
    hidden: Set[str],
    stop_at: Set[str],
) -> Optional[str]:
    """
    If target is hidden, walk up is_a chain until we hit a visible ancestor.
    Returns visible ancestor name, or None if nothing found.
    """
    cur = target
    while cur in hidden:
        parent = getattr(all_classes.get(cur), "is_a", None)
        if not parent:
            return None
        cur = parent
        if cur in stop_at and cur not in hidden:
            return cur
    return cur if cur not in hidden else None


def _detect_kept_external_bases(
    sv: SchemaView,
    all_classes: Dict[str, object],
    *,
    local_classes: Set[str],
) -> Set[str]:
    """
    Decide which external/imported classes should remain visible (header-only),
    while omitting their descendants.

    Strategy:
      - external classes referenced by local classes via:
        (a) local is_a external
        (b) local slot/attribute range external
    Fallback:
      - keep all external classes as bases if nothing detected
    """
    external_classes = set(all_classes.keys()) - set(local_classes)
    referenced_externals: Set[str] = set()

    # local -> external via inheritance
    for cname, cdef in all_classes.items():
        if cname in local_classes:
            parent = getattr(cdef, "is_a", None)
            if parent and parent in external_classes:
                referenced_externals.add(parent)

    # local -> external via slot/attribute ranges
    for cname, cdef in all_classes.items():
        if cname not in local_classes:
            continue
        slot_names = list(getattr(cdef, "slots", None) or []) + list(
            (getattr(cdef, "attributes", None) or {}).keys()
        )
        for sname in slot_names:
            try:
                if sname in (getattr(cdef, "attributes", None) or {}):
                    slot = cdef.attributes[sname]
                else:
                    slot = sv.get_slot(sname)
                if not slot:
                    continue
                usage = (getattr(cdef, "slot_usage", None) or {}).get(sname)
                rng = getattr(usage, "range", None) or getattr(slot, "range", None)
                if rng and rng in external_classes:
                    referenced_externals.add(rng)
            except Exception:
                continue

    return referenced_externals or external_classes


def _build_dot_from_schema_view(sv: SchemaView, *, local_classes: Set[str]) -> str:
    """
    Build a Graphviz DOT string from a (MERGED) SchemaView object.

    RULES:
      - External/imported classes: header-only, and MUST NOT emit outgoing edges.
      - Descendants of kept external bases via is_a: omitted entirely.
      - Local classes: show attributes (or slots if no attributes).
      - Slot ranges to classes: edges only.
      - If an edge target is hidden descendant: collapse to nearest visible ancestor.
      - Exception: MultiLanguage is ALWAYS header-only (no rows) even if local.
      - NEW: merge multiple edges between same src/dst with same cardinality into one edge with merged labels.
    """
    all_classes = sv.all_classes()

    kept_external_bases = _detect_kept_external_bases(sv, all_classes, local_classes=local_classes)
    children_index = _build_children_index(all_classes)
    hidden = _descendants_of(kept_external_bases, children_index)

    logging.info("=" * 80)
    logging.info("Schema ID: %s", sv.schema.id)
    logging.info("Total classes (post-merge): %d", len(all_classes))
    logging.info("Local classes (pre-merge): %d = %s", len(local_classes), sorted(local_classes))
    logging.info("Kept external bases (header-only): %s", sorted(kept_external_bases))
    logging.info("Hidden descendants of external bases: %d", len(hidden))
    logging.info("=" * 80)

    lines = [
        "digraph schema {",
        # layout
        '  graph [rankdir=BT, bgcolor="white", fontname="Helvetica", fontsize=11,',
        "         overlap=false, splines=true, concentrate=true,",
        "         nodesep=0.35, ranksep=0.65];",
        # nodes
        '  node  [fontname="Helvetica", fontsize=10, shape=none, margin=0];',
        # edges
        f'  edge  [fontname="Helvetica", fontsize=9, color="#555555", fontcolor="{TYPE_ORANGE}"];',
        "",
    ]

    # -------------------------
    # Nodes
    # -------------------------
    for class_name, class_def0 in all_classes.items():
        if class_name in hidden:
            continue
        if class_name not in local_classes and class_name not in kept_external_bases:
            continue

        try:
            class_def = sv.get_class(class_name)
        except Exception:
            class_def = class_def0

        is_external = class_name not in local_classes
        force_header_only = class_name in HIDE_DETAILS_FOR
        is_abstract = getattr(class_def, "abstract", False)

        attr_rows = ""

        # Only local + not forced header-only get their rows
        if (not is_external) and (not force_header_only):
            attr_names = list((class_def.attributes or {}).keys())
            if not attr_names:
                attr_names = list(class_def.slots or [])

            for sname in attr_names:
                try:
                    if sname in (class_def.attributes or {}):
                        slot = class_def.attributes[sname]
                    else:
                        slot = sv.get_slot(sname)

                    if slot is None:
                        continue

                    usage = (class_def.slot_usage or {}).get(sname)
                    effective_range = getattr(usage, "range", None) or getattr(slot, "range", None)

                    # class-to-class relations are edges, not rows
                    if effective_range and effective_range in all_classes:
                        continue

                    ann = dict(getattr(slot, "annotations", None) or {})
                    spec_exclude = ann.get("spec_exclude")
                    if spec_exclude and str(getattr(spec_exclude, "value", spec_exclude)).lower() == "true":
                        continue

                    type_text = _escape_dot(
                        _slot_type_text(
                            slot_name=sname,
                            slot_def=slot,
                            class_def=class_def,
                            sv=sv,
                            effective_range=effective_range,
                        )
                    )

                    assignment = _slot_assignment(sname, class_def, slot)
                    mandatory_marker = " <I>(mandatory)</I>" if assignment == "mandatory" else ""
                    display_name = "name" if sname == "@name" else sname

                    # NOTE: CELLBORDER=1 gives visible row separators
                    attr_rows += (
                        f'<TR><TD ALIGN="LEFT" BGCOLOR="{ROW_BLUE}">'
                        f'{_escape_dot(display_name)}&nbsp;:&nbsp;'
                        f'<FONT COLOR="{TYPE_ORANGE}">{type_text}</FONT>'
                        f'{mandatory_marker}'
                        f"</TD></TR>\n"
                    )
                except Exception as e:
                    logging.debug("Skipping slot %s on %s: %s", sname, class_name, e)
                    continue

        # Styling
        if is_external:
            header_bg = EXTERNAL_GRAY
        else:
            header_bg = "white" if is_abstract else HEADER_BLUE

        header_text = _escape_dot(class_name)
        if is_external:
            header_text = f"<I>{header_text}</I>"

        label = textwrap.dedent(
            f"""\
            <<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3" BGCOLOR="white">
              <TR><TD BGCOLOR="{header_bg}"><B><FONT COLOR="black">{header_text}</FONT></B></TD></TR>
              {attr_rows}</TABLE>>"""
        )

        lines.append(f'  "{class_name}" [label={label}];')

    lines.append("")

    # -------------------------
    # Edges
    # -------------------------

    # Inheritance edges (is_a)
    # NOTE: You previously allowed kept_external_bases here; keeping your behavior.
    for class_name, class_def in all_classes.items():
        if class_name in hidden:
            continue
        if class_name not in local_classes and class_name not in kept_external_bases:
            continue

        parent = getattr(class_def, "is_a", None)
        if not parent:
            continue

        if parent in hidden:
            parent2 = _collapse_to_visible_ancestor(
                parent,
                all_classes,
                hidden=hidden,
                stop_at=kept_external_bases,
            )
            if not parent2:
                continue
            parent = parent2

        if parent in hidden:
            continue

        lines.append(
            f'  "{class_name}" -> "{parent}" '
            '[arrowhead=empty, style=solid, color="#555555"];'
        )

    # Association edges — only from local sources, merged by (src, dst, mult)
    edge_groups: Dict[Tuple[str, str, str], list[str]] = defaultdict(list)

    for class_name, class_def in all_classes.items():
        if class_name in hidden:
            continue
        if class_name not in local_classes:
            continue

        slot_names = list(getattr(class_def, "slots", None) or []) + list(
            (getattr(class_def, "attributes", None) or {}).keys()
        )

        for sname in slot_names:
            try:
                if sname in (getattr(class_def, "attributes", None) or {}):
                    slot = class_def.attributes[sname]
                else:
                    slot = sv.get_slot(sname)
                if slot is None:
                    continue

                usage = (class_def.slot_usage or {}).get(sname)
                effective_range = getattr(usage, "range", None) or getattr(slot, "range", None)

                # only class-to-class edges
                if not (effective_range and effective_range in all_classes):
                    continue

                # collapse hidden descendants to visible base
                if effective_range in hidden:
                    collapsed = _collapse_to_visible_ancestor(
                        effective_range,
                        all_classes,
                        hidden=hidden,
                        stop_at=kept_external_bases,
                    )
                    if not collapsed:
                        continue
                    effective_range = collapsed

                if effective_range in hidden:
                    continue

                mult = "0..*" if getattr(slot, "multivalued", False) else "0..1"
                edge_groups[(class_name, effective_range, mult)].append(sname)

            except Exception:
                continue

    # Emit merged association edges (AFTER collecting)
    for (src, dst, mult), labels in edge_groups.items():
        seen: Set[str] = set()
        uniq: list[str] = []
        for l in labels:
            if l not in seen:
                seen.add(l)
                uniq.append(l)

        merged_label = ", ".join(uniq)
        lines.append(
            f'  "{src}" -> "{dst}" '
            f'[label="{_escape_dot(merged_label)} {mult}", '
            f'arrowhead=open, style=solid, color="{TYPE_ORANGE}", fontcolor="{TYPE_ORANGE}"];'
        )

    lines.append("}")
    return "\n".join(lines)


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
        "thing_description.yaml": ("td.svg", "TD core vocabulary"),
        "jsonschema.yaml": ("jsonschema.svg", "Data schema vocabulary"),
        "wot_security.yaml": ("wotsec.svg", "WoT security vocabulary"),
        "hypermedia.yaml": ("hctl.svg", "Hypermedia controls vocabulary"),
    }

    visualization_dir.mkdir(parents=True, exist_ok=True)

    for filename, (target_svg, label) in mapping.items():
        schema_path = schemas_dir / filename
        out_svg = visualization_dir / target_svg

        if not schema_path.exists():
            logging.warning("Schema not found for diagram (%s). Skipping %s.", schema_path, target_svg)
            continue

        try:
            logging.info("Generating UML diagram for %s -> %s (%s)", filename, out_svg.name, label)

            sv_merged = SchemaView(str(schema_path), merge_imports=True)
            sv_unmerged = SchemaView(str(schema_path), merge_imports=False)
            local_classes: Set[str] = set((sv_unmerged.schema.classes or {}).keys())

            dot_source = _build_dot_from_schema_view(sv_merged, local_classes=local_classes)
            _dot_to_svg(dot_source, out_svg)
            logging.info("Saved %s", out_svg)

        except Exception as e:
            logging.error(
                "Failed to generate %s from %s: %s",
                out_svg.name, schema_path, e,
                exc_info=True,
            )

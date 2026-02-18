from __future__ import annotations

import logging
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from linkml_runtime.utils.schemaview import SchemaView


ORANGE = "#C83500"
BLUE_BORDER = "#8CCBF2"
BLUE_BG = "#DDEEFF"
HEADER_BG = "#8CCBF2"
GRAY_BG = "#F2F2F2"
GRAY_BORDER = "#8C8C8C"
SVG_FONT = "Courier"

HIDE_DETAILS_FOR: Set[str] = {"MultiLanguage"}
HIDE_CLASSES: Set[str] = {"Any", "linkml:Any"}


def _normalize_range(rng: Optional[str]) -> str:
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
    usage = (class_def.slot_usage or {}).get(slot_name)
    if getattr(slot_def, "required", False) or (usage and getattr(usage, "required", False)):
        return "mandatory"
    return "optional"


def _slot_type_text(
        slot_name: str,
        slot_def,
        class_def,
        sv: SchemaView,
        effective_range: Optional[str] = None,
) -> str:
    raw_rng = effective_range if effective_range else getattr(slot_def, "range", None)
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
            p = f"(Array of) {rng}" if mv and rng else (rng if rng else "")
            if p and p not in seen:
                seen.add(p)
                pretty.append(p)
        return " or ".join(pretty)

    all_enums = sv.all_enums()
    if raw_rng in all_enums:
        enum_def = all_enums[raw_rng]
        is_uri_enum = (getattr(enum_def, "enum_uri", None) in ["linkml:uri", "anyURI"]
                       or (raw_rng or "").lower() == "uri")
        return "anyURI" if is_uri_enum else "string"

    rng = _normalize_range(raw_rng)
    if not rng: return ""
    if getattr(slot_def, "multivalued", False): return f"(Array of) {rng}"
    return rng


def _format_type_html(type_text: str) -> str:
    parts = type_text.split(" or ")
    formatted_parts = []
    for p in parts:
        if p.startswith("(Array of) "):
            range_part = p.replace("(Array of) ", "")
            formatted_parts.append(
                f'<FONT COLOR="black">(Array of)</FONT> <FONT COLOR="{ORANGE}">{_escape_dot(range_part)}</FONT>')
        else:
            formatted_parts.append(f'<FONT COLOR="{ORANGE}">{_escape_dot(p)}</FONT>')
    return ' <FONT COLOR="black">or</FONT> '.join(formatted_parts)


def _require_dot() -> bool:
    return bool(shutil.which("dot"))


def _dot_to_svg(dot_source: str, out_svg: Path) -> None:
    out_svg.parent.mkdir(parents=True, exist_ok=True)
    tmp_dot = out_svg.with_suffix(out_svg.suffix + ".dot")
    tmp_dot.write_text(dot_source, encoding="utf-8")
    subprocess.run(["dot", "-Tsvg", str(tmp_dot), "-o", str(out_svg)], check=True)


def _escape_dot(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _induced_slot(sv: SchemaView, class_name: str, slot_name: str):
    try:
        s = sv.induced_slot(slot_name, class_name)
        return s if s is not None else sv.get_slot(slot_name)
    except Exception:
        return sv.get_slot(slot_name)


def _build_children_index(all_classes: Dict[str, object]) -> Dict[str, Set[str]]:
    children: Dict[str, Set[str]] = {}
    for cname, cdef in all_classes.items():
        parent = getattr(cdef, "is_a", None)
        if parent: children.setdefault(parent, set()).add(cname)
    return children


def _descendants_of(roots: Iterable[str], children_index: Dict[str, Set[str]]) -> Set[str]:
    roots = set(roots)
    out: Set[str] = set()
    stack = list(roots)
    while stack:
        r = stack.pop()
        for ch in children_index.get(r, set()):
            if ch not in out and ch not in roots: out.add(ch); stack.append(ch)
    return out


def _collapse_to_visible_ancestor(target: str, all_classes: Dict[str, object], *, hidden: Set[str],
                                  stop_at: Set[str]) -> Optional[str]:
    cur = target
    while cur in hidden:
        parent = getattr(all_classes.get(cur), "is_a", None)
        if not parent: return None
        cur = parent
        if cur in stop_at and cur not in hidden: return cur
    return cur if cur not in hidden else None


def _detect_kept_external_bases(sv: SchemaView, all_classes: Dict[str, object], *, local_classes: Set[str]) -> Set[str]:
    external_classes = set(all_classes.keys()) - set(local_classes)
    referenced_externals: Set[str] = set()
    for cname, cdef in all_classes.items():
        if cname in local_classes:
            parent = getattr(cdef, "is_a", None)
            if parent and parent in external_classes: referenced_externals.add(parent)
            slot_names = list(getattr(cdef, "slots", None) or []) + list(
                (getattr(cdef, "attributes", None) or {}).keys())
            for sname in slot_names:
                try:
                    slot = _induced_slot(sv, cname, sname)
                    if slot and slot.range and slot.range in external_classes: referenced_externals.add(slot.range)
                except Exception:
                    continue
    return referenced_externals or external_classes


def _build_dot_from_schema_view(sv: SchemaView, *, local_classes: Set[str]) -> str:
    all_classes = sv.all_classes()
    kept_external_bases = _detect_kept_external_bases(sv, all_classes, local_classes=local_classes)
    children_index = _build_children_index(all_classes)
    hidden = _descendants_of(kept_external_bases, children_index)

    def _is_visible(c: str) -> bool:
        return c not in HIDE_CLASSES and c not in hidden and (c in local_classes or c in kept_external_bases)

    lines: List[str] = [
        "digraph schema {",
        # Compact Vertical: Tighter nodesep/ranksep and zero margin
        f'  graph [rankdir=BT, bgcolor="white", splines=polyline, overlap=false, nodesep=0.5, ranksep=0.6, margin=0.1, concentrate=false, fontname="{SVG_FONT}"];',
        f'  node  [fontname="{SVG_FONT}", fontsize=10, shape=none, margin=0];',
        f'  edge  [fontname="{SVG_FONT}", fontsize=9, color="black"];',
        "",
    ]

    for class_name, class_def0 in all_classes.items():
        if not _is_visible(class_name): continue
        try:
            class_def = sv.get_class(class_name)
        except Exception:
            class_def = class_def0

        is_external = class_name not in local_classes

        attr_rows = ""
        if (not is_external) and (class_name not in HIDE_DETAILS_FOR):
            attr_names = list((class_def.attributes or {}).keys()) or list(class_def.slots or [])
            for sname in attr_names:
                slot = _induced_slot(sv, class_name, sname)
                if slot is None or (getattr(slot, "range", None) in all_classes) or (
                        getattr(slot, "range", None) in HIDE_CLASSES): continue

                type_text = _slot_type_text(sname, slot, class_def, sv, getattr(slot, "range", None))
                type_display = _format_type_html(type_text)
                assignment = _slot_assignment(sname, class_def, slot)
                mandatory_marker = " <I>(mandatory)</I>" if assignment == "mandatory" else ""
                display_name = "name" if sname == "@name" else sname

                attr_rows += (f'<TR><TD ALIGN="LEFT" BGCOLOR="{BLUE_BG}" COLOR="{BLUE_BORDER}" WIDTH="200">'
                              f'<FONT COLOR="{ORANGE}">{_escape_dot(display_name)}</FONT> : {type_display}{mandatory_marker}'
                              f'</TD></TR>\n')

        if is_external:
            label = (f'<<TABLE BORDER="0.5" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3" COLOR="{GRAY_BORDER}">'
                     f'<TR><TD BGCOLOR="{GRAY_BG}" WIDTH="200"><B><FONT COLOR="black"><I>{_escape_dot(class_name)}</I></FONT></B></TD></TR></TABLE>>')
        else:
            label = (f'<<TABLE BORDER="0.5" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3" COLOR="{BLUE_BORDER}">'
                     f'<TR><TD BGCOLOR="{HEADER_BG}" WIDTH="200"><B><FONT COLOR="{ORANGE}">{_escape_dot(class_name)}</FONT></B></TD></TR>'
                     f'{attr_rows}</TABLE>>')
        lines.append(f'  "{class_name}" [label={label}];')

    for child, cdef in all_classes.items():
        if not _is_visible(child): continue
        parent = getattr(cdef, "is_a", None)
        if parent:
            parent = _collapse_to_visible_ancestor(parent, all_classes, hidden=hidden, stop_at=kept_external_bases)
            if parent and _is_visible(parent):
                lines.append(f'  "{child}" -> "{parent}" [arrowhead=empty, color="{GRAY_BORDER}"];')

    edge_groups = defaultdict(list)
    for src, cdef in all_classes.items():
        if not _is_visible(src) or src not in local_classes: continue
        slots = list(getattr(cdef, "slots", None) or []) + list((getattr(cdef, "attributes", None) or {}).keys())
        for sname in slots:
            slot = _induced_slot(sv, src, sname)
            if not slot or not (getattr(slot, "range", None) in all_classes): continue
            dst = _collapse_to_visible_ancestor(getattr(slot, "range", None), all_classes, hidden=hidden,
                                                stop_at=kept_external_bases)
            if dst and _is_visible(dst):
                mult = "0..*" if getattr(slot, "multivalued", False) else "0..1"
                edge_groups[(src, dst, mult)].append(sname)

    for (src, dst, mult), labels in edge_groups.items():
        labels.sort(key=len)
        label_rows = "".join(
            f'<TR><TD ALIGN="LEFT"><FONT COLOR="{ORANGE}">{_escape_dot(l)}</FONT></TD></TR>' for l in labels)
        merged_label = f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="1">{label_rows}</TABLE>>'
        # Kept the improved cardinality distance but reduced minlen for compactness
        lines.append(
            f'  "{src}" -> "{dst}" [label={merged_label}, headlabel="{mult}", labeldistance=3.0, labelangle=20, minlen=1, arrowhead=open, color="black"];')

    lines.append("}")
    return "\n".join(lines)


def generate_visualizations(schemas_dir: Path, visualization_dir: Path) -> None:
    if not _require_dot():
        logging.error("Graphviz 'dot' executable not found.")
        return

    mapping = {
        "thing_description.yaml": "td.svg",
        "jsonschema.yaml": "jsonschema.svg",
        "wot_security.yaml": "wotsec.svg",
        "hypermedia.yaml": "hctl.svg"
    }

    visualization_dir.mkdir(parents=True, exist_ok=True)

    for filename, target_svg in mapping.items():
        path = schemas_dir / filename
        if not path.exists():
            continue
        try:
            sv_merged = SchemaView(str(path), merge_imports=True)
            sv_unmerged = SchemaView(str(path), merge_imports=False)
            local_classes = set((sv_unmerged.schema.classes or {}).keys())
            dot_source = _build_dot_from_schema_view(sv_merged, local_classes=local_classes)
            _dot_to_svg(dot_source, visualization_dir / target_svg)
            logging.info(f"Generated {target_svg}")
        except Exception as e:
            logging.error(f"Failed {filename}: {e}", exc_info=True)
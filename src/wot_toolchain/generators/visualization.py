"""Render the class diagram of each vocabulary module as SVG with Graphviz ``dot``."""

from __future__ import annotations

import logging
import shutil
import subprocess
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path

from linkml_runtime.linkml_model.meta import ClassDefinition, SlotDefinition
from linkml_runtime.utils.schemaview import SchemaView

from ..config import Module
from ..errors import ExternalToolError
from ..schema_utils import load_schema_view

logger = logging.getLogger(__name__)

ORANGE = "#C83500"
BLUE_BORDER = "#8CCBF2"
BLUE_BG = "#DDEEFF"
HEADER_BG = "#8CCBF2"
GRAY_BG = "#F2F2F2"
GRAY_BORDER = "#8C8C8C"
SVG_FONT = "Courier"

HIDE_DETAILS_FOR: set[str] = {"MultiLanguage"}
HIDE_CLASSES: set[str] = {"Any", "linkml:Any"}


def _normalize_range(rng: str | None, range_labels: Mapping[str, str]) -> str:
    if not rng:
        return ""
    return range_labels.get(rng, rng)


def _slot_assignment(slot_name: str, class_def: ClassDefinition, slot_def: SlotDefinition) -> str:
    usage = (class_def.slot_usage or {}).get(slot_name)
    if getattr(slot_def, "required", False) or (usage and getattr(usage, "required", False)):
        return "mandatory"
    return "optional"


def _slot_type_text(
    slot_name: str,
    slot_def: SlotDefinition,
    class_def: ClassDefinition,
    sv: SchemaView,
    range_labels: Mapping[str, str],
    effective_range: str | None = None,
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
            rng = _normalize_range(alt_rng_raw, range_labels)
            mv = bool(getattr(alt, "multivalued", False))
            p = f"(Array of) {rng}" if mv and rng else (rng if rng else "")
            if p and p not in seen:
                seen.add(p)
                pretty.append(p)
        return " or ".join(pretty)

    all_enums = sv.all_enums()
    if raw_rng in all_enums:
        enum_def = all_enums[raw_rng]
        is_uri_enum = (
            getattr(enum_def, "enum_uri", None) in ["linkml:uri", "anyURI"] or (raw_rng or "").lower() == "uri"
        )
        return "anyURI" if is_uri_enum else "string"

    rng = _normalize_range(raw_rng, range_labels)
    if not rng:
        return ""
    if getattr(slot_def, "multivalued", False):
        return f"(Array of) {rng}"
    return rng


def _format_type_html(type_text: str) -> str:
    parts = type_text.split(" or ")
    formatted_parts = []
    for p in parts:
        if p.startswith("(Array of) "):
            range_part = p.replace("(Array of) ", "")
            formatted_parts.append(
                f'<FONT COLOR="black">(Array of)</FONT> <FONT COLOR="{ORANGE}">{_escape_dot(range_part)}</FONT>'
            )
        else:
            formatted_parts.append(f'<FONT COLOR="{ORANGE}">{_escape_dot(p)}</FONT>')
    return ' <FONT COLOR="black">or</FONT> '.join(formatted_parts)


def require_dot() -> None:
    """Check that Graphviz ``dot`` can be run.

    Raises:
        ExternalToolError: ``dot`` is not on ``PATH``.
    """
    if shutil.which("dot") is None:
        raise ExternalToolError("Graphviz 'dot' is not installed or not on PATH; it is needed to render diagrams.")


def _dot_to_svg(dot_source: str, out_svg: Path) -> None:
    out_svg.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            ["dot", "-Tsvg", "-o", str(out_svg)],
            input=dot_source,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except FileNotFoundError as exc:
        raise ExternalToolError("Graphviz 'dot' is not installed or not on PATH.") from exc
    if result.returncode != 0:
        raise ExternalToolError(
            f"Graphviz 'dot' exited with code {result.returncode} while rendering {out_svg}:\n{result.stderr}"
        )


def _escape_dot(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _class_slot_names(class_def: ClassDefinition) -> list[str]:
    return [*class_def.slots, *class_def.attributes]


def _induced_slot(sv: SchemaView, class_name: str, slot_name: str) -> SlotDefinition | None:
    # A module may list a slot that only the schema importing it defines; SchemaView reports that as ValueError.
    try:
        return sv.induced_slot(slot_name, class_name)
    except ValueError:
        return None


def _unresolved_slots(sv: SchemaView) -> list[str]:
    """Return ``Class.slot`` for every slot a class lists that the schema and its imports do not define."""
    return [
        f"{class_name}.{slot_name}"
        for class_name, class_def in sv.all_classes().items()
        for slot_name in _class_slot_names(class_def)
        if _induced_slot(sv, class_name, slot_name) is None
    ]


def _build_children_index(all_classes: dict[str, object]) -> dict[str, set[str]]:
    children: dict[str, set[str]] = {}
    for cname, cdef in all_classes.items():
        parent = getattr(cdef, "is_a", None)
        if parent:
            children.setdefault(parent, set()).add(cname)
    return children


def _descendants_of(roots: Iterable[str], children_index: dict[str, set[str]]) -> set[str]:
    roots = set(roots)
    out: set[str] = set()
    stack = list(roots)
    while stack:
        r = stack.pop()
        for ch in children_index.get(r, set()):
            if ch not in out and ch not in roots:
                out.add(ch)
                stack.append(ch)
    return out


def _collapse_to_visible_ancestor(
    target: str, all_classes: dict[str, object], *, hidden: set[str], stop_at: set[str]
) -> str | None:
    cur = target
    while cur in hidden:
        parent = getattr(all_classes.get(cur), "is_a", None)
        if not parent:
            return None
        cur = parent
        if cur in stop_at and cur not in hidden:
            return cur
    return cur if cur not in hidden else None


def _detect_kept_external_bases(sv: SchemaView, all_classes: dict[str, object], *, local_classes: set[str]) -> set[str]:
    external_classes = set(all_classes.keys()) - set(local_classes)
    referenced_externals: set[str] = set()
    for cname, cdef in all_classes.items():
        if cname in local_classes:
            parent = getattr(cdef, "is_a", None)
            if parent and parent in external_classes:
                referenced_externals.add(parent)
            slot_names = list(getattr(cdef, "slots", None) or []) + list(
                (getattr(cdef, "attributes", None) or {}).keys()
            )
            for sname in slot_names:
                slot = _induced_slot(sv, cname, sname)
                if slot and slot.range and slot.range in external_classes:
                    referenced_externals.add(slot.range)
    return referenced_externals or external_classes


def _build_dot_from_schema_view(sv: SchemaView, *, local_classes: set[str], range_labels: Mapping[str, str]) -> str:
    all_classes = sv.all_classes()
    kept_external_bases = _detect_kept_external_bases(sv, all_classes, local_classes=local_classes)
    children_index = _build_children_index(all_classes)
    hidden = _descendants_of(kept_external_bases, children_index)

    def _is_visible(c: str) -> bool:
        return c not in HIDE_CLASSES and c not in hidden and (c in local_classes or c in kept_external_bases)

    lines: list[str] = [
        "digraph schema {",
        # Compact Vertical: Tighter nodesep/ranksep and zero margin
        '  graph [rankdir=BT, bgcolor="white", splines=polyline, overlap=false, nodesep=0.5, ranksep=0.6, '
        f'margin=0.1, concentrate=false, fontname="{SVG_FONT}"];',
        f'  node  [fontname="{SVG_FONT}", fontsize=10, shape=none, margin=0];',
        f'  edge  [fontname="{SVG_FONT}", fontsize=9, color="black"];',
        "",
    ]

    for class_name, class_def in all_classes.items():
        if not _is_visible(class_name):
            continue

        is_external = class_name not in local_classes

        attr_rows = ""
        if (not is_external) and (class_name not in HIDE_DETAILS_FOR):
            attr_names = list((class_def.attributes or {}).keys()) or list(class_def.slots or [])
            for sname in attr_names:
                slot = _induced_slot(sv, class_name, sname)
                if (
                    slot is None
                    or (getattr(slot, "range", None) in all_classes)
                    or (getattr(slot, "range", None) in HIDE_CLASSES)
                ):
                    continue

                type_text = _slot_type_text(sname, slot, class_def, sv, range_labels, getattr(slot, "range", None))
                type_display = _format_type_html(type_text)
                assignment = _slot_assignment(sname, class_def, slot)
                mandatory_marker = " <I>(mandatory)</I>" if assignment == "mandatory" else ""
                display_name = "name" if sname == "@name" else sname

                attr_rows += (
                    f'<TR><TD ALIGN="LEFT" BGCOLOR="{BLUE_BG}" COLOR="{BLUE_BORDER}" WIDTH="200">'
                    f'<FONT COLOR="{ORANGE}">{_escape_dot(display_name)}</FONT> : {type_display}{mandatory_marker}'
                    f"</TD></TR>\n"
                )

        if is_external:
            label = (
                f'<<TABLE BORDER="0.5" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3" COLOR="{GRAY_BORDER}">'
                f'<TR><TD BGCOLOR="{GRAY_BG}" WIDTH="200"><B><FONT COLOR="black">'
                f"<I>{_escape_dot(class_name)}</I></FONT></B></TD></TR></TABLE>>"
            )
        else:
            label = (
                f'<<TABLE BORDER="0.5" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3" COLOR="{BLUE_BORDER}">'
                f'<TR><TD BGCOLOR="{HEADER_BG}" WIDTH="200"><B><FONT COLOR="{ORANGE}">'
                f"{_escape_dot(class_name)}</FONT></B></TD></TR>"
                f"{attr_rows}</TABLE>>"
            )
        lines.append(f'  "{class_name}" [label={label}];')

    for child, cdef in all_classes.items():
        if not _is_visible(child):
            continue
        parent = getattr(cdef, "is_a", None)
        if parent:
            parent = _collapse_to_visible_ancestor(parent, all_classes, hidden=hidden, stop_at=kept_external_bases)
            if parent and _is_visible(parent):
                lines.append(f'  "{child}" -> "{parent}" [arrowhead=empty, color="{GRAY_BORDER}"];')

    edge_groups = defaultdict(list)
    for src, cdef in all_classes.items():
        if not _is_visible(src) or src not in local_classes:
            continue
        slots = list(getattr(cdef, "slots", None) or []) + list((getattr(cdef, "attributes", None) or {}).keys())
        for sname in slots:
            slot = _induced_slot(sv, src, sname)
            if not slot or slot.range is None or slot.range not in all_classes:
                continue
            dst = _collapse_to_visible_ancestor(slot.range, all_classes, hidden=hidden, stop_at=kept_external_bases)
            if dst and _is_visible(dst):
                mult = "0..*" if getattr(slot, "multivalued", False) else "0..1"
                edge_groups[(src, dst, mult)].append(sname)

    for (src, dst, mult), labels in edge_groups.items():
        labels.sort(key=len)
        label_rows = "".join(
            f'<TR><TD ALIGN="LEFT"><FONT COLOR="{ORANGE}">{_escape_dot(name)}</FONT></TD></TR>' for name in labels
        )
        merged_label = f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="1">{label_rows}</TABLE>>'
        # Kept the improved cardinality distance but reduced minlen for compactness
        lines.append(
            f'  "{src}" -> "{dst}" [label={merged_label}, headlabel="{mult}", '
            'labeldistance=3.0, labelangle=20, minlen=1, arrowhead=open, color="black"];'
        )

    lines.append("}")
    return "\n".join(lines)


def generate_visualizations(modules: Iterable[Module], output_dir: Path, range_labels: Mapping[str, str]) -> None:
    """Render the class diagram of every module that declares one.

    Args:
        modules: Vocabulary modules; each one whose ``diagram`` is set gets an SVG of that name.
        output_dir: Directory that receives the diagrams.
        range_labels: Text shown for a slot range, keyed by range name; ranges without an entry are shown under
            their own name.

    Raises:
        ExternalToolError: Graphviz ``dot`` is missing or fails to render a diagram.
        SchemaError: A module schema cannot be loaded.
    """
    diagrams = [(module.schema, module.diagram) for module in modules if module.diagram is not None]
    if not diagrams:
        return
    require_dot()
    output_dir.mkdir(parents=True, exist_ok=True)

    for schema_path, diagram in diagrams:
        sv_merged = load_schema_view(schema_path, merge_imports=True)
        sv_unmerged = load_schema_view(schema_path, merge_imports=False)
        local_classes = set((sv_unmerged.schema.classes or {}).keys())
        unresolved = _unresolved_slots(sv_merged)
        if unresolved:
            logger.warning(
                "%s: slots not defined in this schema or its imports are left out of %s: %s",
                schema_path,
                diagram,
                ", ".join(unresolved),
            )
        dot_source = _build_dot_from_schema_view(sv_merged, local_classes=local_classes, range_labels=range_labels)
        _dot_to_svg(dot_source, output_dir / diagram)
        logger.info("Generated %s from %s", diagram, schema_path)

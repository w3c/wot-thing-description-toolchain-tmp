"""Class diagrams of the vocabularies, drawn with Graphviz."""

import logging
import shutil
import subprocess
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path

from linkml_runtime.linkml_model import ClassDefinition, SlotDefinition
from linkml_runtime.utils.schemaview import SchemaView

from ..artifacts.jsonschema.traversal import is_linkml_any
from ..errors import GenerationError

ORANGE = "#C83500"
BLUE_BORDER = "#8CCBF2"
BLUE_BG = "#DDEEFF"
HEADER_BG = "#8CCBF2"
GRAY_BG = "#F2F2F2"
GRAY_BORDER = "#8C8C8C"
SVG_FONT = "Courier"

HIDE_DETAILS_FOR: set[str] = {"MultiLanguage"}

URI_ENUM = "linkml:uri"


def _linkml_any_classes(sv: SchemaView) -> set[str]:
    """Return the names of the classes that stand for ``linkml:Any``."""
    return {name for name, cls_def in sv.all_classes().items() if is_linkml_any(sv, cls_def)}


def _own_slot_names(class_def: ClassDefinition) -> list[str]:
    """Return the names of the slots and attributes that a class declares itself."""
    return [*class_def.slots, *class_def.attributes]


def _display_name(slot: SlotDefinition) -> str:
    """Return the name a slot has in a document: its alias, or else its name."""
    return slot.alias or slot.name


def _range_label(rng: str | None, sv: SchemaView, range_labels: Mapping[str, str]) -> str:
    """Return the label of a range; an enum is labelled as the type of its values."""
    if not rng:
        return ""
    enum_def = sv.all_enums().get(rng)
    if enum_def is not None:
        rng = "uri" if enum_def.enum_uri == URI_ENUM else "string"
    return range_labels.get(rng, rng)


def _slot_type_text(slot: SlotDefinition, sv: SchemaView, range_labels: Mapping[str, str]) -> str:
    """Return the type of an induced slot, its ``exactly_one_of`` or ``any_of`` alternatives joined with "or"."""
    alternatives = slot.exactly_one_of or slot.any_of or [slot]
    texts: dict[str, None] = {}
    for alternative in alternatives:
        label = _range_label(alternative.range or slot.range, sv, range_labels)
        if label:
            texts[f"(Array of) {label}" if alternative.multivalued else label] = None
    return " or ".join(texts)


def _format_type_html(type_text: str) -> str:
    parts = type_text.split(" or ")
    formatted_parts = []
    for part in parts:
        if part.startswith("(Array of) "):
            range_part = part.replace("(Array of) ", "")
            formatted_parts.append(
                f'<FONT COLOR="black">(Array of)</FONT> <FONT COLOR="{ORANGE}">{_escape_dot(range_part)}</FONT>'
            )
        else:
            formatted_parts.append(f'<FONT COLOR="{ORANGE}">{_escape_dot(part)}</FONT>')
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


def _build_children_index(all_classes: Mapping[str, ClassDefinition]) -> dict[str, set[str]]:
    children: dict[str, set[str]] = defaultdict(set)
    for class_name, class_def in all_classes.items():
        if class_def.is_a:
            children[class_def.is_a].add(class_name)
    return children


def _descendants_of(roots: Iterable[str], children_index: Mapping[str, set[str]]) -> set[str]:
    roots = set(roots)
    descendants: set[str] = set()
    stack = list(roots)
    while stack:
        for child in children_index.get(stack.pop(), set()):
            if child not in descendants and child not in roots:
                descendants.add(child)
                stack.append(child)
    return descendants


def _collapse_to_visible_ancestor(
    target: str | None, all_classes: Mapping[str, ClassDefinition], *, hidden: set[str], stop_at: set[str]
) -> str | None:
    current = target
    while current in hidden:
        parent = all_classes[current].is_a
        if not parent:
            return None
        current = parent
        if current in stop_at and current not in hidden:
            return current
    return current if current not in hidden else None


def _referenced_external_classes(sv: SchemaView, local_classes: set[str]) -> set[str]:
    """Return the classes of other schemas that a local class extends or has as the range of a slot."""
    all_classes = sv.all_classes()
    referenced: set[str] = set()
    for class_name in local_classes:
        class_def = all_classes[class_name]
        ranges = {sv.induced_slot(slot_name, class_name).range for slot_name in _own_slot_names(class_def)}
        referenced |= ({class_def.is_a} | ranges) & all_classes.keys()
    return referenced - local_classes


def _attribute_rows(
    class_name: str, sv: SchemaView, range_labels: Mapping[str, str], association_classes: set[str]
) -> str:
    """Return a table row for each own slot of a class that is not drawn as an association."""
    rows = ""
    for slot_name in _own_slot_names(sv.get_class(class_name)):
        slot = sv.induced_slot(slot_name, class_name)
        if slot.range in association_classes:
            continue
        type_display = _format_type_html(_slot_type_text(slot, sv, range_labels))
        mandatory_marker = " <I>(mandatory)</I>" if slot.required else ""
        rows += (
            f'<TR><TD ALIGN="LEFT" BGCOLOR="{BLUE_BG}" COLOR="{BLUE_BORDER}" WIDTH="200">'
            f'<FONT COLOR="{ORANGE}">{_escape_dot(_display_name(slot))}</FONT> : {type_display}{mandatory_marker}'
            f"</TD></TR>\n"
        )
    return rows


def _build_dot_from_schema_view(sv: SchemaView, *, local_classes: set[str], range_labels: Mapping[str, str]) -> str:
    """Return the DOT source of the diagram of ``local_classes``; ``sv`` resolves every slot they use."""
    all_classes = sv.all_classes()
    kept_external_bases = _referenced_external_classes(sv, local_classes)
    children_index = _build_children_index(all_classes)
    hidden = _descendants_of(kept_external_bases, children_index)
    any_classes = _linkml_any_classes(sv)
    association_classes = all_classes.keys() - any_classes

    def _is_visible(c: str) -> bool:
        return c not in any_classes and c not in hidden and (c in local_classes or c in kept_external_bases)

    lines: list[str] = [
        "digraph schema {",
        # Left to right keeps every diagram about equally wide, so the spec scales them alike.
        f'  graph [rankdir=LR, bgcolor="white", splines=polyline, overlap=false, nodesep=0.5, ranksep=0.6, margin=0.1, concentrate=false, fontname="{SVG_FONT}"];',
        f'  node  [fontname="{SVG_FONT}", fontsize=10, shape=none, margin=0, width=0, height=0];',
        f'  edge  [fontname="{SVG_FONT}", fontsize=9, color="black"];',
        "",
    ]

    for class_name in all_classes:
        if not _is_visible(class_name):
            continue
        if class_name not in local_classes:
            label = (
                f'<<TABLE BORDER="0.5" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3" COLOR="{GRAY_BORDER}">'
                f'<TR><TD BGCOLOR="{GRAY_BG}" WIDTH="200"><B><FONT COLOR="black"><I>{_escape_dot(class_name)}</I></FONT></B></TD></TR></TABLE>>'
            )
        else:
            attr_rows = (
                ""
                if class_name in HIDE_DETAILS_FOR
                else _attribute_rows(class_name, sv, range_labels, association_classes)
            )
            label = (
                f'<<TABLE BORDER="0.5" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3" COLOR="{BLUE_BORDER}">'
                f'<TR><TD BGCOLOR="{HEADER_BG}" WIDTH="200"><B><FONT COLOR="{ORANGE}">{_escape_dot(class_name)}</FONT></B></TD></TR>'
                f"{attr_rows}</TABLE>>"
            )
        lines.append(f'  "{class_name}" [label={label}];')

    for child, class_def in all_classes.items():
        if not _is_visible(child) or not class_def.is_a:
            continue
        parent = _collapse_to_visible_ancestor(class_def.is_a, all_classes, hidden=hidden, stop_at=kept_external_bases)
        if parent and _is_visible(parent):
            lines.append(f'  "{child}" -> "{parent}" [arrowhead=empty, color="{GRAY_BORDER}"];')

    edge_groups: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for src, class_def in all_classes.items():
        if not _is_visible(src) or src not in local_classes:
            continue
        for slot_name in _own_slot_names(class_def):
            slot = sv.induced_slot(slot_name, src)
            if slot.range not in association_classes:
                continue
            dst = _collapse_to_visible_ancestor(slot.range, all_classes, hidden=hidden, stop_at=kept_external_bases)
            if dst and _is_visible(dst):
                mult = "0..*" if slot.multivalued else "0..1"
                edge_groups[(src, dst, mult)].append(_display_name(slot))

    for (src, dst, mult), labels in edge_groups.items():
        labels.sort(key=len)
        label_rows = "".join(
            f'<TR><TD ALIGN="LEFT"><FONT COLOR="{ORANGE}">{_escape_dot(label)}</FONT></TD></TR>' for label in labels
        )
        merged_label = f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="1">{label_rows}</TABLE>>'
        # Kept the improved cardinality distance but reduced minlen for compactness
        lines.append(
            f'  "{src}" -> "{dst}" [label={merged_label}, headlabel="{mult}", labeldistance=3.0, labelangle=20, minlen=1, arrowhead=open, color="black"];'
        )

    lines.append("}")
    return "\n".join(lines)


def generate_visualizations(
    root_schema: Path, diagrams: Iterable[tuple[Path, str]], visualization_dir: Path, range_labels: Mapping[str, str]
) -> None:
    """Draw the classes of each schema; the root schema and its imports define the slots that the classes use."""
    if not _require_dot():
        raise GenerationError("Graphviz 'dot' executable not found; the diagrams cannot be drawn.")

    visualization_dir.mkdir(parents=True, exist_ok=True)
    schema_view = SchemaView(str(root_schema), merge_imports=True)

    for path, target_svg in diagrams:
        local_classes = set(SchemaView(str(path), merge_imports=False).schema.classes)
        dot_source = _build_dot_from_schema_view(schema_view, local_classes=local_classes, range_labels=range_labels)
        _dot_to_svg(dot_source, visualization_dir / target_svg)
        logging.info(f"Generated {target_svg}")

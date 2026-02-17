import logging
import shutil
import subprocess
import textwrap

from pathlib import Path

from linkml_runtime.utils.schemaview import SchemaView


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


def _range_label(range_str: str | None) -> str:
    """Return a short display label for a slot range."""
    if range_str is None:
        return "string"
    return range_str.split(":")[-1].lower()


def _build_dot_from_schema_view(sv: SchemaView) -> str:
    """
    Build a Graphviz DOT string from a SchemaView object.

    Uses SchemaView directly instead of DotGenerator / SchemaLoader to avoid:
      - "Conflicting URIs" errors when schemas redefine linkml built-in types
        under a different namespace URI.
      - "unknown slot" errors when sub-schemas reference slots that are only
        defined in an imported parent schema.
    """
    all_classes = sv.all_classes()

    lines = [
        'digraph schema {',
        '  graph [rankdir=BT, fontname="Helvetica", fontsize=11, bgcolor="white"];',
        '  node  [fontname="Helvetica", fontsize=10, shape=none, margin=0];',
        '  edge  [fontname="Helvetica", fontsize=9, color="#555555"];',
        '',
    ]
    # nodes
    for class_name, class_def in all_classes.items():
        try:
            induced = sv.get_class(class_name)
            slot_names = list(induced.slots or []) + list(
                (induced.attributes or {}).keys()
            )
        except Exception:
            slot_names = []

        attr_rows = ""
        for sname in slot_names:
            try:
                slot = sv.get_slot(sname) or sv.get_class(class_name).attributes.get(sname)
                if slot is None:
                    continue
                range_str = _range_label(slot.range)
                required_marker = " <I>(mandatory)</I>" if slot.required else ""
                multivalued_marker = "(Array of) " if slot.multivalued else ""
                attr_rows += (
                    f'<TR><TD ALIGN="LEFT">'
                    f'{_escape_dot(sname)}&nbsp;:&nbsp;'
                    f'{multivalued_marker}{_escape_dot(range_str)}'
                    f'{required_marker}'
                    f'</TD></TR>\n'
                )
            except Exception:
                continue

        is_abstract = getattr(class_def, 'abstract', False)
        header_bg = 'white' if is_abstract else '#add8e6'
        border = '1'

        label = textwrap.dedent(f"""\
            <<TABLE BORDER="{border}" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2" BGCOLOR="white">
              <TR><TD BGCOLOR="{header_bg}"><B><FONT COLOR="black">{_escape_dot(class_name)}</FONT></B></TD></TR>
              {attr_rows}</TABLE>>""")

        lines.append(f'  "{class_name}" [label={label}];')

    lines.append('')

    # Edges
    # Inheritance (is_a)
    for class_name, class_def in all_classes.items():
        if class_def.is_a:
            lines.append(
                f'  "{class_name}" -> "{class_def.is_a}" '
                f'[arrowhead=empty, style=solid, color="#555555"];'
            )

    # Association edges for slots whose range is another class
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
                range_name = slot.range
                if range_name and range_name in all_classes:
                    mult = "0..*" if slot.multivalued else "0..1"
                    edge_key = (class_name, range_name, sname)
                    if edge_key not in emitted_edges:
                        emitted_edges.add(edge_key)
                        lines.append(
                            f'  "{class_name}" -> "{range_name}" '
                            f'[label="{_escape_dot(sname)} {mult}", '
                            f'arrowhead=open, style=solid, color="#cc6600"];'
                        )
            except Exception:
                continue

    lines.append('}')
    return '\n'.join(lines)


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
            logging.warning(
                "Schema not found for diagram (%s). Skipping %s.", schema_path, target_svg
            )
            continue

        try:
            logging.info(
                "Generating UML diagram for %s → %s (%s)", filename, out_svg.name, label
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
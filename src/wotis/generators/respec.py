from __future__ import annotations

from html import escape
import logging
import re
import yaml

from jinja2 import exceptions
from linkml_runtime.utils.schemaview import SchemaView
from pathlib import Path
from typing import Callable, Dict, List, Optional

from ..specgen.config import Config
from ..specgen.bikeshed_processor import process_fragments
from ..specgen.respec import build_jinja_env, assemble
from ..specgen.tables import collect_slot_rows
from ..specgen.assertions import html_assertions_to_csv

cfg = Config.from_resources_dir(Path("resources"), placeholder="%s")


def _annotation_value(annotations: dict, key: str):
    ann = annotations.get(key)
    if ann is None:
        return None
    return getattr(ann, "value", ann)


def _record_value(record: dict, key: str):
    value = record.get(key)
    return getattr(value, "value", value)


def _assertion_annotation_records(annotations: dict) -> list[dict]:
    records: list[dict] = []
    grouped = _annotation_value(annotations, "assertions")
    grouped = getattr(grouped, "value", grouped)
    if isinstance(grouped, dict) and "value" in grouped:
        grouped = grouped["value"]
    if isinstance(grouped, dict):
        records.append(grouped)
    elif isinstance(grouped, list):
        records.extend(record for record in grouped if isinstance(record, dict))

    direct = {}
    for key in ("assertion_id", "assertion_text", "assertion_type"):
        value = _annotation_value(annotations, key)
        if value is not None:
            direct[key] = value
    if direct:
        records.append(direct)

    return records


def _inline_html(html: str) -> str:
    """Use Markdown rendering for assertion text, but keep the assertion span inline."""
    match = re.fullmatch(r"\s*<p>(?P<body>.*)</p>\s*", html or "", flags=re.DOTALL)
    if match:
        return match.group("body")
    return html or ""


def _as_block_list(value) -> list[dict]:
    value = getattr(value, "value", value)
    if isinstance(value, dict) and "value" in value:
        value = value["value"]
    if isinstance(value, list):
        return [block for block in value if isinstance(block, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def _render_inline_markdown(
    text: str,
    process_description: Callable[[str], str],
) -> str:
    return _inline_html(process_description(str(text or "")))


def _render_note_block(
    text: str,
    process_description: Callable[[str], str],
    title: Optional[str] = None,
) -> str:
    body = process_description(str(text or ""))
    if not body:
        return ""
    if title:
        return (
            f'<p class="note" title="{escape(str(title), quote=True)}">'
            f"{_inline_html(body)}</p>"
        )
    return f'<div class="note">\n{body}\n</div>'


def _extract_enum_cell(
    pv,
    field: str,
    process_description: Callable[[str], str],
) -> str:
    if field == "name":
        return f"<td>{escape(str(pv.text))}</td>"
    if field == "description":
        desc = getattr(pv, "description", "") or ""
        return f"<td>{_inline_html(process_description(str(desc)))}</td>"
    if field.startswith("comment:"):
        prefix = field[len("comment:") :]
        comments = getattr(pv, "comments", None) or []
        for comment in comments:
            c = str(comment)
            if c.startswith(prefix + " - "):
                content = c[len(prefix) + 3 :]
                return f"<td>{_inline_html(process_description(content))}</td>"
            if c.startswith(prefix):
                content = c[len(prefix) :].lstrip(" -")
                return f"<td>{_inline_html(process_description(content))}</td>"
        return "<td>No correlation.</td>"
    return "<td></td>"


def _render_enum_table(
    block: dict,
    process_description: Callable[[str], str],
    schema_view: Optional["SchemaView"] = None,
) -> str:
    enum_name = _record_value(block, "enum")
    if not enum_name or not schema_view:
        logging.warning("enum_table block requires 'enum' and a SchemaView")
        return ""

    enum_def = schema_view.get_enum(str(enum_name))
    if not enum_def:
        logging.warning("Enum %r not found in schema", enum_name)
        return ""

    columns = _record_value(block, "columns") or []
    if not isinstance(columns, list) or not columns:
        logging.warning("enum_table block requires a non-empty 'columns' list")
        return ""

    caption = _record_value(block, "caption") or ""
    table_id = _record_value(block, "table_id") or ""

    headers = []
    fields = []
    for col in columns:
        if isinstance(col, dict):
            headers.append(escape(str(_record_value(col, "header") or "")))
            fields.append(str(_record_value(col, "field") or "name"))
        else:
            headers.append(escape(str(col)))
            fields.append("name")

    lines: list[str] = []
    if table_id:
        lines.append(f'<div id="{escape(str(table_id), quote=True)}">')

    lines.append('<table class="def numbered">')
    if caption:
        lines.append(f"<caption>{escape(str(caption))}</caption>")
    lines.append("<thead>")
    lines.append("<tr>")
    for h in headers:
        lines.append(f"<th>{h}</th>")
    lines.append("</tr>")
    lines.append("</thead>")
    lines.append("<tbody>")

    require_comments = _record_value(block, "require_comments")
    pvs = enum_def.permissible_values or {}
    for pv_key, pv in pvs.items():
        if require_comments and not (getattr(pv, "comments", None) or []):
            continue
        lines.append("<tr>")
        for field in fields:
            lines.append(_extract_enum_cell(pv, field, process_description))
        lines.append("</tr>")

    lines.append("</tbody>")
    lines.append("</table>")
    if table_id:
        lines.append("</div>")

    return "\n".join(lines)


def _render_assertion_span(
    record: dict,
    process_description: Callable[[str], str],
) -> str:
    assertion_id = _record_value(record, "id") or _record_value(record, "assertion_id")
    assertion_text = _record_value(record, "text") or _record_value(
        record,
        "assertion_text",
    )
    assertion_type = _record_value(record, "assertion_type") or "rfc2119-assertion"

    if not assertion_id or not assertion_text:
        logging.warning(
            "Ignoring incomplete assertion block: id=%r text=%r",
            assertion_id,
            assertion_text,
        )
        return ""

    allowed_types = {
        "rfc2119-assertion",
        "rfc2119-default-assertion",
        "rfc2119-table-assertion",
    }
    if str(assertion_type) not in allowed_types:
        logging.warning(
            "Unsupported assertion type %r; using rfc2119-assertion",
            assertion_type,
        )
        assertion_type = "rfc2119-assertion"

    text_html = _render_inline_markdown(str(assertion_text), process_description)
    return (
        f'<span class="{escape(str(assertion_type), quote=True)}" '
        f'id="{escape(str(assertion_id), quote=True)}">{text_html}</span>'
    )


def _render_list_block(
    block: dict,
    process_description: Callable[[str], str],
) -> str:
    items = _record_value(block, "items") or []
    if not isinstance(items, list):
        logging.warning("Ignoring spec_content list block with non-list items: %r", items)
        return ""

    rendered_items: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            rendered = _render_inline_markdown(str(item), process_description)
        elif _record_value(item, "id") or _record_value(item, "assertion_id"):
            rendered = _render_assertion_span(item, process_description)
        else:
            rendered = _render_inline_markdown(
                str(_record_value(item, "text") or ""),
                process_description,
            )
        if rendered:
            rendered_items.append(f"<li>{rendered}</li>")

    if not rendered_items:
        return ""
    return "<ul>\n" + "\n".join(rendered_items) + "\n</ul>"


def _render_paragraph_block(
    block: dict,
    process_description: Callable[[str], str],
) -> str:
    segments = _record_value(block, "segments") or []
    if not isinstance(segments, list):
        logging.warning(
            "Ignoring spec_content paragraph block with non-list segments: %r",
            segments,
        )
        return ""

    rendered_segments: list[str] = []
    for segment in segments:
        if not isinstance(segment, dict):
            rendered_segments.append(
                _render_inline_markdown(str(segment), process_description)
            )
            continue
        if _record_value(segment, "id") or _record_value(segment, "assertion_id"):
            rendered_segments.append(_render_assertion_span(segment, process_description))
        else:
            rendered_segments.append(
                _render_inline_markdown(
                    str(_record_value(segment, "text") or ""),
                    process_description,
                )
            )

    content = " ".join(part.strip() for part in rendered_segments if part.strip())
    if not content:
        return ""
    return f"<p>{content}</p>"


def render_spec_content_annotation(
    annotations: dict,
    process_description: Callable[[str], str],
    annotation_key: str = "spec_content",
    schema_view: Optional["SchemaView"] = None,
) -> str:
    blocks = _as_block_list(_annotation_value(annotations, annotation_key))
    if not blocks:
        return ""

    return _render_content_blocks(blocks, process_description, schema_view)


def _render_content_blocks(
    blocks: list[dict],
    process_description: Callable[[str], str],
    schema_view: Optional["SchemaView"] = None,
) -> str:
    rendered_blocks: list[str] = []
    for block in blocks:
        block_type = str(_record_value(block, "type") or "markdown")
        text = _record_value(block, "text") or ""

        if block_type == "markdown":
            rendered = process_description(str(text))
        elif block_type == "note":
            title = _record_value(block, "title")
            rendered = _render_note_block(
                str(text), process_description, title=str(title) if title else None
            )
        elif block_type == "assertion":
            span = _render_assertion_span(block, process_description)
            rendered = f"<p>{span}</p>" if span else ""
        elif block_type in {"list", "assertion_list"}:
            rendered = _render_list_block(block, process_description)
        elif block_type == "paragraph":
            rendered = _render_paragraph_block(block, process_description)
        elif block_type == "enum_table":
            rendered = _render_enum_table(block, process_description, schema_view)
        else:
            logging.warning("Ignoring unsupported spec_content block type: %s", block_type)
            rendered = ""

        if rendered:
            rendered_blocks.append(rendered)

    return "\n".join(rendered_blocks)


def render_subsections(
    annotations: dict,
    process_description: Callable[[str], str],
    schema_view: Optional["SchemaView"] = None,
) -> str:
    subsections = _as_block_list(_annotation_value(annotations, "spec_subsections"))
    if not subsections:
        return ""

    rendered: list[str] = []
    for sub in subsections:
        sub_id = _record_value(sub, "id") or ""
        sub_title = _record_value(sub, "title") or ""
        sub_class = _record_value(sub, "class") or ""
        content_blocks = _as_block_list(_record_value(sub, "content"))

        attrs = ""
        if sub_id:
            attrs += f' id="{escape(str(sub_id), quote=True)}"'
        if sub_class:
            attrs += f' class="{escape(str(sub_class), quote=True)}"'

        lines: list[str] = [f"<section{attrs}>"]
        if sub_title:
            lines.append(f"<h4>{escape(str(sub_title))}</h4>")

        if content_blocks:
            content_html = _render_content_blocks(
                content_blocks, process_description, schema_view
            )
            if content_html:
                lines.append(content_html)

        lines.append("</section>")
        rendered.append("\n".join(lines))

    return "\n".join(rendered)


def render_explicit_assertion_annotation(
    annotations: dict,
    process_description: Callable[[str], str],
) -> str:
    """
    Render LinkML assertion annotations.

    annotation keys:
      assertion_id: stable assertion ID
      assertion_text: assertion prose
      assertion_type: CSS class, defaults to rfc2119-assertion

    Multiple prose assertions can be supplied as:
      assertions:
        value:
          - assertion_id: ...
            assertion_text: ...
            assertion_type: rfc2119-assertion
    """
    records = _assertion_annotation_records(annotations)
    if not records:
        return ""

    allowed_types = {
        "rfc2119-assertion",
        "rfc2119-default-assertion",
        "rfc2119-table-assertion",
    }
    rendered: list[str] = []
    for record in records:
        assertion_id = _record_value(record, "assertion_id")
        assertion_text = _record_value(record, "assertion_text")
        assertion_type = _record_value(record, "assertion_type") or "rfc2119-assertion"

        if not assertion_id or not assertion_text:
            logging.warning(
                "Ignoring incomplete assertion annotation: id=%r text=%r",
                assertion_id,
                assertion_text,
            )
            continue

        if str(assertion_type) not in allowed_types:
            logging.warning(
                "Unsupported assertion_type %r; using rfc2119-assertion",
                assertion_type,
            )
            assertion_type = "rfc2119-assertion"

        text_html = _inline_html(process_description(str(assertion_text)))
        rendered.append(
            f'<p><span class="{escape(str(assertion_type), quote=True)}" '
            f'id="{escape(str(assertion_id), quote=True)}">{text_html}</span></p>'
        )

    return "\n".join(rendered)


def generate_respec_spec(
    input_path: Path,
    respec_template_path: Path,
    final_spec_path: Path,
    core_schema_placeholder: str,
    assertions_csv_path: Optional[Path] = None,
    extra_asserts_path: Optional[Path] = None,
) -> None:
    """
    Generate the ReSpec-compatible HTML document from the LinkML schema.

    This function:
      • Loads the LinkML model
      • Converts Markdown and annotations to HTML
      • Applies glossary linking (bibliography [[...]] refs pass through for ReSpec)
      • Renders each class section with Jinja templates
      • Injects the resulting HTML into the ReSpec index template

    Args:
        input_path: Path to the root LinkML YAML schema file.
        respec_template_path: Path to the ReSpec HTML template (index.template.html).
        final_spec_path: Path to write the final, assembled HTML output.
        core_schema_placeholder: The placeholder string inside the ReSpec
            template to replace.
        assertions_csv_path: If provided, write an assertions.csv compatible
            with the WoT TD Test suite (extractFile.js output).
        extra_asserts_path: If provided, merge additional assertions from
            this HTML file into the assertion inventory.
    """
    try:
        sv = SchemaView(input_path, merge_imports=True)
    except yaml.YAMLError as e:
        logging.error("Failed to load LinkML schema: %s", e)
        return

    try:
        env = build_jinja_env(cfg.jinja_templates)
        section_tpl = env.get_template("class_section.jinja2")
    except (exceptions.TemplateNotFound, FileNotFoundError) as e:
        logging.error("Template error: %s", e, exc_info=True)
        assemble(
            respec_template_path,
            f"",
            "",
            "",
            "",
            out_path=final_spec_path,
            placeholder=core_schema_placeholder,
        )
        return

    def process_description(raw_text: str) -> str:
        """Convert inline markdown backticks to <code> tags."""
        text = str(raw_text or "")
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        return text

    file_to_classes: Dict[str, List[str]] = {}
    for section_path in cfg.section_schemas.values():
        try:
            if not section_path.exists():
                logging.error(
                    "Missing schema file: %s. Cannot render this section.",
                    section_path.name,
                )
                file_to_classes[section_path.name] = []
                continue
            section_sv = SchemaView(section_path, merge_imports=False)
            file_to_classes[section_path.name] = list(section_sv.all_classes().keys())
        except (yaml.YAMLError, IOError) as e:
            logging.error(
                "Failed to load section schema %s due to: %s. Skipping section.",
                section_path.name,
                e,
            )
            file_to_classes[section_path.name] = []

    # Identify all non-core classes (defined outside the primary TD schema)
    non_core_classes: set[str] = set()
    try:
        core_section_id = next(iter(cfg.section_schemas.keys()))
    except StopIteration:
        core_section_id = None

    for section_id, section_path in cfg.section_schemas.items():
        if section_id != core_section_id:
            non_core_classes.update(file_to_classes.get(section_path.name, []))
    sections_content: List[str] = []
    for section_id, section_path in cfg.section_schemas.items():
        section_classes_to_render = file_to_classes.get(section_path.name, [])
        schema_prefix = cfg.schema_prefixes.get(section_path.stem, section_path.stem)
        sections_html: List[str] = []
        if section_id == core_section_id and core_section_id is not None:
            section_classes_to_render = [
                cls for cls in section_classes_to_render if cls not in non_core_classes
            ]
        # Enforce 'Thing' first
        if 'Thing' in section_classes_to_render:
            section_classes_to_render.remove('Thing')
            section_classes_to_render.insert(0, 'Thing')
        for cls in section_classes_to_render:
            cdef = sv.get_class(cls)
            if not cdef:
                continue
            ann = getattr(cdef, "annotations", None) or {}
            spec_exclude_ann = ann.get("spec_exclude")
            if spec_exclude_ann:
                ann_value = getattr(spec_exclude_ann, "value", None)
                if ann_value is None:
                    ann_value = spec_exclude_ann
                if str(ann_value).lower() == "true":
                    logging.debug(
                        "Skipping rendering of class %r due to "
                        "spec_exclude=true annotation.",
                        cls,
                    )
                    continue

            rows = collect_slot_rows(sv, cls, process_description, schema_prefix)
            intro_html = ""
            desc_html = ""
            if "spec_intro_content" in ann:
                intro_html = render_spec_content_annotation(
                    ann,
                    process_description,
                    annotation_key="spec_intro_content",
                )
            else:
                raw_desc = getattr(cdef, "description", "") or ""
                if "spec_description" in ann:
                    spec_def = (
                        getattr(ann["spec_description"], "value", None)
                        or ann["spec_description"]
                    )
                    raw_desc = str(spec_def) or raw_desc
                desc_html = process_description(raw_desc)
            spec_content_html = ""
            if "spec_content" in ann:
                spec_content_html = render_spec_content_annotation(
                    ann,
                    process_description,
                    schema_view=sv,
                )
            assertion_html = render_explicit_assertion_annotation(
                ann,
                process_description,
            )
            if assertion_html:
                spec_content_html = "\n".join(
                    part for part in [spec_content_html, assertion_html] if part
                )

            subsections_html = ""
            if "spec_subsections" in ann:
                subsections_html = render_subsections(
                    ann,
                    process_description,
                    schema_view=sv,
                )

            sections_html.append(
                section_tpl.render(
                    class_name=cls,
                    class_description=desc_html,
                    slots=rows,
                    spec_intro_html=intro_html,
                    spec_content_html=spec_content_html,
                    subsections_html=subsections_html,
                )
            )

        section_html_fragment = "\n\n".join(sections_html)
        sections_content.append(section_html_fragment)

    section_ids = list(cfg.section_schemas.keys())
    sections_content = process_fragments(section_ids, sections_content, cfg.glossary_path)

    # Escape literal percent signs so assemble()'s placeholder replacement is safe.
    sections_content = [s.replace('%', '%%') for s in sections_content]

    assemble(
        respec_template_path,
        *sections_content,
        out_path=final_spec_path,
        placeholder=core_schema_placeholder,
    )

    if assertions_csv_path is not None:
        try:
            html_assertions_to_csv(final_spec_path, assertions_csv_path, extra_asserts_path)
        except Exception as exc:
            logging.error("Assertion CSV generation failed: %s", exc, exc_info=True)

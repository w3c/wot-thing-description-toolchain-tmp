"""Render the HTML specification of a project from its LinkML schemas and their ``spec_*`` annotations."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Mapping, Sequence
from html import escape
from pathlib import Path
from typing import Any

from jinja2 import Template
from linkml_runtime.linkml_model.meta import PermissibleValue
from linkml_runtime.utils.schemaview import SchemaView

from ..config import SpecConfig, SpecSection
from ..errors import GenerationError
from ..model.resolved import ResolvedProject
from ..schema_utils import annotation_dict_value as _annotation_value
from ..schema_utils import load_schema_view
from ..specgen.assertions import html_assertions_to_csv
from ..specgen.bikeshed_processor import process_fragments
from ..specgen.respec import assemble, build_jinja_env, process_snippet_placeholders
from ..specgen.snippets import validate_all_snippets
from ..specgen.tables import collect_slot_rows, load_type_hrefs


def _record_value(record: dict, key: str) -> Any:
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


def _as_block_list(value: object) -> list[dict]:
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
    title: str | None = None,
) -> str:
    body = _inline_html(process_description(str(text or ""))).strip()
    if not body:
        return ""
    if title:
        return f'<p class="note" title="{escape(str(title), quote=True)}">{body}</p>'
    return f'<div class="note">\n<p>{body}</p>\n</div>'


def _extract_enum_cell(
    pv: PermissibleValue,
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
    schema_view: SchemaView | None = None,
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
    for pv in pvs.values():
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
            rendered_segments.append(_render_inline_markdown(str(segment), process_description))
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
    schema_view: SchemaView | None = None,
) -> str:
    """Render the content blocks of annotation ``annotation_key`` as HTML; return ``""`` if there are none.

    Supported block types are ``markdown``, ``note``, ``assertion``, ``list``, ``assertion_list``, ``paragraph``
    and ``enum_table``; other types are logged and skipped. ``schema_view`` is needed by ``enum_table`` blocks.
    """
    blocks = _as_block_list(_annotation_value(annotations, annotation_key))
    if not blocks:
        return ""

    return _render_content_blocks(blocks, process_description, schema_view)


def _render_content_blocks(
    blocks: list[dict],
    process_description: Callable[[str], str],
    schema_view: SchemaView | None = None,
) -> str:
    rendered_blocks: list[str] = []
    for block in blocks:
        block_type = str(_record_value(block, "type") or "markdown")
        text = _record_value(block, "text") or ""

        if block_type == "markdown":
            rendered = process_description(str(text))
        elif block_type == "note":
            title = _record_value(block, "title")
            rendered = _render_note_block(str(text), process_description, title=str(title) if title else None)
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
    schema_view: SchemaView | None = None,
) -> str:
    """Render each entry of the ``spec_subsections`` annotation as a ``<section>``; return ``""`` if there are none.

    Each entry may set an ``id``, a ``class``, a ``title`` rendered as ``<h4>``, and ``content`` blocks rendered
    like those of :func:`render_spec_content_annotation`.
    """
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
            content_html = _render_content_blocks(content_blocks, process_description, schema_view)
            if content_html:
                lines.append(content_html)

        lines.append("</section>")
        rendered.append("\n".join(lines))

    return "\n".join(rendered)


def render_explicit_assertion_annotation(
    annotations: dict,
    process_description: Callable[[str], str],
) -> str:
    """Render LinkML assertion annotations.

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


def generate_respec_spec(spec: SpecConfig, root_schema: Path, resolved: ResolvedProject | None = None) -> None:
    """Render the specification described by the config file's ``spec`` section.

    Renders one table per class of every section's module, resolves glossary links with Bikeshed,
    validates and expands the example snippets, injects everything into the HTML template and,
    if configured, extracts the assertion inventory.

    Args:
        spec: The specification settings of the project config file.
        root_schema: Schema that imports all modules; class definitions are read from it.
        resolved: Views already loaded in this run; section schemas are loaded here when omitted.

    Raises:
        GenerationError: ``spec.first_class`` is not rendered by any section,
            or a snippet is invalid.
        SchemaError: A schema cannot be loaded.
        ExternalToolError: Bikeshed is missing or fails.
    """
    # Own merged load: the pipeline's merged view has been mutated by the artifact generators (from_schema rewritten).
    sv = load_schema_view(root_schema, merge_imports=True)
    if resolved is None:
        resolved = ResolvedProject(root_schema)
    section_tpl = build_jinja_env().get_template("class_section.jinja2")
    type_hrefs = load_type_hrefs(spec.glossary)
    fragments = [
        _render_section(
            sv,
            section_tpl,
            classes,
            spec.vocab_id_prefix,
            type_hrefs,
            spec.range_labels,
            spec.default_values_anchor,
        )
        for section, classes in zip(
            spec.sections, _classes_per_section(spec.sections, spec.first_class, resolved), strict=True
        )
    ]
    section_ids = [section.id for section in spec.sections]
    fragments = process_fragments(section_ids, fragments, spec.glossary)

    snippet_errors = validate_all_snippets(spec.snippets, spec.snippet_validation_schemas)
    if snippet_errors:
        raise GenerationError(
            f"{len(snippet_errors)} spec snippet(s) in {spec.snippets} are invalid:\n" + "\n".join(snippet_errors)
        )
    template = process_snippet_placeholders(spec.template.read_text(encoding="utf-8"), spec.snippets)

    assemble(
        spec.template, dict(zip(section_ids, fragments, strict=True)), out_path=spec.output, template_content=template
    )

    if spec.assertions_csv is not None:
        foreign_prefixes = sorted({section.prefix for section in spec.sections} - {spec.vocab_id_prefix})
        html_assertions_to_csv(spec.output, spec.assertions_csv, spec.extra_asserts, foreign_prefixes)


def _process_description(raw_text: str) -> str:
    """Convert inline markdown backticks to <code> tags."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", str(raw_text or ""))


def _classes_per_section(
    sections: Sequence[SpecSection], first_class: str | None, resolved: ResolvedProject
) -> list[list[str]]:
    """Return the names of the classes each section renders, in rendering order."""
    classes = [list(resolved.module(section.schema).all_classes(imports=False)) for section in sections]
    if classes:
        # The first section's schema imports the other modules; their classes belong to their own sections.
        rendered_later = {name for later in classes[1:] for name in later}
        classes[0] = [name for name in classes[0] if name not in rendered_later]
    if first_class is not None:
        if not any(first_class in names for names in classes):
            raise GenerationError(
                f"spec.first_class {first_class!r} is not a class of any spec section. "
                "Name a class of one of the section schemas or remove first_class from the config file."
            )
        classes = [_move_to_front(names, first_class) for names in classes]
    return classes


def _move_to_front(names: list[str], name: str) -> list[str]:
    if name not in names:
        return names
    return [name] + [other for other in names if other != name]


def _render_section(
    sv: SchemaView,
    section_tpl: Template,
    classes: list[str],
    vocab_id_prefix: str,
    type_hrefs: dict[str, str],
    range_labels: Mapping[str, str],
    default_values_anchor: str | None,
) -> str:
    rendered = (
        _render_class(sv, section_tpl, cls, vocab_id_prefix, type_hrefs, range_labels, default_values_anchor)
        for cls in classes
    )
    return "\n\n".join(html for html in rendered if html is not None)


def _render_class(
    sv: SchemaView,
    section_tpl: Template,
    cls: str,
    vocab_id_prefix: str,
    type_hrefs: dict[str, str],
    range_labels: Mapping[str, str],
    default_values_anchor: str | None,
) -> str | None:
    cdef = sv.get_class(cls)
    if not cdef:
        return None
    ann = getattr(cdef, "annotations", None) or {}
    spec_exclude_ann = ann.get("spec_exclude")
    if spec_exclude_ann:
        ann_value = getattr(spec_exclude_ann, "value", None)
        if ann_value is None:
            ann_value = spec_exclude_ann
        if str(ann_value).lower() == "true":
            logging.debug(
                "Skipping rendering of class %r due to spec_exclude=true annotation.",
                cls,
            )
            return None

    rows = collect_slot_rows(
        sv,
        cls,
        _process_description,
        vocab_id_prefix,
        type_hrefs=type_hrefs,
        range_labels=range_labels,
        default_values_anchor=default_values_anchor,
    )
    intro_html = ""
    desc_html = ""
    if "spec_intro_content" in ann:
        intro_html = render_spec_content_annotation(
            ann,
            _process_description,
            annotation_key="spec_intro_content",
        )
    else:
        raw_desc = getattr(cdef, "description", "") or ""
        if "spec_description" in ann:
            spec_def = getattr(ann["spec_description"], "value", None) or ann["spec_description"]
            raw_desc = str(spec_def) or raw_desc
        desc_html = _process_description(raw_desc)
    spec_content_html = ""
    if "spec_content" in ann:
        spec_content_html = render_spec_content_annotation(
            ann,
            _process_description,
            schema_view=sv,
        )
    assertion_html = render_explicit_assertion_annotation(
        ann,
        _process_description,
    )
    if assertion_html:
        spec_content_html = "\n".join(part for part in [spec_content_html, assertion_html] if part)

    subsections_html = ""
    if "spec_subsections" in ann:
        subsections_html = render_subsections(
            ann,
            _process_description,
            schema_view=sv,
        )

    return section_tpl.render(
        class_name=cls,
        class_description=desc_html,
        slots=rows,
        spec_intro_html=intro_html,
        spec_content_html=spec_content_html,
        subsections_html=subsections_html,
    )

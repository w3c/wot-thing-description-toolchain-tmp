from __future__ import annotations
from jinja2 import exceptions
import logging, yaml
from pathlib import Path
from typing import List

from linkml_runtime.utils.schemaview import SchemaView

from .specgen.config import Config
from .specgen.glossary import load_glossary, annotate_html
from .specgen.bibliography import load_bibliography, link_biblio_keys
from .specgen.markdown import render_markdown_html
from .specgen.tables import collect_slot_rows
from .specgen.respec import build_jinja_env, assemble

cfg = Config.from_resources_dir(Path("resources"), placeholder="%s")


def generate_respec_spec(
    input_path: Path,
    respec_template_path: Path,
    final_spec_path: Path,
    core_schema_placeholder: str,
) -> None:
    """
    Generate the complete ReSpec-compatible HTML document from a LinkML schema.

    This function:
      • Loads the LinkML model via SchemaView
      • Converts Markdown and annotations to HTML
      • Applies glossary and bibliography linking
      • Renders each class section with Jinja templates
      • Injects the resulting HTML into the ReSpec index template

    Args:
        input_path: Path to the root LinkML YAML schema file.
        respec_template_path: Path to the ReSpec HTML template (index.template.html).
        final_spec_path: Path to write the final, assembled HTML output.
        core_schema_placeholder: The placeholder string inside the ReSpec template to replace.
    """
    try:
        sv = SchemaView(input_path, merge_imports=True)
    except yaml.YAMLError as e:
        logging.error("Failed to load LinkML schema: %s", e)
        return

    try:
        env = build_jinja_env(cfg.jinja_templates)

        # Load glossary and expose annotate() to Jinja
        glossary_entries, phrase_to_key = load_glossary(cfg.glossary_path)
        env.filters["annotate"] = lambda s: annotate_html(s or "", glossary_entries, phrase_to_key)

        section_tpl = env.get_template("class_section.jinja2")
    except (exceptions.TemplateNotFound, FileNotFoundError) as e:
        logging.error("Template error: %s", e, exc_info=True)
        assemble(
            respec_template_path,
            f"<!-- template error: {e} -->",
            final_spec_path,
            core_schema_placeholder,
        )
        return

    # class order: Thing first
    classes_in_order: List[str] = list(sv.all_classes().keys())
    classes: List[str] = []
    if "Thing" in classes_in_order:
        classes.append("Thing")
        classes.extend(c for c in classes_in_order if c != "Thing")
    else:
        classes = classes_in_order

    biblio = load_bibliography(cfg.biblio_path)

    def process_description(raw_text: str) -> str:
        """Markdown rendering, bibliography linking, and glossary annotation."""
        html = render_markdown_html(raw_text or "")
        html = link_biblio_keys(html, biblio)
        html = annotate_html(html, glossary_entries, phrase_to_key)
        return html

    sections_html: List[str] = []
    for cls in classes:
        cdef = sv.get_class(cls)
        if not cdef:
            continue

        rows = collect_slot_rows(sv, cls, process_description)

        # Class description
        desc_html = process_description(getattr(cdef, "description", "") or "")

        # Optional spec_scope_note
        note_html = ""
        ann = getattr(cdef, "annotations", None) or {}
        if "spec_scope_note" in ann:
            raw = getattr(ann["spec_scope_note"], "value", None) or ann["spec_scope_note"]
            note_html = render_markdown_html(str(raw))
            note_html = link_biblio_keys(note_html, biblio)
            note_html = annotate_html(note_html, glossary_entries, phrase_to_key)

        sections_html.append(
            section_tpl.render(
                class_name=cls,
                class_description=desc_html,
                slots=rows,
                spec_scope_note_html=note_html,
            )
        )
    assemble(
        respec_template_path,
        "\n\n".join(sections_html),
        final_spec_path,
        core_schema_placeholder,
    )
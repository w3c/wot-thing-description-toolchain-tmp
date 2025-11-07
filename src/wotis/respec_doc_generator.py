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


def generate_respec_spec(input_path: Path,
                         respec_template_path: Path,
                         final_spec_path: Path,
                         core_schema_placeholder: str) -> None:
    """Generate the Respec HTML from LinkML schema + Jinja templates."""
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
        assemble(respec_template_path, f"<!-- template error: {e} -->", final_spec_path, core_schema_placeholder)
        return

    # class order: Thing first
    classes: List[str] = list(sv.all_classes().keys())
    classes = (["Thing"] + sorted(c for c in classes if c != "Thing")) if "Thing" in classes else sorted(classes)
    _, _, phrase_to_id = load_glossary(cfg.glossary_path)
    biblio = load_bibliography(cfg.biblio_path)

    sections_html: List[str] = []
    for cls in classes:
        cdef = sv.get_class(cls)
        if not cdef:
            continue
        rows = collect_slot_rows(sv, cls)
        desc_html = render_markdown_html(getattr(cdef, "description", "") or "")
        desc_html = link_biblio_keys(desc_html, biblio)
        desc_html = annotate_html(desc_html, phrase_to_id)
        note_html = ""
        ann = getattr(cdef, "annotations", None) or {}
        if "spec_scope_note" in ann:
            raw = getattr(ann["spec_scope_note"], "value", None) or ann["spec_scope_note"]
            note_html = render_markdown_html(str(raw))
            note_html = link_biblio_keys(note_html, biblio)
            note_html = annotate_html(note_html, phrase_to_id)
        sections_html.append(section_tpl.render(
            class_name=cls,
            class_description=desc_html,
            slots=rows,
            spec_scope_note_html=note_html,
        ))
    assemble(respec_template_path, "\n\n".join(sections_html), final_spec_path, core_schema_placeholder)

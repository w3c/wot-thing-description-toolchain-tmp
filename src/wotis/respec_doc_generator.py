from __future__ import annotations
from jinja2 import exceptions
import logging, yaml
from pathlib import Path
from typing import Dict, List

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
            f"",
            "",
            "",
            "",
            out_path=final_spec_path,
            placeholder=core_schema_placeholder,
        )
        return

    biblio = load_bibliography(cfg.biblio_path)

    def process_description(raw_text: str) -> str:
        """Markdown rendering, bibliography linking, and glossary annotation."""
        html = render_markdown_html(raw_text or "")
        html = link_biblio_keys(html, biblio)
        html = annotate_html(html, glossary_entries, phrase_to_key)
        return html

    file_to_classes: Dict[str, List[str]] = {}
    for section_path in cfg.section_schemas.values():
        try:
            if not section_path.exists():
                logging.error(f"Missing schema file: {section_path.name}. Cannot render this section.")
                file_to_classes[section_path.name] = []
                continue
            # Load each section schema without merging imports to see its classes
            section_sv = SchemaView(section_path, merge_imports=False)
            file_to_classes[section_path.name] = list(section_sv.all_classes().keys())
        except (yaml.YAMLError, IOError) as e:
            logging.error(f"Failed to load section schema {section_path.name} due to: {e}. Skipping section.")
            file_to_classes[section_path.name] = []

    # Identify all non-core classes (defined outside the primary TD schema)
    non_core_classes: set[str] = set()
    try:
        core_section_id = next(iter(cfg.section_schemas.keys()))
    except StopIteration:
        core_section_id = None

    for section_id, section_path in cfg.section_schemas.items():
        if section_id != core_section_id:
            # add all classes from non-core schemas to the exclusion set
            non_core_classes.update(file_to_classes.get(section_path.name, []))

    # extract classes order and build content
    sections_content: List[str] = []

    for section_id, section_path in cfg.section_schemas.items():
        # Get the classes defined in the current section's file
        section_classes_to_render = file_to_classes.get(section_path.name, [])
        sections_html: List[str] = []
        # filter the core vocabulary section
        if section_id == core_section_id and core_section_id is not None:
            # Exclude any class that is defined in one of the other schema files
            section_classes_to_render = [
                cls for cls in section_classes_to_render if cls not in non_core_classes
            ]
        # Enforce 'Thing' first
        if 'Thing' in section_classes_to_render:
            section_classes_to_render.remove('Thing')
            section_classes_to_render.insert(0, 'Thing')
        # Generate HTML for classes belonging ONLY to this section
        for cls in section_classes_to_render:
            cdef = sv.get_class(cls)
            if not cdef:
                continue
            ann = getattr(cdef, "annotations", None) or {}
            spec_exclude_ann = ann.get("spec_exclude")
            if spec_exclude_ann:
                ann_value = getattr(spec_exclude_ann, 'value', None)
                if ann_value is None:
                    ann_value = spec_exclude_ann

                if str(ann_value).lower() == 'true':
                    logging.debug(f"Skipping rendering of class '{cls}' due to spec_exclude=true annotation.")
                    continue

            rows = collect_slot_rows(sv, cls, process_description)
            # Class description
            raw_desc = getattr(cdef, "description", "") or ""
            ann = getattr(cdef, "annotations", None) or {}
            if "spec_table_definition" in ann:
                spec_def = getattr(ann["spec_table_definition"], "value", None) or ann["spec_table_definition"]
                raw_desc = str(spec_def) or raw_desc

            desc_html = process_description(raw_desc)

            # Optional spec_scope_note
            note_html = ""
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

        section_html_fragment = "\n\n".join(sections_html)
        # Escape all literal percent signs in the fragment content.
        escaped_fragment = section_html_fragment.replace('%', '%%')
        sections_content.append(escaped_fragment)

    assemble(
        respec_template_path,
        *sections_content,
        out_path=final_spec_path,
        placeholder=core_schema_placeholder,
    )
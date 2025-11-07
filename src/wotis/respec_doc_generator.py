import logging
import re
import yaml

from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader, exceptions, select_autoescape
from linkml_runtime.utils.schemaview import SchemaView
from pathlib import Path
from typing import Tuple, List, Dict

from src.wotis import JINJA_TEMPLATE_DIR, GLOSSARY_PATH, BIBLIO_PATH


@dataclass
class GlossaryTerm:
    name: str
    id: str
    aliases: list


def _load_glossary() -> Tuple[list[GlossaryTerm], list[Tuple[re.Pattern, str]]]:
    """Load glossary.yaml and return (terms, compiled_patterns)."""
    if not GLOSSARY_PATH.exists():
        return [], []
    data = yaml.safe_load(GLOSSARY_PATH.read_text(encoding="utf-8")) or {}
    terms: list[GlossaryTerm] = []
    patterns: list[Tuple[re.Pattern, str]] = []
    for canonical, payload in (data.get("terms") or {}).items():
        gid = payload.get("id")
        aliases = payload.get("aliases", [])
        names = [canonical] + aliases
        terms.append(GlossaryTerm(name=canonical, id=gid, aliases=aliases))
        for n in sorted(set(names), key=len, reverse=True):
            # link plain text occurrences, avoid inside existing HTML tags
            pat = re.compile(rf"(?<![>/])\b({re.escape(n)})\b(?![^<]*?>)")
            patterns.append((pat, gid))
    return terms, patterns


def _annotate_terms(text: str, patterns_or_unused) -> str:
    """
    Longest-match, one-pass phrase linker that:
      - avoids existing <a ...>...</a> and <code>...</code> blocks
      - prefers longer glossary phrases (e.g., 'Thing Description' over 'Thing')
      - preserves original casing of matched text
    """
    if not text or "<table" in text:
        return text

    # Build a phrase->id map from the glossary file (canonical + aliases)
    # We load it once per call; if you prefer, refactor to pass this in alongside patterns.
    try:
        from src.wotis import GLOSSARY_PATH
        data = yaml.safe_load(GLOSSARY_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        data = {}

    phrase_to_id = {}
    for canonical, payload in (data.get("terms") or {}).items():
        gid = payload.get("id")
        for phrase in [canonical] + payload.get("aliases", []):
            # normalize spaces and case for lookup
            phrase_to_id[phrase.lower()] = gid

    if not phrase_to_id:
        return text

    # Build a single alternation of all phrases, longest first, word-boundary-ish
    phrases_sorted = sorted(phrase_to_id.keys(), key=len, reverse=True)
    # Escape each phrase for regex; allow spaces inside phrases
    alternation = "|".join(re.escape(p) for p in phrases_sorted)
    # Word boundaries around the whole phrase (covers multi-word too)
    pattern = re.compile(rf"(?<![>/])\b(?:{alternation})\b(?![^<]*?>)", flags=re.IGNORECASE)

    def replacer(m: re.Match):
        matched_text = m.group(0)
        gid = phrase_to_id.get(matched_text.lower())
        if not gid:
            return matched_text
        return f'<a href="#{gid}">{matched_text}</a>'

    # Protect existing anchors and code blocks: split, annotate only outside segments
    splitter = re.compile(r"(<a\b[^>]*>.*?</a>|<code>.*?</code>)", flags=re.DOTALL | re.IGNORECASE)
    parts = splitter.split(text)
    for i in range(0, len(parts), 2):  # even indices: outside protected blocks
        parts[i] = pattern.sub(replacer, parts[i])
    return "".join(parts)


def _normalize_admonitions_for_respec(html: str) -> str:
    """
    Convert Python-Markdown / markdown-it admonitions to Respec-style notes:
      <div class="admonition note"><p class="admonition-title">Note</p>BODY</div>
    -> <div class="note">BODY</div>
    Handles any admonition type but keeps only 'note' mapped to .note;
    other types (warning, tip) can be mapped similarly if you add CSS.
    """
    # 1) Strip the title <p class="admonition-title">…</p>
    html = re.sub(
        r'<div class="admonition\s+note">\s*<p class="admonition-title">.*?</p>\s*',
        '<div class="note">', html, flags=re.DOTALL | re.IGNORECASE
    )
    # 2) If admonition has no explicit title paragraph, still map class
    html = re.sub(
        r'<div class="admonition\s+note">',
        '<div class="note">', html, flags=re.IGNORECASE
    )
    # 3) Close tags are identical; nothing to change there
    return html



def _convert_fenced_admonitions_for_py_md(src: str) -> str:
    """
    Convert '::: note ... :::' (case-insensitive) blocks to Python-Markdown admonition:
      !!! note
          content...
    Handles multiple blocks. Preserves inner indentation and blank lines.
    """
    def repl(m: re.Match) -> str:
        kind = m.group("kind").lower()
        body = m.group("body").rstrip()
        # indent every non-empty line by 4 spaces
        indented = "\n".join(("    " + line if line.strip() != "" else "") for line in body.splitlines())
        return f"!!! {kind}\n{indented}\n"

    # start fence must be at line start; capture until closing fence on its own line
    pattern = re.compile(
        r"(?mi)^[ \t]*:::[ \t]*(?P<kind>[A-Za-z]+)[ \t]*\n(?P<body>.*?)[ \t]*\n[ \t]*:::[ \t]*$",
        flags=re.DOTALL | re.MULTILINE,
    )
    return pattern.sub(repl, src)



def _render_markdown_html(text: str, biblio: dict | None = None, breaks: bool = False) -> str:
    """
    Render Markdown to HTML with admonitions and sane lists.
    - If markdown-it-py is available, we use it (supports ::: note by default with mdit-py-plugins).
    - Else, fall back to Python-Markdown (expects !!! note; we auto-rewrite :::NOTE to !!! note).
    - After Markdown, apply [[BIBKEY]] links and return HTML.
    """
    s = (text or "").strip()
    if not s:
        return ""

    # Normalize your ":::NOTE" style to lowercase directive so plugins accept it.
    s = re.sub(r":::([A-Z]+)", lambda m: f":::{m.group(1).lower()}", s)

    html_out = None

    # --- Preferred: markdown-it-py ---
    try:
        from markdown_it import MarkdownIt
        from mdit_py_plugins.anchors import anchors
        from mdit_py_plugins.admon import admon_plugin
        from mdit_py_plugins.attrs import attrs_plugin
        from mdit_py_plugins.deflist import deflist_plugin

        md = MarkdownIt("commonmark", {"linkify": True, "breaks": breaks})
        md = md.use(admon_plugin).use(attrs_plugin).use(deflist_plugin).use(anchors)
        html_out = md.render(s)
    except Exception:
        pass

    # --- Fallback: Python-Markdown ---
    if html_out is None:
        try:
            s2 = _convert_fenced_admonitions_for_py_md(s)
            from markdown import markdown as md_markdown
            html_out = md_markdown(
                s2,
                extensions=["extra", "admonition", "sane_lists"],
                output_format="html5",
            )
        except Exception:
            html_out = None

    # --- Last-resort: very small converter (keeps your current NOTE + code + paragraphs) ---
    if html_out is None:
        def _note_block(m):
            inner = m.group(1).strip()
            return f'<div class="note">{inner}</div>'

        tmp = re.sub(r":::note\s*(.*?)\s*:::", _note_block, s, flags=re.DOTALL)
        tmp = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", tmp)
        parts = [p.strip() for p in re.split(r"\n\s*\n", tmp) if p.strip()]
        html_out = "".join(f"<p>{p}</p>" for p in parts) if parts else tmp

        # Normalize admonitions to Respec style (removes inner “Note” title)
    html_out = _normalize_admonitions_for_respec(html_out)

    # Bibliography replacement: [[KEY]] → link (known keys), else keep [[KEY]] for ReSpec
    def _double_bracket(m):
        token = m.group(1)
        if biblio and token.upper() in biblio:
            ref = biblio[token.upper()]
            href = ref.get("href", "")
            title = ref.get("title", token)
            return f'<a href="{href}" title="{title}">[{token}]</a>'
        return f"[[{token}]]"
    html_out = re.sub(r"\[\[([^\]]+)\]\]", _double_bracket, html_out)

    return html_out



def _load_bibliography() -> dict[str, dict[str, str]]:
    """Load bibliography mapping (key -> {href,title})."""
    if not BIBLIO_PATH.exists():
        return {}
    data = yaml.safe_load(BIBLIO_PATH.read_text(encoding="utf-8")) or {}
    return data.get("bibliography", {})


def get_assignment(slot_name: str, class_def: object, slot_def: object) -> str:
    """
    Determines the assignment (mandatory/optional) for a slot based on LinkML properties
    and slot_usage overrides within the class.

    :param slot_name: The name of the slot.
    :param class_def: The LinkML ClassDefinition object.
    :param slot_def: The LinkML SlotDefinition object.
    :return: 'mandatory' or 'optional'.
    """

    slot_usage = (class_def.slot_usage or {}).get(slot_name)
    if getattr(slot_def, "required", False) or (slot_usage and getattr(slot_usage, "required", False)):
        return "mandatory"

    min_value = getattr(slot_def, "minimum_value", None)
    if slot_usage and getattr(slot_usage, "minimum_value", None) is not None:
        min_value = slot_usage.minimum_value
    try:
        if min_value is not None and float(min_value) > 0:
            return "mandatory"
    except Exception:
        pass
    return "optional"


def assemble_respec_spec(template_path: Path, fragment_content: str, final_path: Path, placeholder: str):
    """
    Reads the Respec template and injects the pre-formatted content into the final HTML spec.

    :param template_path: Path to the Respec HTML template.
    :param fragment_content: The HTML fragment (the table) to inject.
    :param final_path: Path to save the final Respec HTML file.
    :param placeholder: The placeholder string to replace in the template.
    """
    logging.info("Assembling final Respec specification by injecting pre-formatted content...")
    if not template_path.exists():
        logging.error(f"Respec template not found at {template_path}. Cannot assemble spec.")
        return
    respec_template = template_path.read_text(encoding='utf-8')
    if placeholder not in respec_template:
        logging.error(
            f"Placeholder '{placeholder}' was NOT found in the template: {template_path}. "
            f"This is why the replacement failed and the placeholder is still visible."
        )
        return
    final_content = respec_template.replace(placeholder, fragment_content)
    final_path.write_text(final_content, encoding='utf-8')
    logging.info(f"Final Respec specification saved to {final_path}. Injected content length: {len(fragment_content)}.")


def _slot_range_text(slot_name: str, slot_def, class_def) -> str:
    """
    Compute the Type column strictly from the LinkML schema:
      - prefer slot_usage.exactly_one_of if present (detect "X or Array of X")
      - else fall back to inlined / multivalued / range
    No special-casing of @context/@type labels.
    """
    # 1) Prefer class-level slot_usage.exactly_one_of
    slot_usage = (getattr(class_def, "slot_usage", None) or {}).get(slot_name)
    xo = getattr(slot_usage, "exactly_one_of", None) if slot_usage else None

    if xo:
        # Gather (range, multivalued) per alternative
        alts = []
        for alt in xo:
            rng = getattr(alt, "range", None) or getattr(slot_def, "range", None) or "any type"
            mv = bool(getattr(alt, "multivalued", False))
            alts.append((rng, mv))

        # If same range appears in both single and multivalued, show "X or Array of X"
        ranges = {rng for rng, _ in alts}
        for rng in ranges:
            flags = {mv for rr, mv in alts if rr == rng}
            if flags == {False, True}:
                return f"{rng} or Array of {rng}"

        # Otherwise, show a simple union like "X | Y" (and "(Array)" where applicable)
        pretty = []
        for rng, mv in alts:
            pretty.append(f"{rng} (Array)" if mv else rng)
        return " | ".join(dict.fromkeys(pretty))  # preserve order, dedupe

    # 2) Fallback: slot-level shape
    range_name = getattr(slot_def, "range", None) or "any type"
    is_multivalued = bool(getattr(slot_def, "multivalued", False))
    is_inlined = bool(getattr(slot_def, "inlined", False))

    if is_inlined:
        return f"Map of {range_name}"
    if is_multivalued:
        return f"{range_name} (Array)"
    return range_name



def _collect_slot_rows(sv: SchemaView, class_name: str) -> List[Dict[str, str]]:
    """Build rows for the vocabulary table of a class."""
    class_def = sv.get_class(class_name)
    rows: List[Dict[str, str]] = []
    for slot_name in class_def.slots or []:
        slot_def = sv.get_slot(slot_name)
        description = getattr(slot_def, "description", "") or ""
        assignment = get_assignment(slot_name, class_def, slot_def)
        range_text = _slot_range_text(slot_name, slot_def, class_def)

        escaped_description = description.replace("'", "&#39;").replace('"', "&quot;")
        rows.append(
            {
                "slot_name": slot_name,
                "description": escaped_description,
                "assignment": assignment,
                "range_text": range_text,
            }
        )
    return rows


def assemble_respec_spec(template_path: Path, fragment_content: str, final_path: Path, placeholder: str):
    logging.info("Assembling final Respec specification by injecting pre-formatted content...")
    if not template_path.exists():
        logging.error(f"Respec template not found at {template_path}. Cannot assemble spec.")
        return
    respec_template = template_path.read_text(encoding="utf-8")
    if placeholder not in respec_template:
        logging.error(
            f"Placeholder '{placeholder}' was NOT found in the template: {template_path}. "
            f"This is why the replacement failed and the placeholder is still visible."
        )
        return
    final_content = respec_template.replace(placeholder, fragment_content)
    final_path.write_text(final_content, encoding="utf-8")
    logging.info(f"Final Respec specification saved to {final_path}. Injected content length: {len(fragment_content)}.")


def generate_respec_spec(input_path: Path, respec_template_path: Path, final_spec_path: Path,
                         core_schema_placeholder: str):
    """
    Generates the custom HTML table for the 'Thing' class and assembles the
    final Respec specification using Jinja2 templates.

    :param input_path: Path to the input LinkML schema file.
    :param respec_template_path: Path to the Respec HTML template.
    :param final_spec_path: Path to save the final Respec HTML file.
    :param core_schema_placeholder: The placeholder string in the template.
    """
    try:
        sv = SchemaView(input_path, merge_imports=True)
    except yaml.YAMLError as e:
        logging.error(f"Failed to load LinkML schema for Respec generation: {e}")
        return

        # order: Thing first if present, then alpha
    classes = list(sv.all_classes().keys())
    if "Thing" in classes:
        classes.remove("Thing")
        classes = ["Thing"] + sorted(classes)
    else:
        classes = sorted(classes)

    # glossary
    _, glossary_patterns = _load_glossary()

    # Jinja env
    try:
        if not JINJA_TEMPLATE_DIR.is_dir():
            raise exceptions.TemplateNotFound(
                f"Template directory not found: {JINJA_TEMPLATE_DIR}. Please ensure 'resources/jinja_templates' exists."
            )
        env = Environment(
            loader=FileSystemLoader(JINJA_TEMPLATE_DIR),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        env.filters["annotate"] = lambda s: _annotate_terms(s, glossary_patterns)
        section_tpl = env.get_template("class_section.jinja2")
    except exceptions.TemplateNotFound as e:
        logging.error(f"Jinja2 template rendering failed: {e}", exc_info=True)
        assemble_respec_spec(respec_template_path, f"<!-- template error: {e} -->", final_spec_path,
                             core_schema_placeholder)
        return
    except Exception as e:
        logging.error(f"Jinja2 environment setup failed: {e}", exc_info=True)
        assemble_respec_spec(respec_template_path, f"<!-- jinja init error: {e} -->", final_spec_path,
                             core_schema_placeholder)
        return

    biblio = _load_bibliography()
    # render sections
    sections_html: List[str] = []
    for cls in classes:
        class_def = sv.get_class(cls)
        if not class_def:
            continue

        rows = _collect_slot_rows(sv, cls)

        class_desc_html = _render_markdown_html(getattr(class_def, "description", "") or "", biblio)
        class_desc = _annotate_terms(class_desc_html, glossary_patterns)

        # spec_scope_note (optional)
        note_html = ""
        ann = getattr(class_def, "annotations", None) or {}
        if "spec_scope_note" in ann:
            raw = getattr(ann["spec_scope_note"], "value", None) or ann["spec_scope_note"]
            note_html = _render_markdown_html(str(raw), biblio, breaks=False)
            note_html = _annotate_terms(note_html, glossary_patterns)

        html_section = section_tpl.render(
            class_name=cls,
            class_description=class_desc,
            slots=rows,
            spec_scope_note_html=note_html,
        )
        sections_html.append(html_section)

    fragment = "\n\n".join(sections_html)
    logging.info(f"Generated HTML fragment for {len(sections_html)} classes; length={len(fragment)}.")
    assemble_respec_spec(respec_template_path, fragment, final_spec_path, core_schema_placeholder)

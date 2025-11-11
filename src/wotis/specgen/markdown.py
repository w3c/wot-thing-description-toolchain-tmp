from __future__ import annotations
import re
import logging
from markdown import markdown as md_markdown


def _convert_fenced_for_py_md(src: str) -> str:
    """
    Convert :::NOTE blocks (with optional blank lines and indentation)
    into Python-Markdown admonitions of form:

        !!! note
            content...
    """

    def repl(m: re.Match) -> str:
        kind = m.group("kind").lower()
        body = m.group("body")
        body = body.strip()
        indented = "\n".join(
            ("    " + line)
            for line in body.splitlines()
        )
        return f"\n\n!!! {kind}\n{indented}\n\n"

    # Match :::KIND on a line, capture everything until closing :::
    pattern = re.compile(
        r":::\s*(?P<kind>[A-Za-z]+)\s*\n(?P<body>.*?)\n\s*:::",
        re.DOTALL
    )
    result = pattern.sub(repl, src)
    return result


def _normalize_and_wrap_notes(html: str) -> str:
    """
    Normalize Python-Markdown admonitions into simple
    <div class="note"> ... </div> blocks, without adding
    an extra rendered “Note” heading inside.
    """
    # 1) Remove the title paragraph Python-Markdown inserts
    html = re.sub(
        r'<p\s+class="admonition-title">.*?</p>\s*',
        '',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    # 2) Replace the outer container from "admonition note" to just "note"
    html = re.sub(
        r'<div\s+class="admonition\s+note">',
        '<div class="note">',
        html,
        flags=re.IGNORECASE,
    )
    # 3) Safety: if there is a top-level <p>Note</p> immediately inside, drop it too
    html = re.sub(
        r'(<div class="note">\s*)<p>\s*Note\s*</p>\s*',
        r'\1',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return html


def render_markdown_html(text: str, breaks: bool = False) -> str:
    """
    Render Markdown with :::NOTE fenced blocks to HTML suitable for ReSpec.
    """
    s = text or ""
    if not s:
        return ""

    lines = s.splitlines()
    if lines:
        min_indent = min(
            (len(line) - len(line.lstrip()) for line in lines if line.strip()),
            default=0
        )
        s = "\n".join(line[min_indent:] if len(line) >= min_indent else line for line in lines)

    # Normalize :::NOTE → :::note
    s = re.sub(r":::([A-Z]+)", lambda m: f":::{m.group(1).lower()}", s)

    print("DEBUG - AFTER CASE NORMALIZATION:")
    print(repr(s[:200]))

    html = None
    if html is None:
        try:
            converted = _convert_fenced_for_py_md(s)
            # Ensure the converted text starts with a newline for proper parsing
            if not converted.startswith('\n'):
                converted = '\n' + converted
            html = md_markdown(
                converted,
                extensions=["extra", "admonition", "sane_lists"],
                output_format="html5",
            )
        except Exception as e:
            logging.warning("Markdown conversion failed: %s", e)
            print(f"DEBUG - Python-Markdown failed: {e}")
            html = None

    if html is None:
        html = re.sub(
            r":::note\s*\n(.*?)\n\s*:::",
            lambda m: f'<div class="note"><p>{m.group(1).strip()}</p></div>',
            s,
            flags=re.DOTALL,
        )
    result = _normalize_and_wrap_notes(html)
    return result
from __future__ import annotations
import re
from markdown import markdown as md_markdown


def render_markdown_html(text: str) -> str:
    """
    Render Markdown to HTML suitable for ReSpec.
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
        # blank lines between paragraphs in LinkML
        s = "\n".join(
            (line[min_indent:] if len(line) >= min_indent else line)
            if line.strip()
            else ""
            for line in lines
        )
        s = re.sub(r"\n\s*\n", "\n\n", s)
        s = s.strip()
        s = "\n" + s + "\n"

    # forces paragraph break
    s = re.sub(
        r"(\S)\n(\s*\S)",
        r"\1\n\n\2",
        s,
        flags=re.DOTALL
    )
    return md_markdown(
        s,
        extensions=["extra", "sane_lists"],
        output_format="html5",
    )

from __future__ import annotations
from markdown_it import MarkdownIt
from mdit_py_plugins.admon import admon_plugin
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.attrs import attrs_plugin
from mdit_py_plugins.deflist import deflist_plugin
from markdown import markdown as md_markdown


import re


def _convert_fenced_for_py_md(src: str) -> str:
    def repl(m: re.Match) -> str:
        kind = m.group("kind").lower()
        body = m.group("body").rstrip()
        indented = "\n".join(("    " + line if line.strip() else "") for line in body.splitlines())
        return f"!!! {kind}\n{indented}\n"
    pattern = re.compile(r"(?mi)^[ \t]*:::[ \t]*(?P<kind>[A-Za-z]+)[ \t]*\n(?P<body>.*?)[ \t]*\n[ \t]*:::[ \t]*$",
                         re.DOTALL | re.MULTILINE)
    return pattern.sub(repl, src)

def _normalize_admonitions_for_respec(html: str) -> str:
    html = re.sub(r'<div class="admonition\s+note">\s*<p class="admonition-title">.*?</p>\s*',
                  '<div class="note">', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<div class="admonition\s+note">', '<div class="note">', html, flags=re.IGNORECASE)
    return html

def render_markdown_html(text: str, breaks: bool = False) -> str:
    s = (text or "").strip()
    if not s:
        return ""
    s = re.sub(r":::([A-Z]+)", lambda m: f":::{m.group(1).lower()}", s)

    # markdown-it library
    html = None
    try:
        md = MarkdownIt("commonmark", {"linkify": True, "breaks": breaks})
        md = md.use(admon_plugin).use(attrs_plugin).use(deflist_plugin).use(anchors_plugin)
        html = md.render(s)
    except Exception:
        pass

    if html is None:
        try:
            html = md_markdown(_convert_fenced_for_py_md(s),
                               extensions=["extra", "admonition", "sane_lists"],
                               output_format="html5")
        except Exception:
            # last resort: minimal
            tmp = re.sub(r":::note\s*(.*?)\s*:::", lambda m: f'<div class="note">{m.group(1).strip()}</div>',
                         s, flags=re.DOTALL)
            tmp = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", tmp)
            parts = [p.strip() for p in re.split(r"\n\s*\n", tmp) if p.strip()]
            html = "".join(f"<p>{p}</p>" for p in parts) if parts else tmp
    return _normalize_admonitions_for_respec(html)

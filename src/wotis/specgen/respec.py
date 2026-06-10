from __future__ import annotations

import logging

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup
from pathlib import Path


def build_jinja_env(templates_dir: Path, snippets_dir: Path | None = None) -> Environment:
    if not templates_dir.is_dir():
        raise FileNotFoundError(f"Template directory not found: {templates_dir}")
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    if snippets_dir and snippets_dir.is_dir():
        from .snippets import render_snippet, render_snippet_group
        env.globals["snippet"] = lambda name: Markup(render_snippet(name, snippets_dir))
        env.globals["snippet_group"] = lambda name: Markup(render_snippet_group(name, snippets_dir))
    return env


def assemble(
    template_path: Path,
    *fragments_html: str,
    out_path: Path,
    placeholder: str,
    template_content: str | None = None,
) -> None:
    if template_content is not None:
        final_content = template_content
    else:
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found at {template_path}")
        final_content = template_path.read_text(encoding="utf-8")
    for fragment in fragments_html:
        final_content = final_content.replace(placeholder, fragment, 1)
    out_path.write_text(final_content, encoding="utf-8")
    if final_content.count(placeholder) > 0:
        logging.warning(
            f"Warning: {final_content.count(placeholder)} placeholders were not replaced."
        )

    logging.info(
        "Wrote assembled ReSpec document to %s (%d total chars injected)",
        out_path,
        sum(len(f) for f in fragments_html)
    )

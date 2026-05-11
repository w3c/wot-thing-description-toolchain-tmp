from __future__ import annotations

import logging

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path


def build_jinja_env(templates_dir: Path) -> Environment:
    if not templates_dir.is_dir():
        raise FileNotFoundError(f"Template directory not found: {templates_dir}")
    return Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def assemble(template_path: Path, *fragments_html: str, out_path: Path, placeholder: str) -> None:
    """
    Assembles the final HTML spec by injecting multiple vocabulary fragments
    into the ReSpec template using sequential string replacement.
    """
    if not template_path.exists():
        raise FileNotFoundError(f"Respec template not found at {template_path}")

    tpl = template_path.read_text(encoding="utf-8")
    final_content = tpl
    for fragment in fragments_html:
        # We replace the placeholder with the fragment, only once (count=1).
        final_content = final_content.replace(placeholder, fragment, 1)
    out_path.write_text(final_content, encoding="utf-8")
    if final_content.count(placeholder) > 0:
        logging.warning(
            f"Warning: {final_content.count(placeholder)} placeholders were not replaced."
        )

    logging.info(
        "Wrote multi-section spec to %s (%d total chars injected)",
        out_path,
        sum(len(f) for f in fragments_html)
    )

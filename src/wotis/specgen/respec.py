from __future__ import annotations
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
import logging

def build_jinja_env(templates_dir: Path) -> Environment:
    if not templates_dir.is_dir():
        raise FileNotFoundError(f"Template directory not found: {templates_dir}")
    return Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

def assemble(template_path: Path, fragment_html: str, out_path: Path, placeholder: str) -> None:
    if not template_path.exists():
        raise FileNotFoundError(f"Respec template not found at {template_path}")
    tpl = template_path.read_text(encoding="utf-8")
    if placeholder not in tpl:
        raise ValueError(f"Placeholder '{placeholder}' not found in {template_path}")
    out_path.write_text(tpl.replace(placeholder, fragment_html), encoding="utf-8")
    logging.info("Wrote spec to %s (%d chars injected)", out_path, len(fragment_html))

"""Assemble the specification HTML from its template, rendered section fragments and example snippets."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from ..errors import GenerationError
from .snippets import load_snippet_manifest, render_snippet, render_snippet_group

_SNIPPET_PLACEHOLDER_RE = re.compile(r"%snippet\('([^']+)'\)%")
_SECTION_PLACEHOLDER_RE = re.compile(r"%section\('([^']+)'\)%")


def process_snippet_placeholders(text: str, snippets_dir: Path) -> str:
    """Replace each ``%snippet('name')%`` with the rendered snippet or snippet group of that name.

    Args:
        text: Template text containing the placeholders.
        snippets_dir: Directory holding the snippet JSON files and their manifest.

    Returns:
        ``text`` with every placeholder replaced.

    Raises:
        GenerationError: The manifest is unusable, a name is unknown or names both a snippet and a group.
    """
    manifest = load_snippet_manifest(snippets_dir)
    groups = manifest.get("groups", {})

    snippets = manifest.get("snippets", {})

    def _replace(m: re.Match[str]) -> str:
        name = m.group(1)
        if name in groups and name in snippets:
            raise GenerationError(f"'{name}' exists as both snippet and group in the snippet manifest — rename one")
        if name in groups:
            return render_snippet_group(name, snippets_dir, manifest)
        return render_snippet(name, snippets_dir, manifest)

    return _SNIPPET_PLACEHOLDER_RE.sub(_replace, text)


def build_jinja_env() -> Environment:
    """Create the Jinja environment for the specification templates shipped with the package.

    Returns:
        An environment that loads templates from the ``wot_toolchain`` package data.
    """
    return Environment(
        loader=PackageLoader("wot_toolchain", "templates"),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def assemble(
    template_path: Path,
    fragments_by_section: Mapping[str, str],
    *,
    out_path: Path,
    template_content: str | None = None,
) -> None:
    """Replace each ``%section('<id>')%`` in the template with the fragment of that section and write ``out_path``.

    Args:
        template_path: Template file; read only when ``template_content`` is not given, named in errors.
        fragments_by_section: HTML fragment per section id.
        out_path: Output file; its parent directories are created.
        template_content: Template text to use instead of reading ``template_path``.

    Raises:
        GenerationError: ``template_content`` is not given and ``template_path`` does not exist,
            a marker names no given section, or a given section has no marker.
    """
    if template_content is not None:
        final_content = template_content
    else:
        if not template_path.exists():
            raise GenerationError(f"Specification template not found: {template_path}")
        final_content = template_path.read_text(encoding="utf-8")

    marked = set(_SECTION_PLACEHOLDER_RE.findall(final_content))
    unknown = sorted(marked - fragments_by_section.keys())
    if unknown:
        raise GenerationError(
            f"Specification template {template_path} has %section()% markers for section id(s) {unknown} "
            "that are not in spec.sections"
        )
    unused = sorted(fragments_by_section.keys() - marked)
    if unused:
        raise GenerationError(
            f"Section id(s) {unused} in spec.sections have no %section()% marker in specification template "
            f"{template_path}"
        )

    final_content = _SECTION_PLACEHOLDER_RE.sub(lambda m: fragments_by_section[m.group(1)], final_content)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(final_content, encoding="utf-8")

    logging.info(
        "Wrote assembled ReSpec document to %s (%d total chars injected)",
        out_path,
        sum(len(f) for f in fragments_by_section.values()),
    )

"""Resolve glossary links in rendered specification sections with Bikeshed."""

from __future__ import annotations

import importlib.util
import logging
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import yaml
from lxml import html as lxml_html

from ..errors import ExternalToolError, GenerationError

logger = logging.getLogger(__name__)

BYOS_METADATA = """\
<pre class='metadata'>
Title: WoT TD Fragment Processing
Group: byos
Status: LS
Shortname: wot-td-fragments
Abstract: Fragment processing for WoT Thing Description vocabulary sections.
Markup Shorthands: markdown yes, biblio no
Die On: nothing
</pre>
"""

SECTION_MARKER_ATTR = "data-wot-toolchain-section"
BIKESHED_TIMEOUT_SECONDS = 120
_BIKESHED_MISSING = (
    "bikeshed is not installed in the Python environment of wot-toolchain; it is needed to build the specification."
)


def require_bikeshed() -> None:
    """Check that ``bikeshed`` can be run.

    Raises:
        ExternalToolError: ``bikeshed`` is not installed next to this package.
    """
    if importlib.util.find_spec("bikeshed") is None:
        raise ExternalToolError(_BIKESHED_MISSING)


def build_anchors_block(glossary_path: Path) -> str:
    """Return a Bikeshed ``<pre class=anchors>`` block defining every glossary term and alias as a ``dfn``.

    Terms with an ``href`` link to that external URL; terms with only an ``id`` link to ``#<id>`` locally.
    Returns ``""`` if the glossary file is missing or defines no linkable terms.
    """
    if not glossary_path.exists():
        return ""
    data = yaml.safe_load(glossary_path.read_text(encoding="utf-8")) or {}
    terms = data.get("terms") or {}

    local_entries: list[tuple[str, str]] = []
    external_entries: dict[str, list[tuple[str, str]]] = {}

    for canonical, payload in terms.items():
        term_id = payload.get("id")
        href = payload.get("href")
        aliases = payload.get("aliases") or []

        if href:
            parsed = urlparse(str(href).strip().strip('"').strip("'"))
            prefix = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            fragment = parsed.fragment
            external_entries.setdefault(prefix, []).append((canonical, f"#{fragment}"))
            for alias in aliases:
                if alias and alias != canonical:
                    external_entries[prefix].append((alias, f"#{fragment}"))
        elif term_id:
            clean_id = str(term_id).strip().strip('"').strip("'")
            local_entries.append((canonical, f"#{clean_id}"))
            for alias in aliases:
                if alias and alias != canonical:
                    local_entries.append((alias, f"#{clean_id}"))

    if not local_entries and not external_entries:
        return ""

    lines = ["<pre class=anchors>"]

    if local_entries:
        lines.append("urlPrefix: ; type: dfn")
        for text, url in local_entries:
            lines.append(f"    text: {text}; url: {url}")

    for prefix, entries in external_entries.items():
        lines.append(f"urlPrefix: {prefix}; type: dfn")
        for text, url in entries:
            lines.append(f"    text: {text}; url: {url}")

    lines.append("</pre>")
    return "\n".join(lines)


def process_fragments(
    section_ids: list[str],
    fragments: list[str],
    glossary_path: Path,
) -> list[str]:
    """Run the section fragments through Bikeshed together and return them processed, in the same order.

    Args:
        section_ids: Section identifiers, one per fragment, used to split Bikeshed's output.
        fragments: HTML fragment of each section.
        glossary_path: Glossary YAML whose terms become Bikeshed anchors.

    Raises:
        ExternalToolError: Bikeshed is missing, fails, times out or produces no output.
        GenerationError: ``section_ids`` and ``fragments`` differ in length,
            or Bikeshed's output does not contain one marker per section.
    """
    if len(section_ids) != len(fragments):
        raise GenerationError(
            f"Cannot process specification sections with Bikeshed: {len(section_ids)} section ids but "
            f"{len(fragments)} fragment(s); every section needs exactly one fragment."
        )

    anchors_block = build_anchors_block(glossary_path)

    body_parts: list[str] = []
    for sid, frag in zip(section_ids, fragments, strict=True):
        body_parts.append(f'<span {SECTION_MARKER_ATTR}="{sid}"></span>')
        body_parts.append(frag)

    bs_source = "\n".join(
        [
            BYOS_METADATA,
            anchors_block,
            "",
            "\n".join(body_parts),
        ]
    )

    with tempfile.TemporaryDirectory(prefix="wot-toolchain-bikeshed-") as work_dir:
        bs_path = Path(work_dir) / "fragments.bs"
        html_path = bs_path.with_suffix(".html")
        bs_path.write_text(bs_source, encoding="utf-8")
        _run_bikeshed(bs_path, html_path)
        processed_html = html_path.read_text(encoding="utf-8")

    return _split_by_markers(_extract_body(processed_html), section_ids)


def _run_bikeshed(bs_path: Path, html_path: Path) -> None:
    """Run ``bikeshed spec``; raise ``ExternalToolError`` unless it produced output."""
    # Run as a module of this interpreter: a tool install exposes only the wot-toolchain entry point on PATH.
    command = [sys.executable, "-m", "bikeshed", "spec", str(bs_path), str(html_path), "--force"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=BIKESHED_TIMEOUT_SECONDS, check=False)
    except FileNotFoundError as exc:
        raise ExternalToolError(_BIKESHED_MISSING) from exc
    except subprocess.TimeoutExpired as exc:
        raise ExternalToolError(f"bikeshed did not finish within {BIKESHED_TIMEOUT_SECONDS} s.") from exc

    if result.returncode != 0:
        raise ExternalToolError(f"bikeshed exited with code {result.returncode}:\n{result.stderr}")
    if not html_path.exists():
        raise ExternalToolError(f"bikeshed produced no output:\n{result.stderr}")


def _extract_body(html_str: str) -> str:
    doc = lxml_html.fromstring(html_str)
    body = doc.find(".//body")
    if body is None:
        return html_str

    _strip_bikeshed_heading_decoration(body)

    parts: list[str] = []
    if body.text:
        parts.append(body.text)
    for child in body:
        parts.append(lxml_html.tostring(child, encoding="unicode"))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def _unwrap_element(el: lxml_html.HtmlElement) -> None:
    parent = el.getparent()
    if parent is None:
        return
    idx = list(parent).index(el)
    if el.text:
        prev = parent[idx - 1] if idx > 0 else None
        if prev is not None:
            prev.tail = (prev.tail or "") + el.text
        else:
            parent.text = (parent.text or "") + el.text
    for child in el:
        child.tail = child.tail or ""
        parent.insert(idx, child)
        idx += 1
    last_moved = parent[idx - 1] if idx > 0 else None
    if last_moved is not None:
        last_moved.tail = (last_moved.tail or "") + (el.tail or "")
    parent.remove(el)


def _strip_bikeshed_heading_decoration(root: lxml_html.HtmlElement) -> None:
    for secno in root.cssselect("span.secno"):
        secno.getparent().remove(secno)
    for selflink in root.cssselect("a.self-link"):
        selflink.getparent().remove(selflink)
    for panel in root.cssselect(".dfn-panel"):
        panel.getparent().remove(panel)
    for dfn in root.cssselect("dfn.dfn-paneled"):
        _unwrap_element(dfn)
    for heading in root.cssselect(".heading.settled"):
        heading.attrib.pop("class", None)
        heading.attrib.pop("data-level", None)
        content_span = heading.cssselect("span.content")
        if content_span:
            _unwrap_element(content_span[0])


def _split_by_markers(content: str, section_ids: list[str]) -> list[str]:
    marker_pattern = re.compile(rf'<span\s+{re.escape(SECTION_MARKER_ATTR)}="([^"]+)"\s*>\s*</span>')

    markers: list[tuple[int, str]] = []
    for m in marker_pattern.finditer(content):
        markers.append((m.end(), m.group(1)))

    if len(markers) != len(section_ids):
        raise GenerationError(f"Bikeshed output has {len(markers)} section markers, expected {len(section_ids)}.")

    fragments: list[str] = []
    for i, (start_pos, _sid) in enumerate(markers):
        if i + 1 < len(markers):
            next_marker_match = marker_pattern.search(content, start_pos)
            end_pos = next_marker_match.start() if next_marker_match else len(content)
        else:
            end_pos = len(content)
        fragments.append(content[start_pos:end_pos].strip())

    return fragments

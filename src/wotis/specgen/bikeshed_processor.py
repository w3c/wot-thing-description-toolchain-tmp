from __future__ import annotations

import logging
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import yaml
from lxml import html as lxml_html

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

SECTION_MARKER_ATTR = "data-wotis-section"


def build_anchors_block(glossary_path: Path) -> str:
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
    if len(section_ids) != len(fragments):
        raise ValueError(
            f"section_ids ({len(section_ids)}) and fragments ({len(fragments)}) must have the same length"
        )

    anchors_block = build_anchors_block(glossary_path)

    body_parts: list[str] = []
    for sid, frag in zip(section_ids, fragments):
        body_parts.append(f'<span {SECTION_MARKER_ATTR}="{sid}"></span>')
        body_parts.append(frag)

    bs_source = "\n".join([
        BYOS_METADATA,
        anchors_block,
        "",
        "\n".join(body_parts),
    ])

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".bs", delete=False, encoding="utf-8"
        ) as bs_file:
            bs_file.write(bs_source)
            bs_path = Path(bs_file.name)

        html_path = bs_path.with_suffix(".html")

        result = subprocess.run(
            ["bikeshed", "spec", str(bs_path), str(html_path), "--force"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            logger.warning("Bikeshed exited with code %d:\n%s", result.returncode, result.stderr)

        if not html_path.exists():
            logger.error("Bikeshed produced no output. Returning unprocessed fragments.")
            return list(fragments)

        processed_html = html_path.read_text(encoding="utf-8")
        body_content = _extract_body(processed_html)
        processed_fragments = _split_by_markers(body_content, section_ids)

        bs_path.unlink(missing_ok=True)
        html_path.unlink(missing_ok=True)

        return processed_fragments

    except Exception:
        logger.exception("Bikeshed fragment processing failed. Returning unprocessed fragments.")
        return list(fragments)


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


def _strip_bikeshed_heading_decoration(root) -> None:
    for secno in root.cssselect("span.secno"):
        secno.getparent().remove(secno)
    for selflink in root.cssselect("a.self-link"):
        selflink.getparent().remove(selflink)
    for panel in root.cssselect(".dfn-panel"):
        panel.getparent().remove(panel)
    for heading in root.cssselect(".heading.settled"):
        heading.attrib.pop("class", None)
        heading.attrib.pop("data-level", None)
        content_span = heading.cssselect("span.content")
        if content_span:
            span = content_span[0]
            parent = span.getparent()
            idx = list(parent).index(span)
            if span.text:
                prev = parent[idx - 1] if idx > 0 else None
                if prev is not None:
                    prev.tail = (prev.tail or "") + span.text
                else:
                    parent.text = (parent.text or "") + span.text
            for child in span:
                child.tail = child.tail or ""
                parent.insert(idx, child)
                idx += 1
            last_moved = parent[idx - 1] if idx > 0 else None
            if last_moved is not None:
                last_moved.tail = (last_moved.tail or "") + (span.tail or "")
            parent.remove(span)


def _split_by_markers(content: str, section_ids: list[str]) -> list[str]:
    marker_pattern = re.compile(
        rf'<span\s+{re.escape(SECTION_MARKER_ATTR)}="([^"]+)"\s*>\s*</span>'
    )

    markers: list[tuple[int, str]] = []
    for m in marker_pattern.finditer(content):
        markers.append((m.end(), m.group(1)))

    if len(markers) != len(section_ids):
        logger.warning(
            "Expected %d section markers, found %d. Returning content as single fragment.",
            len(section_ids),
            len(markers),
        )
        return [content] + [""] * (len(section_ids) - 1) if section_ids else [content]

    fragments: list[str] = []
    for i, (start_pos, _sid) in enumerate(markers):
        if i + 1 < len(markers):
            next_marker_match = marker_pattern.search(content, start_pos)
            end_pos = next_marker_match.start() if next_marker_match else len(content)
        else:
            end_pos = len(content)
        fragments.append(content[start_pos:end_pos].strip())

    return fragments

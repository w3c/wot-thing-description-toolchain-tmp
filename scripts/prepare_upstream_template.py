#!/usr/bin/env python3
"""Replace inline examples in the upstream template with snippet placeholder calls.

Temporary helper — will be removed after merging into the main repo.

Usage:
    python scripts/prepare_upstream_template.py

Input:  resources/upstream/html/index.template.html
Output: resources/index.template.html
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
UPSTREAM_TEMPLATE = REPO_ROOT / "resources" / "upstream" / "html" / "index.template.html"
OUTPUT_TEMPLATE = REPO_ROOT / "resources" / "index.template.html"

EXAMPLE_RE = re.compile(
    r"<(aside|pre)\s+class=\"example(?:\s+(?:ds-selector-tabs|with-default|json))?\"[^>]*>",
)

SNIPPET_CALLS: list[tuple[str, str]] = [
    ("snippet", "simple-td"),
    ("snippet", "td-context-extension"),
    ("snippet", "tm-model-sample"),
    ("snippet_group", "context-expansion"),
    ("snippet_group", "multiple-defaults"),
    ("snippet_group", "td-default-values"),
    ("snippet", "td-context-only"),
    ("snippet", "thing-serialization"),
    ("snippet", "i18n-title-description"),
    ("snippet", "i18n-rtl-direction"),
    ("snippet", "i18n-multi-language"),
    ("snippet", "i18n-default-language"),
    ("snippet", "version-info"),
    ("snippet", "security-basic"),
    ("snippet", "security-nosec"),
    ("snippet", "multiple-security-definitions1"),
    ("snippet", "multiple-security-definitions2a"),
    ("snippet", "multiple-security-definitions2b"),
    ("snippet", "security-in-forms"),
    ("snippet", "security-combo-oneof"),
    ("snippet", "security-oauth2-scopes"),
    ("snippet", "security-apikey"),
    ("snippet", "security-apikey-combo"),
    ("snippet", "security-apikey-body"),
    ("snippet", "security-apikey-body-simplified"),
    ("snippet", "property-serialization"),
    ("snippet", "action-serialization"),
    ("snippet", "event-serialization"),
    ("snippet", "link-serialization"),
    ("snippet", "link-service-doc"),
    ("snippet", "link-electric-drive"),
    ("snippet", "link-electric-motor"),
    ("snippet", "form-serialization"),
    ("snippet", "urivar-lat-long"),
    ("snippet", "urivar-city"),
    ("snippet", "urivar-city-unit"),
    ("snippet", "form-content-type"),
    ("snippet", "form-response"),
    ("snippet", "form-response-empty"),
    ("snippet", "form-additional-responses"),
    ("snippet", "form-content-media-encoding"),
    ("snippet", "td-forms-readall"),
    ("snippet", "urivar-thing-level"),
    ("snippet", "dataschema-serialization"),
    ("snippet", "dataschema-readonly-writeonly"),
    ("snippet", "context-extensions"),
    ("snippet", "semantic-version-units"),
    ("snippet", "saref-state-annotation"),
    ("snippet", "geolocation-basic"),
    ("snippet", "geolocation-schema-org"),
    ("snippet", "geolocation-jsonld-context"),
    ("snippet", "security-extension-ace"),
    ("snippet", "form-http-readproperty"),
    ("snippet", "form-modbus-readproperty"),
    ("snippet", "form-http-invokeaction"),
    ("snippet", "form-mqtt-subscribeevent"),
    ("snippet", "form-subprotocol-longpoll"),
    ("snippet", "payload-binding-forms"),
    ("snippet", "payload-json-object"),
    ("snippet", "payload-json-object-schema"),
    ("snippet", "tm-versioning"),
    ("snippet", "basic-on-off-tm"),
    ("snippet", "smart-lamp-control-tm"),
    ("snippet", "tm-ref-import"),
    ("snippet", "multi-sensor-tm"),
    ("snippet", "tm-overwrite"),
    ("snippet", "tm-extend-import"),
    ("snippet_group", "thing-model-composition"),
    ("snippet_group", "td-smart-ventilator"),
    ("snippet", "smart-ventilator-selfcontained-td"),
    ("snippet", "tm-optional"),
    ("snippet", "tm-optional-overwrite"),
    ("snippet_group", "td-from-tm"),
    ("snippet_group", "linking-td-to-tm"),
    ("snippet", "tm-extending-dim"),
    ("snippet", "td-derived-from-tm"),
    ("snippet_group", "coap-binding"),
    ("snippet_group", "mqtt-binding"),
    ("snippet_group", "temperature-sensor-event"),
    ("snippet", "multiprotocol-single"),
    ("snippet", "multiprotocol-mixed"),
    ("snippet", "payload-senml"),
    ("snippet", "payload-senml-schema"),
    ("snippet", "payload-ocf-batch"),
    ("snippet", "payload-ocf-batch-schema"),
    ("snippet", "payload-ipso-lwm2m"),
    ("snippet", "payload-ipso-lwm2m-schema"),
]


def _find_closing_tag(html: str, start: int, tag: str) -> int:
    """Find the end of the outermost element starting at ``start``.

    Handles nested elements of the same tag.
    """
    depth = 0
    open_re = re.compile(rf"<{tag}[\s>]")
    close_re = re.compile(rf"</{tag}\s*>")
    # Skip past the opening tag itself
    first_open = open_re.search(html, start)
    pos = first_open.end() if first_open else start

    while pos < len(html):
        open_match = open_re.search(html, pos)
        close_match = close_re.search(html, pos)

        if close_match is None:
            raise ValueError(f"No closing </{tag}> found from position {start}")

        if open_match and open_match.start() < close_match.start():
            depth += 1
            pos = open_match.end()
        else:
            if depth == 0:
                return close_match.end()
            depth -= 1
            pos = close_match.end()

    raise ValueError(f"No closing </{tag}> found from position {start}")


def _detect_indentation(html: str, pos: int) -> str:
    """Return the whitespace at the beginning of the line containing ``pos``."""
    line_start = html.rfind("\n", 0, pos)
    if line_start == -1:
        line_start = 0
    else:
        line_start += 1
    return html[line_start:pos] if html[line_start:pos].strip() == "" else ""


def prepare_template(upstream_html: str) -> tuple[str, list[str]]:
    """Replace inline examples with %snippet()% placeholder calls.

    Returns (transformed_html, warnings).
    """
    warnings: list[str] = []
    matches = list(EXAMPLE_RE.finditer(upstream_html))

    if len(matches) != len(SNIPPET_CALLS):
        warnings.append(
            f"Expected {len(SNIPPET_CALLS)} examples, found {len(matches)} — "
            f"upstream template may have changed"
        )
        if len(matches) < len(SNIPPET_CALLS):
            return upstream_html, warnings

    replacements: list[tuple[int, int, str]] = []

    for i, match in enumerate(matches):
        if i >= len(SNIPPET_CALLS):
            line = upstream_html[:match.start()].count("\n") + 1
            warnings.append(f"Extra example at line {line} — left inline")
            continue

        call_type, name = SNIPPET_CALLS[i]
        tag = match.group(1)
        element_start = match.start()

        try:
            element_end = _find_closing_tag(upstream_html, element_start, tag)
        except ValueError as exc:
            line = upstream_html[:element_start].count("\n") + 1
            warnings.append(f"Could not find closing tag at line {line}: {exc}")
            continue

        indent = _detect_indentation(upstream_html, element_start)
        snippet_call = f"{indent}%{call_type}('{name}')%"
        replacements.append((element_start, element_end, snippet_call))

    result = []
    prev_end = 0
    for start, end, replacement in replacements:
        result.append(upstream_html[prev_end:start])
        # Strip leading whitespace from the line since indent is in replacement
        chunk = upstream_html[prev_end:start]
        # Actually, just take everything up to the line start
        line_start = upstream_html.rfind("\n", prev_end, start)
        if line_start != -1 and upstream_html[line_start + 1 : start].strip() == "":
            result[-1] = upstream_html[prev_end : line_start + 1]
        result.append(replacement)
        prev_end = end
        # Skip trailing whitespace on the same line after the closing tag
        rest_of_line = upstream_html[end:]
        newline_pos = rest_of_line.find("\n")
        if newline_pos != -1 and rest_of_line[:newline_pos].strip() == "":
            prev_end = end + newline_pos

    result.append(upstream_html[prev_end:])
    return "".join(result), warnings


def main() -> int:
    if not UPSTREAM_TEMPLATE.exists():
        print(f"ERROR: upstream template not found: {UPSTREAM_TEMPLATE}", file=sys.stderr)
        return 1

    upstream_html = UPSTREAM_TEMPLATE.read_text(encoding="utf-8")
    output, warnings = prepare_template(upstream_html)

    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)

    OUTPUT_TEMPLATE.write_text(output, encoding="utf-8")

    example_count = len(SNIPPET_CALLS)
    warn_count = len(warnings)
    print(f"Replaced {example_count - warn_count}/{example_count} examples")
    if warnings:
        print(f"{warn_count} warning(s) — check stderr")

    return 0


if __name__ == "__main__":
    sys.exit(main())

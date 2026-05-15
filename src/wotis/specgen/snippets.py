from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft7Validator


logger = logging.getLogger(__name__)

_FRONTMATTER_RE = re.compile(
    r"^\s*/\*\s*\n---\n(.*?)\n---\s*\n\*/\s*\n?",
    re.DOTALL,
)

_HIDE_START_RE = re.compile(r"^(\s*)//\s*@hide-start\s*$")
_HIDE_END_RE = re.compile(r"^\s*//\s*@hide-end\s*$")

_JSONC_TOKEN_RE = re.compile(
    r'"(?:[^"\\]|\\.)*"'
    r"|/\*.*?\*/"
    r"|//[^\n]*",
    re.DOTALL,
)


@dataclass
class SnippetData:
    snippet_id: str = ""
    title: str = ""
    layout: str = "aside"
    validate: bool = True
    raw_jsonc: str = ""
    parsed_json: Any = None
    extra: dict[str, Any] = field(default_factory=dict)


def _extract_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    frontmatter_match = _FRONTMATTER_RE.match(text)
    if not frontmatter_match:
        return {}, text
    meta = yaml.safe_load(frontmatter_match.group(1)) or {}
    return meta, text[frontmatter_match.end() :]


def _process_hide_ranges(text: str) -> str:
    lines = text.split("\n")
    result: list[str] = []
    is_hiding = False
    indent = ""
    for line in lines:
        start_match = _HIDE_START_RE.match(line)
        if start_match:
            if is_hiding:
                raise ValueError("Nested // @hide-start without closing // @hide-end")
            is_hiding = True
            indent = start_match.group(1)
            continue
        if _HIDE_END_RE.match(line):
            if not is_hiding:
                raise ValueError("// @hide-end without matching // @hide-start")
            is_hiding = False
            if not result or result[-1].strip() != "// ...":
                result.append(f"{indent}// ...")
            continue
        if not is_hiding:
            result.append(line)
    if is_hiding:
        raise ValueError("Unclosed // @hide-start without // @hide-end")
    return "\n".join(result)


def _strip_jsonc_comments(text: str) -> str:
    def _replace(token_match: re.Match[str]) -> str:
        token = token_match.group(0)
        return token if token.startswith('"') else ""
    return _JSONC_TOKEN_RE.sub(_replace, text)


def _parse_snippet_file(snippet_path: Path) -> SnippetData:
    raw_text = snippet_path.read_text(encoding="utf-8")
    meta, body = _extract_frontmatter(raw_text)

    stripped = _strip_jsonc_comments(body)
    try:
        parsed_json = json.loads(stripped)
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON in snippet: %s", snippet_path.name)
        parsed_json = None

    return SnippetData(
        snippet_id=meta.get("id", ""),
        title=meta.get("title", ""),
        layout=meta.get("layout", "aside"),
        validate=meta.get("validate", True),
        raw_jsonc=body,
        parsed_json=parsed_json,
        extra={k: v for k, v in meta.items() if k not in {"id", "title", "layout", "validate"}},
    )


def _load_schema(schema_path: Path) -> Draft7Validator:
    raw = json.loads(schema_path.read_text(encoding="utf-8"))
    schema = json.loads(raw) if isinstance(raw, str) else raw
    return Draft7Validator(schema)


def _build_element_attrs(snippet_id: str, title: str) -> str:
    attrs = ' class="example"'
    if snippet_id:
        attrs += f' id="{escape(snippet_id, quote=True)}"'
    if title:
        attrs += f' title="{escape(title, quote=True)}"'
    return attrs


def validate_all_snippets(
    snippets_dir: Path,
    td_schema_path: Path,
    tm_schema_path: Path,
) -> list[str]:
    if not snippets_dir.exists():
        return []

    td_validator = _load_schema(td_schema_path)
    tm_validator = _load_schema(tm_schema_path)
    errors: list[str] = []

    for jsonc_file in sorted(snippets_dir.glob("*.jsonc")):
        if jsonc_file.stem == "TEMPLATE":
            continue

        snippet = _parse_snippet_file(jsonc_file)
        if not snippet.validate:
            logger.debug("Skipping validation (validate: false): %s", jsonc_file.name)
            continue

        if snippet.parsed_json is None:
            errors.append(f"{jsonc_file.name}: invalid JSON")
            continue

        _collect_schema_errors(snippet.parsed_json, jsonc_file.name, td_validator, tm_validator, errors)

    return errors


def _collect_schema_errors(
    instance: Any,
    filename: str,
    td_validator: Draft7Validator,
    tm_validator: Draft7Validator,
    errors: list[str],
) -> None:
    is_thing_model = isinstance(instance, dict) and instance.get("@type") == "tm:ThingModel"
    validator = tm_validator if is_thing_model else td_validator

    for error in validator.iter_errors(instance):
        path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"{filename}: {path} — {error.message}")


def render_snippet(name: str, snippets_dir: Path) -> str:
    snippet = _parse_snippet_file(snippets_dir / f"{name}.jsonc")
    filtered = _process_hide_ranges(snippet.raw_jsonc).strip()
    attrs = _build_element_attrs(snippet.snippet_id, snippet.title)

    if snippet.layout == "pre":
        return f"<pre{attrs}>\n{filtered}</pre>"

    return f"<aside{attrs}>\n<pre>\n{filtered}</pre>\n</aside>"


def render_snippet_group(group_name: str, snippets_dir: Path) -> str:
    group_path = snippets_dir / "groups" / f"{group_name}.yaml"
    if not group_path.exists():
        raise FileNotFoundError(f"Snippet group not found: {group_path}")

    group = yaml.safe_load(group_path.read_text(encoding="utf-8"))
    title = group.get("title", "")
    tabs = group.get("tabs", [])
    tab_group_id = f"snippetTab_{group_name}"

    lines: list[str] = ['<aside class="example ds-selector-tabs">']
    if title:
        _append_group_title(lines, title)
    _append_tab_selectors(lines, tabs, tab_group_id)
    _append_tab_contents(lines, tabs, tab_group_id, snippets_dir)
    lines.append("</aside>")
    return "\n".join(lines)


def _append_group_title(lines: list[str], title: str) -> None:
    lines.append('  <div class="marker">')
    lines.append(f'    <span class="example-title">{escape(title)}</span>')
    lines.append("  </div>")


def _append_tab_selectors(lines: list[str], tabs: list[dict[str, Any]], tab_group_id: str) -> None:
    lines.append('  <div class="selectors">')
    for tab in tabs:
        label = escape(tab.get("label", tab["snippet"]))
        tab_class = tab["snippet"].replace("-", "_")
        selected = "selected " if tab.get("selected") else ""
        lines.append(
            f'    <button class="{selected}{tab_group_id} {tab_class}"'
            f" onclick=\"openTab('{tab_group_id}', '{tab_class}')\">"
        )
        lines.append(f"      {label}")
        lines.append("    </button>")
    lines.append("  </div>")


def _append_tab_contents(
    lines: list[str],
    tabs: list[dict[str, Any]],
    tab_group_id: str,
    snippets_dir: Path,
) -> None:
    for tab in tabs:
        snippet = _parse_snippet_file(snippets_dir / f"{tab['snippet']}.jsonc")
        filtered = _process_hide_ranges(snippet.raw_jsonc).strip()
        tab_class = tab["snippet"].replace("-", "_")
        selected = " selected" if tab.get("selected") else ""
        lines.append(
            f'  <pre class="{tab_class} {tab_group_id}{selected} json">'
        )
        lines.append(filtered)
        lines.append("  </pre>")

from __future__ import annotations

import json
import logging
import re
from html import escape
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft7Validator


_FRONTMATTER_RE = re.compile(
    r"^\s*/\*\s*\n---\n(.*?)\n---\s*\n\*/\s*\n?",
    re.DOTALL,
)

_HIDE_START_RE = re.compile(r"^(\s*)//\s*@hide-start\s*$")
_HIDE_END_RE = re.compile(r"^\s*//\s*@hide-end\s*$")


def _extract_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    return meta, text[m.end() :]


def _process_hide_ranges(text: str) -> str:
    lines = text.split("\n")
    result: list[str] = []
    hiding = False
    indent = ""
    for line in lines:
        start_m = _HIDE_START_RE.match(line)
        if start_m:
            if hiding:
                raise ValueError("Nested // @hide-start without closing // @hide-end")
            hiding = True
            indent = start_m.group(1)
            continue
        if _HIDE_END_RE.match(line):
            if not hiding:
                raise ValueError("// @hide-end without matching // @hide-start")
            hiding = False
            if not result or result[-1].strip() != "// ...":
                result.append(f"{indent}// ...")
            continue
        if not hiding:
            result.append(line)
    if hiding:
        raise ValueError("Unclosed // @hide-start without // @hide-end")
    return "\n".join(result)


_JSONC_TOKEN_RE = re.compile(
    r'"(?:[^"\\]|\\.)*"'   # double-quoted string (skip)
    r"|/\*.*?\*/"          # block comment (strip)
    r"|//[^\n]*"           # line comment (strip)
    , re.DOTALL,
)


def _strip_jsonc_comments(text: str) -> str:
    def _replace(m: re.Match[str]) -> str:
        s = m.group(0)
        if s.startswith('"'):
            return s
        return ""
    return _JSONC_TOKEN_RE.sub(_replace, text)


def load_snippet(name: str, snippets_dir: Path) -> tuple[Any, dict[str, Any]]:
    jsonc_path = snippets_dir / f"{name}.jsonc"

    if not jsonc_path.exists():
        raise FileNotFoundError(f"Snippet file not found: {jsonc_path}")

    with jsonc_path.open(encoding="utf-8") as f:
        raw_text = f.read()

    meta, body = _extract_frontmatter(raw_text)
    stripped = _strip_jsonc_comments(body)
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        data = None

    meta["_raw_jsonc"] = body
    meta["_is_jsonc"] = True

    return data, meta


def validate_all_snippets(
    snippets_dir: Path,
    td_schema_path: Path,
    tm_schema_path: Path,
) -> list[str]:
    if not snippets_dir.exists():
        return []

    with td_schema_path.open(encoding="utf-8") as f:
        raw = json.load(f)
        td_schema = json.loads(raw) if isinstance(raw, str) else raw

    td_validator = Draft7Validator(td_schema)

    with tm_schema_path.open(encoding="utf-8") as f:
        raw = json.load(f)
        tm_schema = json.loads(raw) if isinstance(raw, str) else raw

    tm_validator = Draft7Validator(tm_schema)

    errors: list[str] = []

    for jsonc_file in sorted(snippets_dir.glob("*.jsonc")):
        if jsonc_file.stem == "TEMPLATE":
            continue

        with jsonc_file.open(encoding="utf-8") as f:
            raw_text = f.read()

        meta, body = _extract_frontmatter(raw_text)
        if meta.get("validate") is False:
            logging.debug("Skipping validation (validate: false): %s", jsonc_file.name)
            continue

        stripped = _strip_jsonc_comments(body)
        try:
            instance = json.loads(stripped)
        except json.JSONDecodeError as e:
            errors.append(f"{jsonc_file.name}: invalid JSON — {e}")
            continue

        is_tm = isinstance(instance, dict) and instance.get("@type") == "tm:ThingModel"
        validator = tm_validator if is_tm else td_validator

        for error in validator.iter_errors(instance):
            path = ".".join(str(p) for p in error.absolute_path) or "(root)"
            errors.append(f"{jsonc_file.name}: {path} — {error.message}")

    return errors


def render_snippet(name: str, snippets_dir: Path) -> str:
    _data, meta = load_snippet(name, snippets_dir)

    filtered = _process_hide_ranges(meta["_raw_jsonc"]).strip()

    snippet_id = meta.get("id", "")
    title = meta.get("title", "")
    layout = meta.get("layout", "aside")

    if layout == "pre":
        attrs = f' class="example"'
        if snippet_id:
            attrs += f' id="{escape(snippet_id, quote=True)}"'
        if title:
            attrs += f' title="{escape(title, quote=True)}"'
        return f"<pre{attrs}>\n{filtered}</pre>"

    aside_attrs = ' class="example"'
    if snippet_id:
        aside_attrs += f' id="{escape(snippet_id, quote=True)}"'
    if title:
        aside_attrs += f' title="{escape(title, quote=True)}"'

    return f"<aside{aside_attrs}>\n<pre>\n{filtered}</pre>\n</aside>"


def render_snippet_group(group_name: str, snippets_dir: Path) -> str:
    groups_dir = snippets_dir / "groups"
    group_path = groups_dir / f"{group_name}.yaml"

    if not group_path.exists():
        raise FileNotFoundError(f"Snippet group not found: {group_path}")

    with group_path.open(encoding="utf-8") as f:
        group = yaml.safe_load(f)

    title = group.get("title", "")
    tabs = group.get("tabs", [])
    tab_group_id = f"snippetTab_{group_name}"

    lines: list[str] = ['<aside class="example ds-selector-tabs">']

    if title:
        lines.append('  <div class="marker">')
        lines.append(f'    <span class="example-title">{escape(title)}</span>')
        lines.append("  </div>")

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

    for tab in tabs:
        _data, tab_meta = load_snippet(tab["snippet"], snippets_dir)
        filtered = _process_hide_ranges(tab_meta["_raw_jsonc"]).strip()
        tab_class = tab["snippet"].replace("-", "_")
        selected = " selected" if tab.get("selected") else ""
        lines.append(
            f'  <pre class="{tab_class} {tab_group_id}{selected} json">'
        )
        lines.append(filtered)
        lines.append("  </pre>")

    lines.append("</aside>")
    return "\n".join(lines)

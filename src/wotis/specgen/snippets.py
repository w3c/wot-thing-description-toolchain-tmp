from __future__ import annotations

import json
import logging
from html import escape
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft7Validator, ValidationError


def load_snippet(name: str, snippets_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    json_path = snippets_dir / f"{name}.json"
    meta_path = snippets_dir / f"{name}.meta.yaml"

    if not json_path.exists():
        raise FileNotFoundError(f"Snippet file not found: {json_path}")

    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)

    meta: dict[str, Any] = {}
    if meta_path.exists():
        with meta_path.open(encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}

    return data, meta


def validate_all_snippets(snippets_dir: Path, schema_path: Path) -> list[str]:
    if not snippets_dir.exists():
        return []

    with schema_path.open(encoding="utf-8") as f:
        raw = json.load(f)
        schema = json.loads(raw) if isinstance(raw, str) else raw

    validator = Draft7Validator(schema)
    errors: list[str] = []

    for json_file in sorted(snippets_dir.glob("*.json")):
        with json_file.open(encoding="utf-8") as f:
            try:
                instance = json.load(f)
            except json.JSONDecodeError as e:
                errors.append(f"{json_file.name}: invalid JSON — {e}")
                continue

        if isinstance(instance, dict) and instance.get("@type") == "tm:ThingModel":
            logging.debug("Skipping ThingModel: %s", json_file.name)
            continue

        for error in validator.iter_errors(instance):
            path = ".".join(str(p) for p in error.absolute_path) or "(root)"
            errors.append(f"{json_file.name}: {path} — {error.message}")

    return errors


def _redact(data: Any, redact_keys: set[str]) -> Any:
    if isinstance(data, dict):
        return {
            k: _redact_placeholder(v) if k in redact_keys else _redact(v, redact_keys)
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [_redact(item, redact_keys) for item in data]
    return data


def _redact_placeholder(value: Any) -> str:
    if isinstance(value, list):
        return "[...]"
    if isinstance(value, dict):
        return "{...}"
    return "..."


class _RedactEncoder(json.JSONEncoder):
    def encode(self, o: Any) -> str:
        return self._strip_quotes(super().encode(o))

    def iterencode(self, o: Any, _one_shot: bool = False) -> Any:
        for chunk in super().iterencode(o, _one_shot):
            yield self._strip_quotes(chunk)

    @staticmethod
    def _strip_quotes(s: str) -> str:
        for placeholder in ('"[...]"', '"{...}"', '"..."'):
            s = s.replace(placeholder, placeholder[1:-1])
        return s


def _filter_json(
    data: dict[str, Any],
    meta: dict[str, Any],
) -> str:
    indent = meta.get("indent", 4)
    ellipsis_marker = meta.get("ellipsis", "// ...")
    show_keys = meta.get("show_keys")
    hide_keys = meta.get("hide_keys")
    redact_keys = set(meta.get("redact_keys", []))

    if redact_keys:
        data = _redact(data, redact_keys)

    encoder_cls = _RedactEncoder if redact_keys else None

    if not show_keys and not hide_keys:
        return json.dumps(data, indent=indent, ensure_ascii=False, cls=encoder_cls)

    if not isinstance(data, dict):
        return json.dumps(data, indent=indent, ensure_ascii=False, cls=encoder_cls)

    all_keys = list(data.keys())

    if show_keys:
        visible = set(show_keys)
    elif hide_keys:
        visible = set(all_keys) - set(hide_keys)
    else:
        visible = set(all_keys)

    lines: list[str] = ["{"]
    pad = " " * indent
    filtered_entries: list[tuple[str, Any]] = []
    had_omission = False

    for key in all_keys:
        if key in visible:
            if had_omission:
                filtered_entries.append((None, ellipsis_marker))
                had_omission = False
            filtered_entries.append((key, data[key]))
        else:
            had_omission = True

    if had_omission:
        filtered_entries.append((None, ellipsis_marker))

    for i, (key, value) in enumerate(filtered_entries):
        is_last = i == len(filtered_entries) - 1

        if key is None:
            lines.append(f"{pad}{value}")
        else:
            formatted_value = json.dumps(value, indent=indent, ensure_ascii=False, cls=encoder_cls)
            if "\n" in formatted_value:
                indented = formatted_value.replace("\n", f"\n{pad}")
                entry = f"{pad}{json.dumps(key)}: {indented}"
            else:
                entry = f"{pad}{json.dumps(key)}: {formatted_value}"
            if not is_last:
                entry += ","
            lines.append(entry)

    lines.append("}")
    return "\n".join(lines)


def render_snippet(name: str, snippets_dir: Path) -> str:
    data, meta = load_snippet(name, snippets_dir)
    filtered = _filter_json(data, meta)

    snippet_id = meta.get("id", "")
    title = meta.get("title", "")
    layout = meta.get("layout", "aside")

    if layout == "pre":
        attrs = f' class="example"'
        if title:
            attrs += f' title="{escape(title, quote=True)}"'
        if snippet_id:
            attrs += f' id="{escape(snippet_id, quote=True)}"'
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
        data, meta = load_snippet(tab["snippet"], snippets_dir)
        filtered = _filter_json(data, meta)
        tab_class = tab["snippet"].replace("-", "_")
        selected = " selected" if tab.get("selected") else ""
        lines.append(
            f'  <pre class="{tab_class} {tab_group_id}{selected} json">'
        )
        lines.append(filtered)
        lines.append("  </pre>")

    lines.append("</aside>")
    return "\n".join(lines)

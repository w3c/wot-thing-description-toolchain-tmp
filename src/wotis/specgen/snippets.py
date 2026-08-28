from __future__ import annotations

import json
import logging
from html import escape
from pathlib import Path
from typing import Any

import jsonfold
from dataclasses import replace as _replace
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from jsonschema import Draft7Validator


logger = logging.getLogger(__name__)

_FOLD_CONFIG = _replace(
    jsonfold.JSONFoldConfig.NONE,
    fold_array_items=10,
    fold_obj_items=5,
    fold_nesting=2,
)

_manifest_cache: dict[str, dict] = {}


def _load_manifest(snippets_dir: Path) -> dict:
    key = str(snippets_dir)
    if key not in _manifest_cache:
        manifest_path = snippets_dir / "_snippets.yaml"
        _manifest_cache[key] = yaml.safe_load(
            manifest_path.read_text(encoding="utf-8")
        )
    return _manifest_cache[key]


def _get_snippet_meta(snippets_dir: Path, name: str) -> dict[str, Any]:
    manifest = _load_manifest(snippets_dir)
    snippets = manifest.get("snippets", {})
    if name not in snippets:
        raise KeyError(f"Snippet '{name}' not found in manifest")
    return snippets[name]


def _get_group_meta(snippets_dir: Path, group_name: str) -> dict[str, Any]:
    manifest = _load_manifest(snippets_dir)
    groups = manifest.get("groups", {})
    if group_name not in groups:
        raise KeyError(f"Group '{group_name}' not found in manifest")
    return groups[group_name]


def _read_snippet_json(snippets_dir: Path, name: str) -> tuple[str, Any]:
    """Read snippet file, return (raw_text, parsed_json_or_None)."""
    path = snippets_dir / f"{name}.json"
    raw = path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None
    return raw, parsed


def _segs_match(path_segs: list[str], pattern_segs: list[str]) -> bool:
    if len(path_segs) != len(pattern_segs):
        return False
    return all(p == "*" or p == s for s, p in zip(path_segs, pattern_segs))


def _segs_ancestor(path_segs: list[str], pattern_segs: list[str]) -> bool:
    if len(path_segs) >= len(pattern_segs):
        return False
    return all(p == "*" or p == s for s, p in zip(path_segs, pattern_segs))


def _key_visibility(path: str, paths: list[str], mode: str) -> str:
    ps = path.split(".")
    split_paths = [p.split(".") for p in paths]

    matches = any(_segs_match(ps, sp) for sp in split_paths)
    collapsed = any(_segs_match(ps + ["*"], sp) for sp in split_paths)
    ancestor = any(_segs_ancestor(ps, sp) for sp in split_paths)

    if mode == "hide":
        if matches:
            return "hidden"
        if collapsed:
            return "collapsed"
        if ancestor:
            return "partial"
        return "visible"
    if matches:
        return "visible"
    if ancestor:
        return "partial"
    return "hidden"


def _filtered_serialize(
    obj: Any,
    paths: list[str],
    mode: str,
    current_path: str = "",
    indent: int = 0,
) -> str:
    pad = " " * (indent * 4)
    inner_pad = " " * ((indent + 1) * 4)

    if isinstance(obj, dict):
        if not obj:
            return "{}"

        parts: list[str | None] = []
        items = list(obj.items())

        for key, value in items:
            path = f"{current_path}.{key}" if current_path else key
            vis = _key_visibility(path, paths, mode)

            if vis == "hidden":
                parts.append(None)
            elif vis == "collapsed":
                if isinstance(value, dict):
                    parts.append(f'{inner_pad}"{key}": ' + "{// ...}")
                elif isinstance(value, list):
                    parts.append(f'{inner_pad}"{key}": ' + "[// ...]")
                else:
                    parts.append(f'{inner_pad}"{key}": ' + "// ...")
            elif vis == "partial":
                child_str = _filtered_serialize(value, paths, mode, path, indent + 1)
                parts.append(f'{inner_pad}"{key}": {child_str}')
            else:
                val_str = _json_fold(value, indent + 1)
                parts.append(f'{inner_pad}"{key}": {val_str}')

        collapsed: list[str] = []
        for part in parts:
            if part is None:
                if not collapsed or collapsed[-1] != "HIDDEN":
                    collapsed.append("HIDDEN")
            else:
                collapsed.append(part)

        if not any(c != "HIDDEN" for c in collapsed):
            return "{// ...}"

        visible = [c for c in collapsed if c != "HIDDEN"]
        lines = ["{"]
        vi = 0
        for c in collapsed:
            if c == "HIDDEN":
                lines.append(f"{inner_pad}// ...")
            else:
                vi += 1
                comma = "," if vi < len(visible) else ""
                lines.append(c + comma)
        lines.append(f"{pad}" + "}")
        return "\n".join(lines)

    if isinstance(obj, list) and mode == "show":
        if not obj:
            return "[]"
        entries = []
        has_hidden = False
        for item in obj:
            if isinstance(item, dict):
                child_str = _filtered_serialize(item, paths, mode, current_path, indent + 1)
                if child_str == "{// ...}":
                    has_hidden = True
                else:
                    entries.append(f"{inner_pad}{child_str}")
            else:
                entries.append(f"{inner_pad}{json.dumps(item)}")

        lines = ["["]
        for i, entry in enumerate(entries):
            comma = "," if i < len(entries) - 1 or has_hidden else ""
            lines.append(entry + comma)
        if has_hidden:
            lines.append(f"{inner_pad}// ...")
        lines.append(f"{pad}]")
        return "\n".join(lines)

    return _json_fold(obj, indent)


def _json_fold(obj: Any, indent: int = 0) -> str:
    raw = jsonfold.dumps(obj, indent=4, compact=_FOLD_CONFIG, ensure_ascii=False).rstrip("\n")
    if "\n" not in raw:
        return raw
    lines = raw.split("\n")
    pad = " " * (indent * 4)
    return lines[0] + "\n" + "\n".join(pad + l for l in lines[1:])


def _render_filtered_json(parsed_json: Any, raw_text: str, meta: dict[str, Any]) -> str:
    hide_paths = meta.get("hide_paths")
    show_paths = meta.get("show_paths")

    if parsed_json is None:
        return raw_text.strip()

    if hide_paths:
        return _filtered_serialize(parsed_json, hide_paths, "hide")
    if show_paths:
        return _filtered_serialize(parsed_json, show_paths, "show")

    return jsonfold.dumps(parsed_json, indent=4, compact=_FOLD_CONFIG, ensure_ascii=False).rstrip("\n")


def _build_element_attrs(snippet_id: str, title: str) -> str:
    attrs = ' class="example"'
    if snippet_id:
        attrs += f' id="{escape(snippet_id, quote=True)}"'
    if title:
        attrs += f' title="{escape(title, quote=True)}"'
    return attrs


def _load_schema(schema_path: Path) -> Draft7Validator:
    raw = json.loads(schema_path.read_text(encoding="utf-8"))
    schema = json.loads(raw) if isinstance(raw, str) else raw
    return Draft7Validator(schema)


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
        schema_path = "/".join(str(p) for p in error.absolute_schema_path)
        errors.append(f"{filename}: {path} — {error.message} [schema: {schema_path}]")


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

    manifest = _load_manifest(snippets_dir)
    for name, meta in manifest.get("snippets", {}).items():
        if meta.get("validate") is False:
            logger.debug("Skipping validation (validate: false): %s", name)
            continue

        json_path = snippets_dir / f"{name}.json"
        if not json_path.exists():
            errors.append(f"{name}.json: file not found")
            continue

        try:
            parsed = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append(f"{name}.json: invalid JSON")
            continue

        _collect_schema_errors(parsed, f"{name}.json", td_validator, tm_validator, errors)

    return errors


def render_snippet(name: str, snippets_dir: Path) -> str:
    meta = _get_snippet_meta(snippets_dir, name)
    raw_text, parsed_json = _read_snippet_json(snippets_dir, name)
    filtered = _render_filtered_json(parsed_json, raw_text, meta)

    snippet_id = meta.get("id", "")
    title = meta.get("title", "")
    layout = meta.get("layout", "aside")

    if layout == "pre":
        attrs = ' class="example json"'
        if snippet_id:
            attrs += f' id="{escape(snippet_id, quote=True)}"'
        if title:
            attrs += f' title="{escape(title, quote=True)}"'
        return f"<pre{attrs}>\n{filtered}</pre>"

    if not snippet_id:
        raise ValueError(f"Snippet '{name}' missing required 'id' in manifest")
    attrs = _build_element_attrs(snippet_id, title)
    return f"<aside{attrs}>\n<pre>\n{filtered}</pre>\n</aside>"


def render_snippet_group(group_name: str, snippets_dir: Path, templates_dir: Path) -> str:
    group = _get_group_meta(snippets_dir, group_name)

    if group.get("layout") == "with-default":
        return _render_with_default(group, snippets_dir, templates_dir)

    title = group.get("title", "")
    tabs = group.get("tabs", [])
    tab_group_id = f"example-tabs-{group_name}"

    lines: list[str] = ['<aside class="example ds-selector-tabs">']
    if title:
        _append_group_title(lines, title)
    _append_tab_selectors(lines, tabs, tab_group_id)
    _append_tab_contents(lines, tabs, tab_group_id, snippets_dir)
    lines.append("</aside>")
    return "\n".join(lines)


def _get_snippet_jinja_env(templates_dir: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["jinja2", "html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _render_with_default(group: dict[str, Any], snippets_dir: Path, templates_dir: Path) -> str:
    compact_raw, compact_parsed = _read_snippet_json(snippets_dir, group["compact"])
    expanded_raw, expanded_parsed = _read_snippet_json(snippets_dir, group["expanded"])

    compact_meta = _get_snippet_meta(snippets_dir, group["compact"])
    expanded_meta = _get_snippet_meta(snippets_dir, group["expanded"])

    compact_body = _render_filtered_json(compact_parsed, compact_raw, compact_meta)
    expanded_body = _render_filtered_json(expanded_parsed, expanded_raw, expanded_meta)

    env = _get_snippet_jinja_env(templates_dir)
    tpl = env.get_template("snippet_with_default.jinja2")
    return tpl.render(
        id=group.get("id", ""),
        title=group.get("title", ""),
        toggle_label=group.get("toggle_label", "with Default Values"),
        compact_body=compact_body,
        expanded_body=expanded_body,
    )


def _append_group_title(lines: list[str], title: str) -> None:
    lines.append('  <div class="marker">')
    lines.append(f'    <span class="example-title">{escape(title)}</span>')
    lines.append("  </div>")


def _append_tab_selectors(lines: list[str], tabs: list[dict[str, Any]], tab_group_id: str) -> None:
    lines.append('  <div class="selectors">')
    for tab in tabs:
        label = escape(tab.get("label", tab["snippet"]))
        tab_class = tab.get("tab_class", tab["snippet"].replace("-", "_"))
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
        raw, parsed = _read_snippet_json(snippets_dir, tab["snippet"])
        meta = _get_snippet_meta(snippets_dir, tab["snippet"])
        filtered = _render_filtered_json(parsed, raw, meta)
        tab_class = tab.get("tab_class", tab["snippet"].replace("-", "_"))
        selected = " selected" if tab.get("selected") else ""
        lines.append(
            f'  <pre class="{tab_class} {tab_group_id}{selected} json">'
        )
        lines.append(filtered)
        lines.append("  </pre>")

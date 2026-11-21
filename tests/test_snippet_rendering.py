"""Snippet groups render to well-formed example markup."""

from __future__ import annotations

from pathlib import Path

from wot_toolchain.specgen.snippets import render_snippet_group


def _with_default_manifest(group: dict[str, str]) -> dict[str, object]:
    return {
        "snippets": {"short": {"validate": False}, "long": {"validate": False}},
        "groups": {"pair": {"layout": "with-default", "compact": "short", "expanded": "long", **group}},
    }


def _write_snippets(snippets_dir: Path) -> None:
    (snippets_dir / "short.json").write_text('{"a": 1}', encoding="utf-8")
    (snippets_dir / "long.json").write_text('{"a": 1, "b": 2}', encoding="utf-8")


def test_with_default_group_id_is_a_quoted_attribute(tmp_path: Path) -> None:
    _write_snippets(tmp_path)
    html = render_snippet_group("pair", tmp_path, _with_default_manifest({"id": "example-pair"}))
    assert '<aside class="example with-default" id="example-pair">' in html


def test_with_default_group_without_id_has_no_id_attribute(tmp_path: Path) -> None:
    _write_snippets(tmp_path)
    html = render_snippet_group("pair", tmp_path, _with_default_manifest({}))
    assert '<aside class="example with-default">' in html

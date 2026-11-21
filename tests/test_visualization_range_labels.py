"""The class diagram names slot ranges with the labels it is given, not with labels of its own."""

from __future__ import annotations

from pathlib import Path

from wot_toolchain.generators.visualization import _build_dot_from_schema_view
from wot_toolchain.schema_utils import load_schema_view

_SCHEMA = """\
id: https://example.org/demo
name: demo
prefixes:
  linkml: https://w3id.org/linkml/
  demo: https://example.org/demo#
default_prefix: demo
imports:
  - linkml:types
classes:
  Widget:
    attributes:
      href:
        range: uri
      created:
        range: datetime
"""


def _dot(tmp_path: Path, range_labels: dict[str, str]) -> str:
    schema = tmp_path / "demo.yaml"
    schema.write_text(_SCHEMA, encoding="utf-8")
    sv = load_schema_view(schema, merge_imports=True)
    return _build_dot_from_schema_view(sv, local_classes={"Widget"}, range_labels=range_labels)


def test_range_is_shown_with_the_given_label(tmp_path: Path) -> None:
    dot = _dot(tmp_path, {"uri": "link target"})

    assert ">link target</FONT>" in dot
    assert ">uri</FONT>" not in dot


def test_range_without_a_label_is_shown_under_its_own_name(tmp_path: Path) -> None:
    dot = _dot(tmp_path, {"uri": "link target"})

    assert ">datetime</FONT>" in dot

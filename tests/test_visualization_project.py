"""The visualization generator takes its diagrams from the manifest modules and fails loudly."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import pytest

from wot_toolchain.config import Module
from wot_toolchain.errors import ExternalToolError, SchemaError
from wot_toolchain.generators.visualization import generate_visualizations

_SCHEMA = """\
id: https://example.org/demo
name: demo
prefixes:
  linkml: https://w3id.org/linkml/
  demo: https://example.org/demo#
default_prefix: demo
default_range: string
imports:
  - linkml:types
classes:
  Widget:
    attributes:
      label:
"""

requires_dot = pytest.mark.skipif(shutil.which("dot") is None, reason="Graphviz 'dot' is not installed")


def _module(tmp_path: Path, diagram: str | None, text: str = _SCHEMA) -> Module:
    schema = tmp_path / "demo.yaml"
    schema.write_text(text, encoding="utf-8")
    return Module(schema=schema, prefix="demo", ontology=None, context=None, diagram=diagram)


def _fake_dot(bin_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bin_dir.mkdir()
    script = bin_dir / "dot"
    script.write_text("#!/bin/sh\necho 'Error: syntax error in line 1' >&2\nexit 1\n", encoding="utf-8")
    script.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))


@requires_dot
def test_diagram_file_name_comes_from_the_module(tmp_path: Path) -> None:
    out = tmp_path / "out"

    generate_visualizations([_module(tmp_path, "widgets.svg")], out)

    assert (out / "widgets.svg").is_file()
    assert not (out / "td.svg").exists()


@requires_dot
def test_module_without_diagram_gets_none(tmp_path: Path) -> None:
    out = tmp_path / "out"

    generate_visualizations([_module(tmp_path, None)], out)

    assert not list(out.glob("*.svg"))


def test_missing_dot_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(ExternalToolError, match="dot"):
        generate_visualizations([_module(tmp_path, "widgets.svg")], tmp_path / "out")


def test_failing_dot_raises_with_stderr(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_dot(tmp_path / "bin", monkeypatch)
    with pytest.raises(ExternalToolError, match="syntax error in line 1"):
        generate_visualizations([_module(tmp_path, "widgets.svg")], tmp_path / "out")


@requires_dot
def test_unloadable_schema_raises_naming_the_file(tmp_path: Path) -> None:
    module = _module(tmp_path, "widgets.svg", text="classes: [unclosed\n")
    with pytest.raises(SchemaError, match="demo.yaml"):
        generate_visualizations([module], tmp_path / "out")


@requires_dot
def test_only_the_diagram_is_written(tmp_path: Path) -> None:
    out = tmp_path / "out"

    generate_visualizations([_module(tmp_path, "widgets.svg")], out)

    assert [path.name for path in out.iterdir()] == ["widgets.svg"]


_SCHEMA_WITH_UNDEFINED_SLOT = _SCHEMA + "    slots:\n      - elsewhere\n"


@requires_dot
def test_slot_defined_outside_the_module_is_reported(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    module = _module(tmp_path, "widgets.svg", text=_SCHEMA_WITH_UNDEFINED_SLOT)

    with caplog.at_level(logging.WARNING, logger="wot_toolchain.generators.visualization"):
        generate_visualizations([module], tmp_path / "out")

    assert "Widget.elsewhere" in caplog.text
    assert "demo.yaml" in caplog.text

"""The specification template marks each generated section with ``%section('<id>')%``, filled by section id."""

from __future__ import annotations

from pathlib import Path

import pytest

from wot_toolchain.errors import GenerationError
from wot_toolchain.specgen.respec import assemble


def write_template(tmp_path: Path, text: str) -> Path:
    template = tmp_path / "index.template.html"
    template.write_text(text, encoding="utf-8")
    return template


def test_sections_are_filled_by_id_regardless_of_fragment_order(tmp_path: Path) -> None:
    template = write_template(tmp_path, "<a>%section('sec-a')%</a><b>%section('sec-b')%</b>")
    out = tmp_path / "index.html"

    assemble(template, {"sec-b": "B", "sec-a": "A"}, out_path=out)

    assert out.read_text(encoding="utf-8") == "<a>A</a><b>B</b>"


def test_marker_without_config_section_raises_naming_id_and_template(tmp_path: Path) -> None:
    template = write_template(tmp_path, "%section('sec-a')%%section('sec-stray')%")

    with pytest.raises(GenerationError, match=r"sec-stray") as error:
        assemble(template, {"sec-a": "A"}, out_path=tmp_path / "index.html")

    assert str(template) in str(error.value)


def test_config_section_without_marker_raises_naming_id_and_template(tmp_path: Path) -> None:
    template = write_template(tmp_path, "%section('sec-a')%")

    with pytest.raises(GenerationError, match=r"sec-unused") as error:
        assemble(template, {"sec-a": "A", "sec-unused": "U"}, out_path=tmp_path / "index.html")

    assert str(template) in str(error.value)


def test_template_content_is_used_instead_of_reading_the_file(tmp_path: Path) -> None:
    out = tmp_path / "index.html"

    assemble(tmp_path / "unread.html", {"sec-a": "A"}, out_path=out, template_content="[%section('sec-a')%]")

    assert out.read_text(encoding="utf-8") == "[A]"


def test_nothing_is_written_when_markers_and_sections_disagree(tmp_path: Path) -> None:
    template = write_template(tmp_path, "%section('sec-a')%")
    out = tmp_path / "index.html"

    with pytest.raises(GenerationError):
        assemble(template, {"sec-b": "B"}, out_path=out)

    assert not out.exists()

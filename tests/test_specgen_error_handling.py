"""Specgen failures surface as typed errors; only expected, harmless exceptions are tolerated."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from linkml_runtime.linkml_model.meta import ClassDefinition, SlotDefinition
from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.errors import GenerationError, SchemaError
from wot_toolchain.specgen.assertions import (
    extract_all_table_assertions,
    extract_inline_assertions,
    make_slot_assertion_id,
)
from wot_toolchain.specgen.bikeshed_processor import process_fragments
from wot_toolchain.specgen.respec import assemble
from wot_toolchain.specgen.tables import collect_slot_rows, get_assignment

_SCHEMA_HEADER = """\
id: https://example.org/mod
name: mod
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
default_range: string
"""


def _write_schema(tmp_path: Path, body: str) -> Path:
    schema = tmp_path / "mod.yaml"
    schema.write_text(_SCHEMA_HEADER + body, encoding="utf-8")
    return schema


class _UnconvertibleNumber:
    def __float__(self) -> float:
        raise RuntimeError("cannot convert")


def test_get_assignment_treats_non_numeric_minimum_value_as_optional() -> None:
    slot = SlotDefinition(name="since", minimum_value="2020-01-01")
    assert get_assignment("since", ClassDefinition(name="C"), slot) == "optional"


def test_get_assignment_treats_mapping_minimum_value_as_optional() -> None:
    slot = SlotDefinition(name="size", minimum_value={"unit": "m"})
    assert get_assignment("size", ClassDefinition(name="C"), slot) == "optional"


def test_get_assignment_propagates_unexpected_minimum_value_errors() -> None:
    slot = SlotDefinition(name="size", minimum_value=_UnconvertibleNumber())
    with pytest.raises(RuntimeError, match="cannot convert"):
        get_assignment("size", ClassDefinition(name="C"), slot)


def test_table_assertions_raise_schema_error_for_invalid_schema(tmp_path: Path) -> None:
    schema = tmp_path / "broken.yaml"
    schema.write_text("classes: [unclosed\n", encoding="utf-8")
    with pytest.raises(SchemaError, match="broken.yaml"):
        extract_all_table_assertions({"sec": schema}, {}, "sen")


def test_inline_assertions_raise_schema_error_for_invalid_schema(tmp_path: Path) -> None:
    schema = tmp_path / "broken.yaml"
    schema.write_text("classes: [unclosed\n", encoding="utf-8")
    with pytest.raises(SchemaError, match="broken.yaml"):
        extract_inline_assertions({"sec": schema}, {})


def test_table_assertion_for_slot_undefined_in_module_has_empty_text(tmp_path: Path) -> None:
    schema = _write_schema(tmp_path, "classes:\n  C:\n    slots: [defined_by_importer]\n")
    [assertion] = extract_all_table_assertions({"sec": schema}, {}, "sen")
    assert assertion.id == "sen-vocab-defined_by_importer--C"
    assert assertion.text == ""


def test_table_assertions_propagate_slot_induction_failures(tmp_path: Path) -> None:
    schema = _write_schema(
        tmp_path,
        "slots:\n"
        "  x:\n"
        '    minimum_value: "a"\n'
        "classes:\n"
        "  C:\n"
        "    slots: [x]\n"
        "    slot_usage:\n"
        "      x:\n"
        "        minimum_value: 1\n",
    )
    with pytest.raises(TypeError):
        extract_all_table_assertions({"sec": schema}, {}, "sen")


def test_assemble_missing_template_raises_generation_error(tmp_path: Path) -> None:
    template = tmp_path / "missing.template.html"
    with pytest.raises(GenerationError, match="missing.template.html"):
        assemble(template, "<p>x</p>", out_path=tmp_path / "out.html", placeholder="%s")


def test_assemble_warns_about_unreplaced_placeholders_naming_the_files(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    template = tmp_path / "index.template.html"
    template.write_text("<p>%s</p><p>%s</p><p>%s</p>", encoding="utf-8")
    out = tmp_path / "index.html"
    with caplog.at_level(logging.WARNING):
        assemble(template, "first", out_path=out, placeholder="%s")
    [record] = [r for r in caplog.records if r.levelno == logging.WARNING]
    message = record.getMessage()
    assert "2" in message
    assert str(template) in message
    assert str(out) in message
    assert not message.startswith("Warning")
    assert out.read_text(encoding="utf-8") == "<p>first</p><p>%s</p><p>%s</p>"


def test_process_fragments_length_mismatch_raises_generation_error(tmp_path: Path) -> None:
    with pytest.raises(GenerationError, match=r"2 section ids but 1 fragment"):
        process_fragments(["a", "b"], ["<p>x</p>"], tmp_path / "glossary.yaml")


def test_slot_rows_display_unaliased_at_name_slot_under_its_own_name(tmp_path: Path) -> None:
    schema = _write_schema(tmp_path, 'slots:\n  "@name": {}\nclasses:\n  Sensor:\n    slots: ["@name"]\n')
    [row] = collect_slot_rows(SchemaView(str(schema)), "Sensor", lambda text: text)
    assert row["slot_name"] == "@name"


def test_slot_assertion_id_uses_configured_vocab_id_prefix() -> None:
    assert make_slot_assertion_id("sen", "Sensor", "@type") == "sen-vocab-at-type--Sensor"


def test_slot_rows_carry_assertion_ids_with_configured_vocab_id_prefix(tmp_path: Path) -> None:
    schema = _write_schema(tmp_path, "slots:\n  unit: {}\nclasses:\n  Sensor:\n    slots: [unit]\n")
    [row] = collect_slot_rows(SchemaView(str(schema)), "Sensor", lambda text: text, "sen")
    assert row["assertion_id"] == "sen-vocab-unit--Sensor"


def test_slot_rows_display_ranges_under_their_configured_labels(tmp_path: Path) -> None:
    schema = _write_schema(
        tmp_path,
        "slots:\n"
        "  href:\n"
        "    range: uri\n"
        "  created:\n"
        "    range: datetime\n"
        "classes:\n"
        "  Sensor:\n"
        "    slots: [href, created]\n",
    )
    rows = collect_slot_rows(SchemaView(str(schema)), "Sensor", lambda text: text, range_labels={"uri": "anyURI"})
    assert [row["range_text"] for row in rows] == [
        '<a href="https://www.w3.org/TR/2012/REC-xmlschema11-2-20120405/#anyURI"><code>anyURI</code></a>',
        '<a href="https://www.w3.org/TR/2012/REC-xmlschema11-2-20120405/#datetime"><code>datetime</code></a>',
    ]


def test_slot_rows_show_labelled_any_range_as_plain_text(tmp_path: Path) -> None:
    schema = _write_schema(
        tmp_path,
        "slots:\n"
        "  value:\n"
        "    range: Any\n"
        "  values:\n"
        "    range: Any\n"
        "    multivalued: true\n"
        "  choice:\n"
        "    exactly_one_of:\n"
        "      - range: Any\n"
        "      - range: string\n"
        "classes:\n"
        "  Any:\n"
        "    class_uri: linkml:Any\n"
        "  Sensor:\n"
        "    slots: [value, values, choice]\n",
    )
    rows = collect_slot_rows(SchemaView(str(schema)), "Sensor", lambda text: text, range_labels={"Any": "anything"})
    assert [row["range_text"] for row in rows] == [
        "anything",
        "<a>Array</a> of anything",
        'anything or <a href="https://www.w3.org/TR/2012/REC-xmlschema11-2-20120405/#string"><code>string</code></a>',
    ]


_DEFAULTED_SLOT_SCHEMA = (
    "slots:\n  safe:\n    annotations:\n      spec_default: true\nclasses:\n  Sensor:\n    slots: [safe]\n"
)


def test_slot_rows_link_default_assignment_to_configured_anchor(tmp_path: Path) -> None:
    schema = _write_schema(tmp_path, _DEFAULTED_SLOT_SCHEMA)
    [row] = collect_slot_rows(
        SchemaView(str(schema)), "Sensor", lambda text: text, default_values_anchor="sec-defaults"
    )
    assert row["assignment"] == '<a href="#sec-defaults">with default</a>'


def test_slot_rows_show_default_assignment_as_plain_text_without_anchor(tmp_path: Path) -> None:
    schema = _write_schema(tmp_path, _DEFAULTED_SLOT_SCHEMA)
    [row] = collect_slot_rows(SchemaView(str(schema)), "Sensor", lambda text: text)
    assert row["assignment"] == "with default"

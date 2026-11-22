import dataclasses
from pathlib import Path

import pytest
import yaml
from linkml_runtime.linkml_model.meta import SchemaDefinition
from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.artifacts.owl.pre_passes import OWL_PRE_PASSES, OwlPreContext
from wot_toolchain.artifacts.owl.preprocess import preprocess_for_gen_owl
from wot_toolchain.artifacts.passes import Pass, PassKind
from wot_toolchain.errors import SchemaError

SCHEMA = """\
id: https://example.org/mini
name: mini
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/
default_prefix: ex
default_range: string
imports:
  - linkml:types
slots:
  title:
    slot_uri: ex:hasTitle
  "@type":
    slot_uri: ex:type
  note: {}
classes:
  Thing:
    class_uri: ex:Thing
    slots: [title, "@type", note]
  Helper:
    slots: [title]
"""

ORDER_BEFORE_THE_MOVE = [
    "rename_slots_to_uri_local_names",
    "strip_no_uri_classes",
    "strip_foreign_mixins",
    "promote_attributes",
    "strip_no_uri_original_slots",
    "strip_non_ontological_enums",
    "fix_enum_pv_labels",
    "clear_constraints",
    "strip_dangling_slot_refs",
]

UPSTREAM_GAP_PASSES = {"promote_attributes"}


@pytest.fixture
def schema_path(tmp_path: Path) -> Path:
    path = tmp_path / "mini.yaml"
    path.write_text(SCHEMA, encoding="utf-8")
    return path


def _pass(name: str) -> Pass:
    return {p.name: p for p in OWL_PRE_PASSES}[name]


def _context(view: SchemaView, **overrides: object) -> OwlPreContext:
    fields: dict[str, object] = {
        "view": view,
        "namespace": "https://example.org/",
        "no_uri_classes": frozenset(),
        "original_no_uri_slots": frozenset(),
    }
    return OwlPreContext(**(fields | overrides))  # type: ignore[arg-type]


def _schema(view: SchemaView) -> SchemaDefinition:
    schema = view.schema
    assert isinstance(schema, SchemaDefinition)
    return schema


def test_pass_names_are_unique_and_every_pass_has_a_reason() -> None:
    names = [p.name for p in OWL_PRE_PASSES]
    assert len(names) == len(set(names))
    assert all(p.reason.strip() for p in OWL_PRE_PASSES)


def test_pass_order_is_the_order_of_preprocess_for_gen_owl_before_the_move() -> None:
    assert [p.name for p in OWL_PRE_PASSES] == ORDER_BEFORE_THE_MOVE


def test_promote_attributes_is_upstream_gap_and_every_other_pass_is_wot_shaping() -> None:
    kinds = {p.name: p.kind for p in OWL_PRE_PASSES}
    assert {name for name, kind in kinds.items() if kind is PassKind.UPSTREAM_GAP} == UPSTREAM_GAP_PASSES
    assert {kind for name, kind in kinds.items() if name not in UPSTREAM_GAP_PASSES} == {PassKind.WOT_SHAPING}


def test_context_is_immutable(schema_path: Path) -> None:
    context = _context(SchemaView(str(schema_path)))
    with pytest.raises(dataclasses.FrozenInstanceError):
        context.namespace = "https://example.org/other/"  # type: ignore[misc]


def test_rename_pass_renames_a_slot_to_the_local_name_of_its_slot_uri(schema_path: Path) -> None:
    view = SchemaView(str(schema_path))
    schema = _schema(view)

    _pass("rename_slots_to_uri_local_names").apply(schema, _context(view))

    assert "hasTitle" in schema.slots
    assert "title" not in schema.slots
    assert "hasTitle" in schema.classes["Thing"].slots


def test_no_uri_class_pass_removes_the_classes_named_by_the_context(schema_path: Path) -> None:
    view = SchemaView(str(schema_path))
    schema = _schema(view)

    _pass("strip_no_uri_classes").apply(schema, _context(view, no_uri_classes=frozenset({"Helper"})))

    assert set(schema.classes) == {"Thing"}


def test_no_uri_slot_pass_removes_the_slots_named_by_the_context(schema_path: Path) -> None:
    view = SchemaView(str(schema_path))
    schema = _schema(view)

    _pass("strip_no_uri_original_slots").apply(schema, _context(view, original_no_uri_slots=frozenset({"note"})))

    assert "note" not in schema.slots
    assert "note" not in schema.classes["Thing"].slots


def test_preprocess_for_gen_owl_runs_the_passes_and_returns_yaml(schema_path: Path) -> None:
    result = yaml.safe_load(preprocess_for_gen_owl(str(schema_path)))

    assert set(result["slots"]) == {"hasTitle", "type"}
    assert set(result["classes"]) == {"Thing"}
    assert result["classes"]["Thing"]["slots"] == ["hasTitle", "type"]


def test_schema_error_of_a_pass_reaches_the_caller_unchanged(schema_path: Path) -> None:
    schema_path.write_text(SCHEMA.replace("ex:hasTitle", "nope:hasTitle"), encoding="utf-8")
    view = SchemaView(str(schema_path))
    view.expand_curie = _raise_value_error  # type: ignore[method-assign]

    with pytest.raises(SchemaError, match="cannot expand slot_uri"):
        _pass("rename_slots_to_uri_local_names").apply(_schema(view), _context(view))


def _raise_value_error(_curie: str) -> str:
    raise ValueError("unresolvable prefix map")

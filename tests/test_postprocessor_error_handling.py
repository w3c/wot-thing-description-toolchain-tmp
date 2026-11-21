"""Invalid schema content reaching the postprocessors raises a typed error that names the offending element."""

from __future__ import annotations

import json

import pytest
from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.errors import SchemaError
from wot_toolchain.postprocessors.jsonld_context_postprocessor import post_process_jsonld_context
from wot_toolchain.postprocessors.jsonschema_postprocessor import post_process_jsonschema
from wot_toolchain.schema_utils import default_prefix, get_schema, resolve_prefix_namespace

SCHEMA_HEADER = """
id: https://example.org/probe
name: probe
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/ex#
  a: https://example.org/a#
  b: https://example.org/b#
default_prefix: ex
imports: [linkml:types]
"""


def _schema_view(body: str) -> SchemaView:
    return SchemaView(SCHEMA_HEADER + body)


def _jsonld_context(sv: SchemaView, extra_root_terms: tuple[str, ...] = ()) -> str:
    serialized = ContextGenerator(sv.schema, mergeimports=True, fix_multivalue_containers=True).serialize()
    return post_process_jsonld_context(sv, serialized, extra_root_terms=extra_root_terms)


def test_undeclared_prefix_raises_schema_error_naming_prefix_and_schema() -> None:
    sv = _schema_view("classes:\n  A: {}\n")
    with pytest.raises(SchemaError, match=r"'nope'.*'probe'"):
        resolve_prefix_namespace(sv, "nope")


def test_declared_prefix_resolves_to_namespace() -> None:
    assert resolve_prefix_namespace(_schema_view("classes:\n  A: {}\n"), "a") == "https://example.org/a#"


def test_jsonld_context_annotation_with_undeclared_prefix_raises_schema_error() -> None:
    sv = _schema_view(
        """
slots:
  label:
    range: string
    annotations:
      jsonld_context: nope
classes:
  A:
    slots: [label]
"""
    )
    with pytest.raises(SchemaError, match=r"'label'.*'nope'"):
        _jsonld_context(sv)


def test_undeclared_class_uri_prefix_in_slot_range_raises_schema_error() -> None:
    sv = _schema_view(
        """
slots:
  zz_value: {range: string, slot_uri: "zz:value"}
  link: {range: Target, slot_uri: "ex:link"}
classes:
  Target:
    class_uri: "zz:Target"
    slots: [zz_value]
  Holder:
    slots: [link]
"""
    )
    with pytest.raises(SchemaError, match=r"'link'.*'Target'.*\['zz'\]"):
        _jsonld_context(sv)


def test_ambiguous_jsonld_context_raises_schema_error() -> None:
    sv = _schema_view(
        """
slots:
  a_value: {range: string, slot_uri: "a:value"}
  b_value: {range: string, slot_uri: "b:value"}
  link: {range: Target, slot_uri: "ex:link"}
classes:
  BMixin:
    mixin: true
    class_uri: "b:BMixin"
    slots: [b_value]
  Target:
    class_uri: "a:Target"
    mixins: [BMixin]
    slots: [a_value]
  Holder:
    slots: [link]
"""
    )
    with pytest.raises(SchemaError, match=r"'link'.*\['a', 'b'\]"):
        _jsonld_context(sv)


def test_string_map_check_reports_class_with_unresolvable_slot() -> None:
    sv = _schema_view("classes:\n  Broken:\n    slots: [missing]\n")
    raw = {
        "$defs": {
            "Broken": {"type": "object"},
            "Holder": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "object",
                        "additionalProperties": {"anyOf": [{"$ref": "#/$defs/Broken__identifier_optional"}]},
                    }
                },
            },
        }
    }
    with pytest.raises(SchemaError, match=r"'Broken'.*missing"):
        post_process_jsonschema(raw, sv)


def test_string_map_check_treats_unknown_def_as_not_a_string_map() -> None:
    sv = _schema_view("classes:\n  A: {}\n")
    raw = {
        "$defs": {
            "Synthetic": {"type": "object"},
            "Holder": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "object",
                        "additionalProperties": {"anyOf": [{"$ref": "#/$defs/Synthetic__identifier_optional"}]},
                    }
                },
            },
        }
    }
    processed = post_process_jsonschema(raw, sv)
    assert processed["$defs"]["Holder"]["properties"]["items"]["additionalProperties"] == {"$ref": "#/$defs/Synthetic"}


def test_identifier_slot_removal_reports_class_with_unresolvable_slot() -> None:
    sv = _schema_view("classes:\n  Broken:\n    slots: [missing]\n")
    # No __identifier_optional reference, so the string-map check never sees Broken: only identifier removal does.
    raw = {"$defs": {"Broken": {"type": "object", "properties": {"missing": {"type": "string"}}}}}
    with pytest.raises(SchemaError, match=r"'Broken'.*missing"):
        post_process_jsonschema(raw, sv)


def test_identifier_slot_removal_leaves_non_class_def_untouched() -> None:
    sv = _schema_view("classes:\n  A: {}\n")
    synthetic = {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}
    raw = {"$defs": {"Synthetic": synthetic}}
    processed = post_process_jsonschema(raw, sv)
    assert processed["$defs"]["Synthetic"] == synthetic


def test_get_schema_without_loaded_schema_raises_schema_error() -> None:
    sv = _schema_view("classes:\n  A: {}\n")
    sv.schema = None

    with pytest.raises(SchemaError, match="no schema loaded"):
        get_schema(sv)


def test_get_schema_returns_loaded_schema_definition() -> None:
    sv = _schema_view("classes:\n  A: {}\n")

    assert get_schema(sv).name == "probe"


def test_root_context_keeps_terms_of_the_schema_default_prefix() -> None:
    sv = _schema_view(
        """
slots:
  label:
    slot_uri: ex:label
    range: string
classes:
  Probe:
    class_uri: ex:Probe
    slots: [label]
"""
    )
    root = json.loads(_jsonld_context(sv))["@context"]
    assert "label" in root
    assert "Probe" in root


def _schema_view_with_default_prefix_line(default_prefix_line: str) -> SchemaView:
    return SchemaView(
        f"""
id: https://example.org/probe
name: probe
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/ex#
{default_prefix_line}
imports: [linkml:types]
classes:
  Probe:
    class_uri: ex:Probe
"""
    )


def test_default_prefix_returns_declared_default_prefix() -> None:
    assert default_prefix(_schema_view("classes:\n  A: {}\n")) == "ex"


def test_default_prefix_undeclared_raises_schema_error_naming_value_and_schema() -> None:
    sv = _schema_view_with_default_prefix_line("default_prefix: zz")

    with pytest.raises(SchemaError, match=r"default_prefix 'zz' is not declared.*'probe'"):
        default_prefix(sv)


def test_root_context_with_omitted_default_prefix_raises_schema_error() -> None:
    # LinkML substitutes the schema id for an omitted default_prefix, which is never a declared prefix.
    sv = _schema_view_with_default_prefix_line("")
    substituted = get_schema(sv).default_prefix

    with pytest.raises(SchemaError, match=rf"default_prefix '{substituted}' is not declared.*'probe'"):
        _jsonld_context(sv)


FOREIGN_SLOT_SCHEMA = """
slots:
  stamp:
    slot_uri: a:stamp
    range: string
classes:
  Probe:
    class_uri: ex:Probe
    slots: [stamp]
"""


def test_root_context_drops_term_outside_default_prefix() -> None:
    root = json.loads(_jsonld_context(_schema_view(FOREIGN_SLOT_SCHEMA)))["@context"]

    assert "stamp" not in root


def test_root_context_keeps_extra_root_term_outside_default_prefix() -> None:
    root = json.loads(_jsonld_context(_schema_view(FOREIGN_SLOT_SCHEMA), ("stamp",)))["@context"]

    assert root["stamp"] == {"@id": "a:stamp"}


def test_extra_root_term_missing_from_generated_context_raises_schema_error_naming_term() -> None:
    with pytest.raises(SchemaError, match=r"'nowhere'"):
        _jsonld_context(_schema_view(FOREIGN_SLOT_SCHEMA), ("nowhere",))


def _remaining_defs(body: str, defs: dict) -> set[str]:
    return set(post_process_jsonschema({"$defs": defs}, _schema_view(body))["$defs"])


def test_unreferenced_def_of_linkml_any_class_is_dropped() -> None:
    body = "classes:\n  Wildcard:\n    class_uri: linkml:Any\n"
    assert _remaining_defs(body, {"Wildcard": {"type": "object"}}) == set()


def test_unreferenced_def_of_tree_root_class_is_dropped() -> None:
    body = "classes:\n  Root:\n    tree_root: true\n"
    assert _remaining_defs(body, {"Root": {"type": "object"}}) == set()


def test_unreferenced_def_of_abstract_class_is_dropped() -> None:
    body = "classes:\n  Base:\n    abstract: true\n"
    assert _remaining_defs(body, {"Base": {"type": "object"}}) == set()


def test_unreferenced_def_of_enum_subset_partitioned_class_is_dropped_and_its_variants_kept() -> None:
    body = """
subsets:
  reads:
    description: Read operations.
enums:
  Op:
    permissible_values:
      get: {in_subset: [reads]}
slots:
  op: {range: Op}
classes:
  Split:
    slots: [op]
    annotations:
      jsonschema_enum_subset_partition:
        value: {slot: op, enum: Op}
"""
    remaining = _remaining_defs(body, {"Split": {"type": "object", "properties": {"op": {"type": "string"}}}})
    assert remaining == {"Split_element_base", "Split_element_reads"}


def test_drop_candidate_still_referenced_is_kept() -> None:
    body = "classes:\n  Base:\n    abstract: true\n"
    defs = {"Base": {"type": "object"}, "Holder": {"type": "object", "properties": {"b": {"$ref": "#/$defs/Base"}}}}
    assert _remaining_defs(body, defs) == {"Base", "Holder"}


def test_drop_candidate_referenced_only_by_dropped_defs_is_dropped() -> None:
    body = "classes:\n  Root:\n    tree_root: true\n  Base:\n    abstract: true\n"
    defs = {"Base": {"type": "object"}, "Root": {"type": "object", "properties": {"b": {"$ref": "#/$defs/Base"}}}}
    assert _remaining_defs(body, defs) == set()


def test_def_of_unmarked_class_named_form_is_kept() -> None:
    assert _remaining_defs("classes:\n  Form: {}\n", {"Form": {"type": "object"}}) == {"Form"}


def _holder_property(body: str, target: str) -> dict:
    holder = {"type": "object", "properties": {"v": {"$ref": f"#/$defs/{target}"}}}
    defs = {target: {"type": "object"}, "Holder": holder}
    return post_process_jsonschema({"$defs": defs}, _schema_view(body))["$defs"]["Holder"]["properties"]["v"]


def test_ref_to_linkml_any_class_not_named_any_is_unconstrained() -> None:
    body = "classes:\n  Wildcard:\n    class_uri: linkml:Any\n  Holder: {}\n"
    assert "$ref" not in _holder_property(body, "Wildcard")


def test_ref_to_unmarked_class_named_any_is_kept() -> None:
    body = "classes:\n  Any: {}\n  Holder: {}\n"
    assert _holder_property(body, "Any") == {"$ref": "#/$defs/Any"}

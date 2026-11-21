"""The JSON Schema postprocessor takes project-specific decisions from the schema, never from name or shape guesses."""

from __future__ import annotations

from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.postprocessors.jsonschema_postprocessor import post_process_jsonschema

SCHEMA_HEADER = """
id: https://example.org/probe
name: probe
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/ex#
default_prefix: ex
imports: [linkml:types]
"""

PARTITIONED_BODY = """
subsets:
  reads:
    description: Read modes.
enums:
  Mode:
    permissible_values:
      peek: {in_subset: [reads]}
slots:
  mode: {range: Mode}
  entries: {range: Entry, multivalued: true, inlined_as_list: true}
classes:
  Entry:
    slots: [mode]
    annotations:
      jsonschema_enum_subset_partition:
        value: {slot: mode, enum: Mode}
  Catalog:
    tree_root: %(catalog_is_root)s
    slots: [entries]
    slot_usage:
      entries:
        annotations:
          jsonschema_form_subset:
            value: reads
"""

NARROWED_ITEMS = {"$ref": "#/$defs/Entry_element_reads"}
UNNARROWED_ITEMS = {"$ref": "#/$defs/Entry"}


def _entries_property() -> dict:
    return {"type": "array", "items": dict(UNNARROWED_ITEMS)}


def _post_process(raw: dict, catalog_is_root: bool) -> dict:
    body = PARTITIONED_BODY % {"catalog_is_root": "true" if catalog_is_root else "false"}
    return post_process_jsonschema(raw, SchemaView(SCHEMA_HEADER + body))


def _entry_def() -> dict:
    return {"type": "object", "properties": {"mode": {"type": "string"}}}


def test_form_subset_on_non_root_class_leaves_top_level_properties_alone_even_with_matching_keys() -> None:
    raw = {
        "properties": {"entries": _entries_property()},
        "$defs": {"Entry": _entry_def(), "Catalog": {"type": "object", "properties": {"entries": _entries_property()}}},
    }
    processed = _post_process(raw, catalog_is_root=False)
    assert processed["$defs"]["Catalog"]["properties"]["entries"]["items"] == NARROWED_ITEMS
    assert processed["properties"]["entries"]["items"] == UNNARROWED_ITEMS


def test_form_subset_on_tree_root_narrows_top_level_properties_even_with_differing_keys() -> None:
    raw = {
        "properties": {"entries": _entries_property(), "extra": {"type": "string"}},
        "$defs": {"Entry": _entry_def(), "Catalog": {"type": "object", "properties": {"entries": _entries_property()}}},
    }
    processed = _post_process(raw, catalog_is_root=True)
    assert processed["properties"]["entries"]["items"] == NARROWED_ITEMS


def test_form_subset_on_non_root_class_without_def_leaves_top_level_properties_alone() -> None:
    raw = {"properties": {"entries": _entries_property()}, "$defs": {"Entry": _entry_def()}}
    processed = _post_process(raw, catalog_is_root=False)
    assert processed["properties"]["entries"]["items"] == UNNARROWED_ITEMS

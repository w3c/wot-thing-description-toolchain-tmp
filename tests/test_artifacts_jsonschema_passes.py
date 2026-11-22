import copy
from typing import Any

from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.artifacts.jsonschema.annotations import read_annotations
from wot_toolchain.artifacts.jsonschema.postprocess import JSONSCHEMA_PASSES, post_process_jsonschema
from wot_toolchain.artifacts.passes import Pass, run_passes

SCHEMA = """
id: https://example.org/probe
name: probe
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/ex#
default_prefix: ex
imports: [linkml:types]
classes:
  Wildcard:
    class_uri: linkml:Any
  Holder: {}
"""

ORDER_BEFORE_THE_MOVE = [
    "flatten_subclasses",
    "build_oneof_dispatch",
    "build_enum_subset_partitions",
    "narrow_form_subsets",
    "dedup_oneof",
    "normalize_types",
    "simplify_exclusive_minimum",
    "remove_identifier_slots",
    "remove_excluded_defs",
    "resolve_refs",
    "remove_unreferenced_candidate_defs",
    "clean_metadata",
]

RESOLVE = "resolve_refs"
PRUNE = "remove_unreferenced_candidate_defs"


def _raw() -> dict[str, Any]:
    return {
        "$defs": {
            "Wildcard": {"type": "object"},
            "Holder": {"type": "object", "properties": {"v": {"$ref": "#/$defs/Wildcard"}}},
        }
    }


def _run(passes: list[Pass]) -> dict[str, Any]:
    schema_view = SchemaView(SCHEMA)
    schema = copy.deepcopy(_raw())
    run_passes(passes, schema, schema_view, read_annotations(schema_view))
    return schema


def test_passes_run_in_the_order_of_the_legacy_postprocessor() -> None:
    assert [p.name for p in JSONSCHEMA_PASSES] == ORDER_BEFORE_THE_MOVE


def test_every_pass_has_a_reason() -> None:
    assert all(p.reason.strip() for p in JSONSCHEMA_PASSES)


def test_candidate_defs_are_pruned_after_refs_are_resolved() -> None:
    names = [p.name for p in JSONSCHEMA_PASSES]

    assert names.index(RESOLVE) < names.index(PRUNE)


def test_def_of_linkml_any_class_is_dropped_once_its_refs_are_resolved() -> None:
    processed = post_process_jsonschema(_raw(), SchemaView(SCHEMA))

    assert set(processed["$defs"]) == {"Holder"}
    assert processed["$defs"]["Holder"]["properties"]["v"] == {}


def test_pruning_before_resolving_refs_would_keep_the_def_of_a_linkml_any_class() -> None:
    passes = list(JSONSCHEMA_PASSES)
    resolve, prune = (next(i for i, p in enumerate(passes) if p.name == name) for name in (RESOLVE, PRUNE))
    passes[resolve], passes[prune] = passes[prune], passes[resolve]

    assert set(_run(passes)["$defs"]) == {"Holder", "Wildcard"}

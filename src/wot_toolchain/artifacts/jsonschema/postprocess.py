"""Lists the JSON Schema transforms in run order and applies them to the raw LinkML JSON Schema."""

from __future__ import annotations

import copy
import logging

from linkml_runtime.utils.schemaview import SchemaView

from ..transforms import Transform, TransformKind, run_transforms
from .annotations import _read_annotations
from .cleanups import _clean_metadata, _normalize_types, _remove_identifier_slots, _simplify_exclusive_minimum
from .pruning import _remove_excluded_defs
from .refs import _resolve_refs
from .subclasses import _build_oneof_dispatch, _flatten_subclasses
from .variants import _build_form_variants

logger = logging.getLogger(__name__)


JSONSCHEMA_TRANSFORMS: tuple[Transform, ...] = (
    Transform(
        name="flatten_subclasses",
        kind=TransformKind.WOT_SHAPING,
        reason="Merges the properties of the direct subclasses of a class annotated jsonschema_flatten_subclasses "
        "into that class, deletes the subclass defs, and copies the merged properties to the classes that use it "
        "as a mixin.",
        apply=_flatten_subclasses,
    ),
    Transform(
        name="build_oneof_dispatch",
        kind=TransformKind.WOT_SHAPING,
        reason="Replaces a class annotated jsonschema_oneof_dispatch by a oneOf over its direct subclasses. With "
        "include_unknown it adds a branch for objects whose discriminator value has a prefix.",
        apply=_build_oneof_dispatch,
    ),
    Transform(
        name="build_form_variants",
        kind=TransformKind.WOT_SHAPING,
        reason="Replaces a class annotated jsonschema_form_variants by a oneOf over one def per listed group of op "
        "values and a base def that only matches objects without op.",
        apply=lambda schema, sv, config: _build_form_variants(schema, config),
    ),
    Transform(
        name="normalize_types",
        kind=TransformKind.LINKML_BUG,
        reason="LinkML emits type next to oneOf for a property with exactly_one_of. Removes that type, which "
        "rejects the oneOf branches of another type.",
        apply=lambda schema, sv, config: _normalize_types(schema),
    ),
    Transform(
        name="simplify_exclusive_minimum",
        kind=TransformKind.LINKML_GAP,
        reason="LinkML has no exclusive minimum. The schema writes minimum_value plus none_of equals_number with "
        "the same value, which LinkML emits as minimum plus not.anyOf.const. Rewrites that to exclusiveMinimum.",
        apply=lambda schema, sv, config: _simplify_exclusive_minimum(schema),
    ),
    Transform(
        name="remove_identifier_slots",
        kind=TransformKind.WOT_SHAPING,
        reason="Removes identifier slots from properties and required. They are the keys of a map, not members of "
        "the JSON object.",
        apply=lambda schema, sv, config: _remove_identifier_slots(schema, sv),
    ),
    Transform(
        name="remove_excluded_defs",
        kind=TransformKind.COSMETIC,
        reason="Removes the defs of classes annotated jsonschema_exclude, of enums, the __identifier_optional defs, "
        "and the defs Any, Thing and InteractionAffordance.",
        apply=_remove_excluded_defs,
    ),
    Transform(
        name="resolve_refs",
        kind=TransformKind.WOT_SHAPING,
        reason="Repairs references after the removals: inlines enums, removes refs to Any, points "
        "__identifier_optional refs to the base def, and reduces an anyOf in additionalProperties to one schema.",
        apply=lambda schema, sv, config: _resolve_refs(schema, sv),
    ),
    Transform(
        name="clean_metadata",
        kind=TransformKind.COSMETIC,
        reason="Removes description and title from every def, and metamodel_version and version from the root.",
        apply=lambda schema, sv, config: _clean_metadata(schema),
    ),
)


def post_process_jsonschema(raw_schema: dict, schema_view: SchemaView) -> dict:
    schema = copy.deepcopy(raw_schema)
    config = _read_annotations(schema_view)

    logger.info("JSON Schema postprocessor: reading annotations")
    logger.debug(f"  flatten_subclass_parents: {config.flatten_subclass_parents}")
    logger.debug(f"  oneof_dispatches: {[d.class_name for d in config.oneof_dispatches]}")
    logger.debug(f"  form_variants: {[f.class_name for f in config.form_variants]}")

    run_transforms(JSONSCHEMA_TRANSFORMS, schema, schema_view, config)

    return schema

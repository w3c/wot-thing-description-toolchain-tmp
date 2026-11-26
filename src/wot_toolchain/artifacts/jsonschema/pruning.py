"""Transforms that delete definitions with no use in the published JSON Schema."""

import logging
from typing import Any

from linkml_runtime.utils.schemaview import SchemaView

from .annotations import TransformConfig
from .traversal import extract_ref_name, is_linkml_any

logger = logging.getLogger(__name__)


def _drop_candidate_defs(defs: dict[str, Any], sv: SchemaView, config: TransformConfig) -> set[str]:
    """Return the defs of classes with no standalone use in the published JSON Schema.

    These are classes for ``linkml:Any``, the top class (its content is the top-level schema), and
    enum-subset-partitioned classes (replaced by their per-subset variants). Abstract classes and tree roots other
    than the top class are part of the model and keep their defs.

    Args:
        defs: The ``$defs`` of the schema being post-processed.
        sv: The schema view of the LinkML schema.
        config: The transforms read from the ``jsonschema_*`` annotations, and the top class.

    Returns:
        The names of the candidate defs present in ``defs``.
    """
    partitioned = {esp.class_name for esp in config.enum_subset_partitions}
    return {
        name
        for name, cls_def in sv.all_classes().items()
        if name in defs and (is_linkml_any(sv, cls_def) or name == config.top_class or name in partitioned)
    }


def _referenced_def_names(obj: Any) -> set[str]:
    """Return the names of all defs that a ``$ref`` anywhere in ``obj`` points to.

    Args:
        obj: A JSON Schema fragment.

    Returns:
        The referenced def names.
    """
    if isinstance(obj, list):
        return set().union(*(_referenced_def_names(item) for item in obj))
    if not isinstance(obj, dict):
        return set()
    names = set().union(*(_referenced_def_names(value) for value in obj.values()))
    ref = obj.get("$ref")
    ref_name = extract_ref_name(ref) if isinstance(ref, str) else None
    if ref_name is not None:
        names.add(ref_name)
    return names


def _unreferenced_candidates(schema: dict[str, Any], candidates: set[str]) -> set[str]:
    """Return the candidate defs that no ``$ref`` outside the dropped defs points to.

    Starts from dropping every candidate and keeps each one still referenced, until no kept def references a dropped
    one, so dropping the result can never leave a dangling ``$ref``.

    Args:
        schema: The JSON Schema being post-processed.
        candidates: The names of the defs that may be dropped.

    Returns:
        The names of the candidates that can be dropped.
    """
    top_level = {key: value for key, value in schema.items() if key != "$defs"}
    dropped = set(candidates)
    while True:
        kept_defs = {name: defn for name, defn in schema.get("$defs", {}).items() if name not in dropped}
        still_referenced = dropped & _referenced_def_names([top_level, kept_defs])
        if not still_referenced:
            return dropped
        dropped -= still_referenced


def remove_unreferenced_candidate_defs(schema: dict[str, Any], sv: SchemaView, config: TransformConfig) -> None:
    """Delete the defs of drop-candidate classes that no ``$ref`` in the schema points to.

    Args:
        schema: The JSON Schema being post-processed, after its ``$ref`` values are resolved.
        sv: The schema view of the LinkML schema.
        config: The transforms read from the ``jsonschema_*`` annotations.
    """
    defs = schema.get("$defs", {})
    for name in _unreferenced_candidates(schema, _drop_candidate_defs(defs, sv, config)):
        del defs[name]
        logger.debug(f"Removed unreferenced def: {name}")


def remove_excluded_defs(schema: dict[str, Any], sv: SchemaView, config: TransformConfig) -> None:
    """Delete the definitions of excluded classes, of enums and of ``__identifier_optional`` variants."""
    defs = schema.get("$defs", {})
    to_remove = set()

    to_remove.update(config.excluded_classes)

    for name in list(defs.keys()):
        if name.endswith("__identifier_optional"):
            to_remove.add(name)

    for enum_name in sv.all_enums():
        if enum_name in defs:
            to_remove.add(enum_name)

    for name in to_remove:
        if name in defs:
            del defs[name]
            logger.debug(f"Removed def: {name}")

"""Passes that clean up constructs the upstream generator leaves in the JSON Schema."""

from typing import Any

from linkml_runtime.utils.schemaview import SchemaView

from .traversal import walk_schema


def dedup_oneof(schema: dict[str, Any]) -> None:
    """Deduplicate identical oneOf branches (e.g. string vs langString both map to {"type":"string"})."""

    def _dedup(obj: dict[str, Any]) -> None:
        if "oneOf" not in obj or not isinstance(obj["oneOf"], list):
            return
        unique: list[dict[str, Any]] = []
        for item in obj["oneOf"]:
            if item not in unique:
                unique.append(item)
        if len(unique) == 1:
            obj.pop("oneOf")
            obj.update(unique[0])
        elif len(unique) < len(obj["oneOf"]):
            obj["oneOf"] = unique

    walk_schema(schema, _dedup)


def simplify_exclusive_minimum(schema: dict[str, Any]) -> None:
    """Rewrite ``minimum`` plus a ``not`` of that same constant to ``exclusiveMinimum``."""

    def _fix(obj: dict[str, Any]) -> None:
        if "minimum" in obj and "not" in obj and isinstance(obj["not"], dict) and "anyOf" in obj["not"]:
            any_of = obj["not"]["anyOf"]
            if (
                len(any_of) == 1
                and isinstance(any_of[0], dict)
                and "const" in any_of[0]
                and any_of[0]["const"] == obj["minimum"]
            ):
                val = obj.pop("minimum")
                del obj["not"]
                obj["exclusiveMinimum"] = val

    walk_schema(schema, _fix)


def clean_metadata(schema: dict[str, Any], sv: SchemaView) -> None:
    """Drop each definition's ``description`` and ``title`` and ``metamodel_version``; take ``version`` from ``sv``."""
    for defn in schema.get("$defs", {}).values():
        if isinstance(defn, dict):
            defn.pop("description", None)
            defn.pop("title", None)

    schema.pop("metamodel_version", None)
    if sv.schema.version:
        schema["version"] = sv.schema.version
    else:
        schema.pop("version", None)

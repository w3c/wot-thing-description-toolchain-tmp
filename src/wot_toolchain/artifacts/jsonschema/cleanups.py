"""Passes that clean up constructs the upstream generator leaves in the JSON Schema."""

from typing import Any


from .traversal import walk_schema


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


def clean_metadata(schema: dict[str, Any]) -> None:
    """Drop each definition's ``description`` and ``title``."""
    for defn in schema.get("$defs", {}).values():
        if isinstance(defn, dict):
            defn.pop("description", None)
            defn.pop("title", None)

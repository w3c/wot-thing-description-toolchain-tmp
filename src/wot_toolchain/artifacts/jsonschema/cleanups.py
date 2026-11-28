"""Passes that clean up constructs the upstream generator leaves in the JSON Schema."""

from typing import Any


def clean_metadata(schema: dict[str, Any]) -> None:
    """Drop each definition's ``description`` and ``title``."""
    for defn in schema.get("$defs", {}).values():
        if isinstance(defn, dict):
            defn.pop("description", None)
            defn.pop("title", None)

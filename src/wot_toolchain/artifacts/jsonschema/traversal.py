"""Helpers shared by the JSON Schema passes: tree walk, ``$ref`` names, ``linkml:Any`` classes."""

from collections.abc import Callable
from typing import Any

from linkml_runtime.linkml_model.meta import ClassDefinition
from linkml_runtime.utils.schemaview import SchemaView

LINKML_ANY_URI = "https://w3id.org/linkml/Any"


def walk_schema(obj: Any, fn: Callable[[dict[str, Any]], dict[str, Any] | None]) -> Any:
    """Apply ``fn`` to every dict in ``obj``, top-down; a non-None result of ``fn`` replaces the dict."""
    if isinstance(obj, dict):
        result = fn(obj)
        if result is not None:
            obj = result
        for key in list(obj.keys()):
            obj[key] = walk_schema(obj[key], fn)
    elif isinstance(obj, list):
        return [walk_schema(item, fn) for item in obj]
    return obj


def extract_ref_name(ref: str) -> str | None:
    """Return the definition name a local ``$ref`` points to, or None for any other reference."""
    for prefix in ("#/$defs/", "#/definitions/"):
        if ref.startswith(prefix):
            return ref[len(prefix) :]
    return None


def is_linkml_any(sv: SchemaView, cls_def: ClassDefinition) -> bool:
    """Return whether the class stands for ``linkml:Any``, written as a CURIE or as the expanded URI."""
    return bool(cls_def.class_uri) and sv.expand_curie(str(cls_def.class_uri)) == LINKML_ANY_URI

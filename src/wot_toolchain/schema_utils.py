"""Shared schema utilities for WoT postprocessors and generators."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from linkml_runtime.linkml_model.meta import SchemaDefinition
from linkml_runtime.utils.schemaview import SchemaView

from .errors import SchemaError


def get_schema(sv: SchemaView) -> SchemaDefinition:
    """Return the SchemaDefinition of a SchemaView.

    Raises:
        SchemaError: The SchemaView has no schema loaded.
    """
    schema = sv.schema
    if schema is None:
        raise SchemaError("SchemaView has no schema loaded; construct it from a LinkML schema file or definition.")
    return schema


def resolve_prefix_namespace(sv: SchemaView, prefix: str) -> str:
    """Return the full namespace URI for a schema-declared prefix.

    Raises:
        SchemaError: ``prefix`` is not declared in the ``prefixes`` of the schema.
    """
    p = sv.schema.prefixes.get(prefix)
    if p is None:
        raise SchemaError(
            f"prefix {prefix!r} is not declared in the prefixes of schema {sv.schema.name!r}. "
            "Declare it under 'prefixes' or use a declared prefix."
        )
    ns = str(p.prefix_reference)
    if not ns.endswith(("#", "/")):
        ns += "#"
    return ns


def curie_prefix(uri: str | None) -> str | None:
    """Extract the prefix part of a CURIE (e.g. 'td:name' -> 'td')."""
    if uri is None or ":" not in uri:
        return None
    return uri.partition(":")[0]


def annotation_str_value(annotatable: Any, key: str) -> str | None:
    """Get annotation value as string from an annotatable element.

    Handles both dict-style and object-style annotations on the element.
    Used by JSON-LD context postprocessor where annotation values are simple strings.
    """
    annotations = getattr(annotatable, "annotations", None) or {}
    annotation = annotations.get(key) if isinstance(annotations, dict) else getattr(annotations, key, None)
    return str(annotation.value) if annotation else None


def annotation_tag_value(annotatable: Any, key: str) -> Any | None:
    """Get annotation value by tag from an annotatable element.

    Iterates annotations by `.tag` attribute and converts JsonObj values
    to plain dicts. Used by JSON Schema postprocessor where annotation
    values may be complex JSON objects.
    """
    if not hasattr(annotatable, "annotations") or not annotatable.annotations:
        return None
    for ann in annotatable.annotations.values():
        if ann.tag == key:
            return _jsonobj_to_dict(ann.value)
    return None


def annotation_dict_value(annotations: dict, key: str) -> Any | None:
    """Get annotation value from a pre-extracted annotations dict.

    Returns raw annotation or its `.value` attribute. Used by respec
    generator and spec tables where the annotations dict is already
    extracted by the caller.
    """
    ann = annotations.get(key)
    if ann is None:
        return None
    return getattr(ann, "value", ann)


def _jsonobj_to_dict(obj: Any) -> Any:
    """Convert JsonObj instances to plain dicts recursively."""
    try:
        from jsonasobj2._jsonobj import JsonObj

        if isinstance(obj, JsonObj):
            result = {}
            for key in (k for k in dir(obj) if not k.startswith("_")):
                try:
                    val = getattr(obj, key)
                    if callable(val):
                        continue
                    result[key] = _jsonobj_to_dict(val)
                except AttributeError:
                    continue
            return result
    except ImportError:
        pass
    if isinstance(obj, dict):
        return {k: _jsonobj_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_jsonobj_to_dict(v) for v in obj]
    return obj


def load_schema_view(schema_path: Path, *, merge_imports: bool) -> SchemaView:
    """Load a LinkML schema file.

    Raises:
        SchemaError: If the file is missing or is not valid YAML.
    """
    if not schema_path.is_file():
        raise SchemaError(f"LinkML schema file not found: {schema_path}")
    try:
        return SchemaView(schema_path, merge_imports=merge_imports)
    except yaml.YAMLError as exc:
        raise SchemaError(f"LinkML schema {schema_path} is not valid YAML: {exc}") from exc

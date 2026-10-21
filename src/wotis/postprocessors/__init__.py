"""Shared helpers for WoT postprocessors."""

from __future__ import annotations

from linkml_runtime.utils.schemaview import SchemaView


def resolve_prefix_namespace(sv: SchemaView, prefix: str) -> str:
    """Return the full namespace URI for a schema-declared prefix."""
    p = sv.schema.prefixes.get(prefix)
    if p is None:
        raise ValueError(f"Unknown prefix: {prefix}")
    ns = str(p.prefix_reference)
    if not ns.endswith(("#", "/")):
        ns += "#"
    return ns


def curie_prefix(uri: str | None) -> str | None:
    """Extract the prefix part of a CURIE (e.g. 'td:name' → 'td')."""
    if uri is None or ":" not in uri:
        return None
    return uri.partition(":")[0]

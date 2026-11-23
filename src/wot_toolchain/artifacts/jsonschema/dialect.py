"""Header and dialect of the generated JSON Schema, as the config file sets them."""

from collections.abc import Iterator
from typing import Any

from wot_toolchain.errors import GenerationError

SCHEMA_URIS = {
    "draft-07": "http://json-schema.org/draft-07/schema#",
    "2019-09": "https://json-schema.org/draft/2019-09/schema",
}

_SUBSCHEMA_KEYWORDS = frozenset(
    {"additionalItems", "additionalProperties", "contains", "else", "if", "items", "not", "propertyNames", "then"}
)
_SUBSCHEMA_LIST_KEYWORDS = frozenset({"allOf", "anyOf", "items", "oneOf"})
_SUBSCHEMA_MAP_KEYWORDS = frozenset({"$defs", "definitions", "patternProperties", "properties"})
_KEYWORDS_NEWER_THAN_DRAFT_07 = frozenset(
    {
        "$anchor",
        "$recursiveAnchor",
        "$recursiveRef",
        "dependentRequired",
        "dependentSchemas",
        "maxContains",
        "minContains",
        "unevaluatedItems",
        "unevaluatedProperties",
    }
)


def apply_settings(schema: dict[str, Any], *, id: str, description: str, dialect: str) -> None:  # noqa: A002
    """Set ``$id``, ``description`` and ``$schema`` of ``schema`` and express it in ``dialect``, in place.

    Raises:
        GenerationError: ``schema`` uses a keyword that ``dialect`` does not define.
    """
    schema["$schema"] = SCHEMA_URIS[dialect]
    schema["$id"] = id
    schema["description"] = description
    if dialect == "draft-07":
        _express_in_draft_07(schema)


def _express_in_draft_07(schema: dict[str, Any]) -> None:
    for subschema in list(_subschemas(schema)):
        if unsupported := sorted(_KEYWORDS_NEWER_THAN_DRAFT_07 & subschema.keys()):
            raise GenerationError(
                f"The JSON Schema uses {', '.join(unsupported)}, which draft-07 does not define. "
                "Set generators.jsonschema.dialect to 2019-09."
            )
        if "$defs" in subschema:
            subschema["definitions"] = subschema.pop("$defs")
        reference = subschema.get("$ref")
        if isinstance(reference, str):
            subschema["$ref"] = reference.replace("#/$defs/", "#/definitions/", 1)
            # Draft-07 ignores every keyword next to "$ref".
            if len(subschema) > 1:
                subschema.setdefault("allOf", []).insert(0, {"$ref": subschema.pop("$ref")})


def _subschemas(schema: Any) -> Iterator[dict[str, Any]]:
    if not isinstance(schema, dict):
        return
    yield schema
    for keyword, value in schema.items():
        if keyword in _SUBSCHEMA_MAP_KEYWORDS and isinstance(value, dict):
            children = list(value.values())
        elif keyword in _SUBSCHEMA_LIST_KEYWORDS and isinstance(value, list):
            children = value
        elif keyword in _SUBSCHEMA_KEYWORDS:
            children = [value]
        else:
            continue
        for child in children:
            yield from _subschemas(child)

"""Passes that clean up constructs the upstream generator leaves in the JSON Schema."""

from typing import Any

from linkml_runtime.utils.schemaview import SchemaView

from .traversal import walk_schema
from ...errors import SchemaError


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


def normalize_types(schema: dict[str, Any]) -> None:
    """Drop ``type`` from each property that also has a ``oneOf``."""

    def _strip_oneof_type(props: dict[str, Any]) -> None:
        for prop in props.values():
            if isinstance(prop, dict) and "oneOf" in prop:
                prop.pop("type", None)

    _strip_oneof_type(schema.get("properties", {}))
    for defn in schema.get("$defs", {}).values():
        if isinstance(defn, dict) and "properties" in defn:
            _strip_oneof_type(defn["properties"])


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


def remove_identifier_slots(schema: dict[str, Any], sv: SchemaView) -> None:
    """Drop identifier slots from the properties and required lists of each class definition.

    Definitions that are not LinkML classes (e.g. generated ``__identifier_optional`` variants) are left untouched.

    Raises:
        SchemaError: If the slots of a class definition cannot be resolved.
    """
    defs = schema.get("$defs", {})
    all_classes = sv.all_classes()

    for cls_name in list(defs.keys()):
        defn = defs[cls_name]
        if not isinstance(defn, dict) or "properties" not in defn or cls_name not in all_classes:
            continue

        try:
            induced_slots = sv.class_induced_slots(cls_name)
        except ValueError as exc:
            raise SchemaError(f"class {cls_name!r}: cannot resolve its slots: {exc}") from exc

        for slot in induced_slots:
            if getattr(slot, "identifier", False) and slot.name in defn["properties"]:
                defn["properties"].pop(slot.name)
                req = defn.get("required", [])
                if slot.name in req:
                    req.remove(slot.name)
                if not req:
                    defn.pop("required", None)


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

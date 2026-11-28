"""Passes that split a class by enum subset and narrow slots to one subset variant."""

from typing import Any

from .annotations import TransformConfig


def build_enum_subset_partitions(schema: dict[str, Any], config: TransformConfig) -> None:
    """Replace each partitioned class definition by a ``oneOf`` of one variant per subset of its enum slot."""
    defs = schema.get("$defs", {})

    for esp in config.enum_subset_partitions:
        cls_name = esp.class_name
        if cls_name not in defs:
            continue

        original = defs[cls_name]
        original_props = original.get("properties", {})
        original_required = original.get("required", [])

        base_props = {k: v for k, v in original_props.items() if k != esp.slot_name}
        base_def = {
            "type": "object",
            "properties": base_props,
            "required": original_required,
            "additionalProperties": original.get("additionalProperties", True),
        }
        base_name = f"{cls_name}_element_base"
        defs[base_name] = base_def

        array_constraints = _array_constraints(original_props.get(esp.slot_name, {}))
        variant_refs = []
        for subset_name, ops in esp.subsets.items():
            variant_def_name = f"{cls_name}_element_{subset_name}"
            array_branch = {"type": "array", "items": {"enum": ops}} | array_constraints
            op_schema = {"oneOf": [{"const": op} for op in ops] + [array_branch]}
            narrowing = {"type": "object", "properties": {esp.slot_name: op_schema}}
            variant_def = {"allOf": [{"$ref": f"#/$defs/{base_name}"}, narrowing]}
            defs[variant_def_name] = variant_def
            variant_refs.append({"$ref": f"#/$defs/{variant_def_name}"})

        defs[cls_name] = {"oneOf": variant_refs}


def _array_constraints(slot_schema: dict[str, Any]) -> dict[str, Any]:
    """Return the array-level keywords (e.g. ``minItems``) of the array form of ``slot_schema``, without its items."""
    branches = [slot_schema, *slot_schema.get("oneOf", []), *slot_schema.get("anyOf", [])]
    array: dict[str, Any] = next((branch for branch in branches if branch.get("type") == "array"), {})
    return {key: value for key, value in array.items() if key not in ("type", "items")}

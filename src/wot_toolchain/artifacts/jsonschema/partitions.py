"""Passes that split a class by enum subset and narrow slots to one subset variant."""

from typing import Any

from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.artifacts.jsonschema.annotations import TransformConfig


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

        variant_refs = []
        for subset_name, ops in esp.subsets.items():
            variant_def_name = f"{cls_name}_element_{subset_name}"
            op_schema = {"oneOf": [{"const": op} for op in ops] + [{"type": "array", "items": {"enum": ops}}]}
            variant_def = {
                "allOf": [
                    {"$ref": f"#/$defs/{base_name}"},
                    {
                        "type": "object",
                        "properties": {esp.slot_name: op_schema},
                    },
                ]
            }
            defs[variant_def_name] = variant_def
            variant_refs.append({"$ref": f"#/$defs/{variant_def_name}"})

        defs[cls_name] = {"oneOf": variant_refs}


def _narrow_slot_items(props: dict[str, Any], slot_name: str, items: dict[str, Any]) -> None:
    """Replace the array ``items`` of ``slot_name`` in ``props``, if that slot is an array property.

    Args:
        props: The ``properties`` of a class definition or of the top-level schema.
        slot_name: The name of the slot to narrow.
        items: The new ``items`` schema.
    """
    slot_prop = props.get(slot_name)
    if isinstance(slot_prop, dict) and "items" in slot_prop:
        slot_prop["items"] = items


def narrow_form_subsets(schema: dict[str, Any], sv: SchemaView, config: TransformConfig) -> None:
    """Narrow the array items of each ``jsonschema_form_subset`` slot to its subset variant.

    The tree root class is also narrowed in the top-level ``properties``, which hold the tree root's content.

    Args:
        schema: The JSON Schema being post-processed, after its enum-subset partitions are built.
        sv: The schema view of the LinkML schema.
        config: The transforms read from the ``jsonschema_*`` annotations.
    """
    defs = schema.get("$defs", {})
    for narrow in config.form_subset_narrows:
        base_name = f"{narrow.partition_class}_element_base"
        variant_def_name = f"{narrow.partition_class}_element_{narrow.subset_name}"
        if variant_def_name not in defs or base_name not in defs:
            continue
        narrowed_items = {"$ref": f"#/$defs/{variant_def_name}"}

        cls_def = defs.get(narrow.class_name)
        if isinstance(cls_def, dict) and "properties" in cls_def:
            _narrow_slot_items(cls_def["properties"], narrow.slot_name, narrowed_items)
        if sv.get_class(narrow.class_name).tree_root:
            _narrow_slot_items(schema.get("properties", {}), narrow.slot_name, narrowed_items)

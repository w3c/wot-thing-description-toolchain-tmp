"""Transform that replaces a form class by a ``oneOf`` over one definition per group of ``op`` values."""

from __future__ import annotations

from .annotations import Annotations


def _build_form_variants(schema: dict, config: Annotations) -> None:
    defs = schema.get('$defs', {})

    for fv in config.form_variants:
        cls_name = fv.class_name
        if cls_name not in defs:
            continue

        original = defs[cls_name]
        original_props = original.get('properties', {})
        original_required = original.get('required', [])

        base_props = {k: v for k, v in original_props.items() if k != fv.op_slot}
        base_def = {
            "type": "object",
            "properties": base_props,
            "required": original_required,
            "additionalProperties": original.get('additionalProperties', True),
        }
        base_name = f"{cls_name}_element_base"
        defs[base_name] = base_def

        variant_refs = []
        for variant_name, ops in fv.variants.items():
            variant_def_name = f"{cls_name}_element_{variant_name}"
            op_schema = {
                "oneOf": [{"const": op} for op in ops] +
                         [{"type": "array", "items": {"enum": ops}}]
            }
            variant_def = {
                "allOf": [
                    {"$ref": f"#/$defs/{base_name}"},
                    {
                        "type": "object",
                        "properties": {fv.op_slot: op_schema},
                        "required": [fv.op_slot],
                    }
                ]
            }
            defs[variant_def_name] = variant_def
            variant_refs.append({"$ref": f"#/$defs/{variant_def_name}"})

        # The base branch takes only forms without op, otherwise a form with op also matches a variant and oneOf fails (KNOWN_LINKML_GAPS.md #10).
        defs[cls_name] = {
            "oneOf": variant_refs + [
                {"$ref": f"#/$defs/{base_name}", "not": {"required": [fv.op_slot]}}
            ]
        }

        thing_props = schema.get('properties', {})
        if 'forms' in thing_props:
            forms_prop = thing_props['forms']
            if isinstance(forms_prop, dict) and 'items' in forms_prop:
                forms_prop['items'] = {"$ref": f"#/$defs/{cls_name}"}

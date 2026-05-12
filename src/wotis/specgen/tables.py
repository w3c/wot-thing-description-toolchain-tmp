from __future__ import annotations
from typing import Any, Dict, List, Callable, Optional
from linkml_runtime.utils.schemaview import SchemaView

from .assertions import make_slot_assertion_id

def _normalize_range_name(rng: str) -> str:
    """
    Map LinkML range names to the textual form expected in the TD spec.

    Currently:
      - LinkML 'uri' -> spec 'anyURI'
      - everything else unchanged.
    """
    if not rng:
        return ""
    if rng in ["Any", "linkml:Any"]:
        return "any type"
    if rng == "uri":
        return "anyURI"
    if rng == "datetime":
        return "dateTime"
    if rng == "NonNegativeInteger":
        return "unsignedInt"
    if rng == "decimal":
        return "double"
    return rng


def _annotation_value(annotations: dict, key: str):
    ann = annotations.get(key)
    if ann is None:
        return None
    return getattr(ann, "value", ann)


def _is_truthy_annotation(value) -> bool:
    value = getattr(value, "value", value)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1", "with default"}
    return value is not None


def _has_default_assignment(slot_name: str, class_def, slot_def) -> bool:
    return any(
        _is_truthy_annotation(_annotation_value(annotations, "spec_default"))
        for annotations in _annotation_candidates(slot_name, class_def, slot_def)
    )


def _annotation_candidates(slot_name: str, class_def, slot_def) -> List[dict]:
    candidates = [getattr(slot_def, "annotations", None) or {}]
    usage = (class_def.slot_usage or {}).get(slot_name)
    if usage:
        candidates.append(getattr(usage, "annotations", None) or {})
    if slot_name in (class_def.attributes or {}):
        candidates.append(
            getattr(class_def.attributes[slot_name], "annotations", None) or {}
        )
    return candidates


def _get_type_values_annotation(slot_name: str, class_def, slot_def):
    for annotations in reversed(_annotation_candidates(slot_name, class_def, slot_def)):
        value = _annotation_value(annotations, "spec_type_values")
        if value is not None:
            return value
    return None


def _format_value_list(values: List[str]) -> str:
    values = [str(value) for value in values if str(value)]
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    return f"{', '.join(values[:-1])}, or {values[-1]}"


def _append_type_values(type_text: str, slot_name: str, class_def, slot_def) -> str:
    value_config = _get_type_values_annotation(slot_name, class_def, slot_def)
    if isinstance(value_config, dict):
        values = value_config.get("values") or []
        mode = value_config.get("mode")
    else:
        values = getattr(value_config, "values", None) or []
        mode = getattr(value_config, "mode", None)
    if not isinstance(values, list):
        return type_text

    formatted_values = _format_value_list(values)
    if not formatted_values:
        return type_text

    mode = str(mode or "examples").strip().lower()
    if mode in {"one_of", "one-of", "one of", "closed"}:
        label = "one of"
    else:
        label = "e.g.,"
    return f"{type_text} ({label} {formatted_values})"


def get_assignment(slot_name, class_def, slot_def) -> str:
    usage = (class_def.slot_usage or {}).get(slot_name)
    if _has_default_assignment(slot_name, class_def, slot_def):
        return '<a href="#sec-default-values">with default</a>'
    if getattr(slot_def, "required", False) or (usage and getattr(usage, "required", False)):
        return "mandatory"
    min_value = getattr(slot_def, "minimum_value", None)
    if usage and getattr(usage, "minimum_value", None) is not None:
        min_value = usage.minimum_value
    try:
        if min_value is not None and float(min_value) > 0:
            return "mandatory"
    except Exception:
        pass
    return "optional"


def slot_type_text(slot_name: str, slot_def, class_def, sv: SchemaView, effective_range: Optional[str] = None) -> str:
    raw_rng = effective_range if effective_range else getattr(slot_def, "range", None)
    # Choice Logic (exactly_one_of or any_of)
    usage = (getattr(class_def, "slot_usage", None) or {}).get(slot_name)
    choices = None
    if usage:
        choices = getattr(usage, "exactly_one_of", None) or getattr(usage, "any_of", None)
    if choices:
        pretty = []
        seen = set()
        for alt in choices:
            # Check local alt range first, then fallback to effective/global range
            alt_rng_raw = getattr(alt, "range", None)
            if not alt_rng_raw:
                alt_rng_raw = raw_rng
            rng = _normalize_range_name(alt_rng_raw)
            mv = bool(getattr(alt, "multivalued", False))
            # --- SPECIAL HANDLING FOR @CONTEXT where we do not want to specify the range in the table---
            # If multivalued and range is empty or not provided in the alt, just return "Array"
            if mv:
                if not getattr(alt, "range", None) and slot_name == "@context":
                    p = "Array"
                else:
                    p = f"Array of {rng}" if rng else "Array"
            else:
                p = rng if rng else ""
            if p and p not in seen:
                seen.add(p)
                pretty.append(p)
        return _append_type_values(
            " or ".join(pretty),
            slot_name,
            class_def,
            slot_def,
        )
    # ENUM LOGIC
    all_enums = sv.all_enums()
    if raw_rng in all_enums:
        enum_def = all_enums[raw_rng]
        is_uri_enum = (enum_def.enum_uri in ["linkml:uri", "anyURI"] or raw_rng.lower() == "uri")
        enum_base = "anyURI" if is_uri_enum else "string"
        if _get_type_values_annotation(slot_name, class_def, slot_def) is not None:
            return _append_type_values(enum_base, slot_name, class_def, slot_def)
        pv_names = list(enum_def.permissible_values.keys())
        if pv_names:
            formatted_pvs = f"{', '.join(pv_names[:-1])}, or {pv_names[-1]}" if len(pv_names) > 1 else pv_names[0]
            return f"anyURI (one of {formatted_pvs})" if is_uri_enum else f"string (e.g., {formatted_pvs})"
        return "string"
    # STANDARD FALLBACK
    rng = _normalize_range_name(raw_rng)
    if not rng:
        return ""
    if getattr(slot_def, "inlined", False):
        return _append_type_values(f"Map of {rng}", slot_name, class_def, slot_def)
    if getattr(slot_def, "multivalued", False):
        return _append_type_values(f"Array of {rng}", slot_name, class_def, slot_def)
    return _append_type_values(rng, slot_name, class_def, slot_def)


def collect_slot_rows(sv: SchemaView, class_name: str, process_description: Callable[[str], str], schema_prefix: str = "",
                      ) -> List[Dict[str, Any]]:
    """
        Collect all visible slot rows for *class_name* in schema-defined order.
        Each returned dict now includes an ``assertion_id`` key containing the
       stable RFC 2119 table-assertion ID for use as the <tr id="..."> attribute.

        The ID is generated by make_slot_assertion_id(schema_prefix, class_name,
        slot_name) and follows the convention: <prefix>-<ClassName-kebab>-<slotName-kebab>
        e.g. "td-thing-context", "td-thing-title", "jsonschema-data-schema-type".
        """

    class_def = sv.get_class(class_name)
    if not class_def:
        return []
    rows: List[Dict[str, str]] = []
    slot_names: List[str] = class_def.slots or []
    # Get attribute names
    attribute_names: List[str] = list(class_def.attributes.keys()) if class_def.attributes else []
    # unique list, prioritizing explicit slots first, followed by attributes
    ordered_unique_names: List[str] = []
    seen = set()
    for name in slot_names + attribute_names:
        if name not in seen:
            ordered_unique_names.append(name)
            seen.add(name)

    for slot_name in ordered_unique_names:
        slot_def = sv.get_slot(slot_name, class_name)
        if not slot_def:
            continue

        usage = (class_def.slot_usage or {}).get(slot_name)
        ann = getattr(slot_def, "annotations", None) or {}
        effective_range_name = getattr(usage, "range", None) or getattr(slot_def, "range", None)
        if not effective_range_name:
            effective_range_name = getattr(slot_def, "range", None)
        if slot_name in class_def.attributes:
            raw_attribute_def = class_def.attributes[slot_name]
            raw_ann = getattr(raw_attribute_def, "annotations", None) or {}
            ann.update(raw_ann)
        spec_exclude_ann = ann.get("spec_exclude")
        if spec_exclude_ann:
            val = getattr(spec_exclude_ann, 'value', spec_exclude_ann)
            if str(val).lower() == 'true':
                continue
        raw_desc = getattr(slot_def, "description", "")
        usage_ann = getattr(usage, "annotations", None) or {} if usage else {}
        if "spec_description" in usage_ann:
            raw_desc = str(getattr(usage_ann["spec_description"], "value", usage_ann["spec_description"]))
        elif usage and getattr(usage, "description", None):
            raw_desc = usage.description
        elif "spec_description" in ann:
            raw_desc = str(getattr(ann["spec_description"], "value", ann["spec_description"]))
        desc_html = process_description(raw_desc)
        desc = (desc_html or "").replace("'", "&#39;")
        # special case for the name defined in wot_security.yaml, name is a reserved keyword in LinkML.
        if slot_name == "@name":
            display_name = "name"
        else:
            display_name = slot_name
        assertion_id = make_slot_assertion_id(schema_prefix, class_name, slot_name) if schema_prefix else ""
        rows.append({
            "slot_name": display_name,
            "assertion_id": assertion_id,
            "description": desc,
            "assignment": get_assignment(slot_name, class_def, slot_def),
            "range_text": slot_type_text(
                slot_name=slot_name,
                slot_def=slot_def,
                class_def=class_def,
                sv=sv,
                effective_range=effective_range_name
            ),
            "range_original": effective_range_name,
        })
    return rows

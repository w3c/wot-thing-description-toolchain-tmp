from __future__ import annotations
from typing import Any, Dict, List, Callable, Optional
from linkml_runtime.utils.schemaview import SchemaView
from linkml_runtime.linkml_model.meta import SlotDefinition

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

def get_assignment(slot_name, class_def, slot_def) -> str:
    usage = (class_def.slot_usage or {}).get(slot_name)
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
    # Determine the base range
    raw_rng = effective_range if effective_range else getattr(slot_def, "range", None)
    # 2. Choice Logic (exactly_one_of or any_of)
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
        return " or ".join(pretty)
    # ENUM LOGIC
    all_enums = sv.all_enums()
    if raw_rng in all_enums:
        enum_def = all_enums[raw_rng]
        pv_names = list(enum_def.permissible_values.keys())
        if pv_names:
            formatted_pvs = f"{', '.join(pv_names[:-1])}, or {pv_names[-1]}" if len(pv_names) > 1 else pv_names[0]
            is_uri_enum = (enum_def.enum_uri in ["linkml:uri", "anyURI"] or raw_rng.lower() == "uri")
            return f"anyURI (one of {formatted_pvs})" if is_uri_enum else f"string (e.g., {formatted_pvs})"
        return "string"
    # 4. STANDARD FALLBACK
    rng = _normalize_range_name(raw_rng)
    if not rng:
        return ""
    if getattr(slot_def, "inlined", False):
        return f"Map of {rng}"
    if getattr(slot_def, "multivalued", False):
        return f"Array of {rng}"
    return rng


def collect_slot_rows(sv: SchemaView, class_name: str, process_description: Callable[[str], str]) -> List[Dict[str, str]]:
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
        # Determine effective_range_name
        effective_range_name = getattr(usage, "range", None) or getattr(slot_def, "range", None)
        if not effective_range_name:
            effective_range_name = getattr(slot_def, "range", None)
        # Merge raw attribute annotations into 'ann' for exclusion check
        if slot_name in class_def.attributes:
            raw_attribute_def = class_def.attributes[slot_name]
            raw_ann = getattr(raw_attribute_def, "annotations", None) or {}
            ann.update(raw_ann)
        spec_exclude_ann = ann.get("spec_exclude")
        if spec_exclude_ann:
            val = getattr(spec_exclude_ann, 'value', spec_exclude_ann)
            if str(val).lower() == 'true':
                continue
        # Determine the source text for the description in the tables
        raw_desc = getattr(slot_def, "description", "")
        usage_ann = getattr(usage, "annotations", None) or {} if usage else {}
        if "spec_table_definition" in usage_ann:
            raw_desc = str(getattr(usage_ann["spec_table_definition"], "value", usage_ann["spec_table_definition"]))
        elif usage and getattr(usage, "description", None):
            raw_desc = usage.description
        elif "spec_table_definition" in ann:
            raw_desc = str(getattr(ann["spec_table_definition"], "value", ann["spec_table_definition"]))
        desc_html = process_description(raw_desc)
        desc = (desc_html or "").replace("'", "&#39;")
        # special case for the name defined in wot_security.yaml, name is a reserved keyword.
        if slot_name == "@name":
            display_name = "name"
        else:
            display_name = slot_name
        rows.append({
            "slot_name": display_name,
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
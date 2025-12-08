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


def slot_type_text(slot_name: str, slot_def, class_def, effective_range: Optional[str] = None) -> str:
    usage = (getattr(class_def, "slot_usage", None) or {}).get(slot_name)
    xo = getattr(usage, "exactly_one_of", None) if usage else None
    if xo:
        alts = []
        for alt in xo:
            # Prioritize effective_range if provided, otherwise check alt, then slot_def
            raw_rng = effective_range if effective_range else getattr(alt, "range", None) or getattr(slot_def, "range",
                                                                                                     None)
            rng = _normalize_range_name(raw_rng)
            mv = bool(getattr(alt, "multivalued", False))
            alts.append((rng, mv))
        ranges = {r for r, _ in alts}
        for r in ranges:
            flags = {mv for rr, mv in alts if rr == r}
            if flags == {False, True}:
                return f"{r} or Array of {r}"
        pretty = [(f"{r} or Array" if mv else r) for r, mv in alts]
        seen, out = set(), []
        for p in pretty:
            if p not in seen:
                seen.add(p)
                out.append(p)
        return "".join(out)

    raw_rng = effective_range if effective_range else getattr(slot_def, "range", None)
    rng = _normalize_range_name(raw_rng)
    if not rng:
        return ""
    if getattr(slot_def, "inlined", False):
        return f"Map of {rng}"
    if getattr(slot_def, "multivalued", False):
        return f"Array of {rng}"
    return rng


def collect_slot_rows(sv: SchemaView, class_name: str, process_description: Callable[[str], str]) -> List[
    Dict[str, str]]:
    class_def = sv.get_class(class_name)
    rows: List[Dict[str, str]] = []
    # Get ordered slot names
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
        slot_def: Optional[SlotDefinition] = sv.get_slot(slot_name, class_name)
        if not slot_def:
            continue

        # Get annotations from the resolved slot_def (includes merged global and local annotations)
        ann = getattr(slot_def, "annotations", None) or {}
        # Get raw slot_usage object for explicit local override
        usage = (class_def.slot_usage or {}).get(slot_name)
        # Determine effective_range_name 🛑
        effective_range_name = getattr(usage, "range", None)
        if not effective_range_name:
            effective_range_name = getattr(slot_def, "range", None)
        # Check raw attribute definition for annotations
        if slot_name in class_def.attributes:
            raw_attribute_def = class_def.attributes[slot_name]
            # Merge raw attribute annotations into 'ann' for exclusion check
            raw_ann = getattr(raw_attribute_def, "annotations", None) or {}
            ann.update(raw_ann)
        spec_exclude_ann = ann.get("spec_exclude")
        if spec_exclude_ann:
            ann_value = getattr(spec_exclude_ann, 'value', None)
            if ann_value is None:
                ann_value = spec_exclude_ann

            if str(ann_value).lower() == 'true':
                continue
        # Determine the source text for the description in the tables
        raw_desc = getattr(slot_def, "description", "")

        if usage:
            # Check for local 'spec_table_definition' override in slot_usage
            usage_ann = getattr(usage, "annotations", None) or {}
            if "spec_table_definition" in usage_ann:
                spec_def = getattr(usage_ann["spec_table_definition"], "value", None) or usage_ann[
                    "spec_table_definition"]
                # Prioritize local annotation
                raw_desc = str(spec_def)
            # If no spec_table_definition, check for local 'description' override in slot_usage
            elif getattr(usage, "description", None):
                raw_desc = getattr(usage, "description")

            # Prioritize resolved slot's 'spec_table_definition' (from global/merged annotations)
        elif "spec_table_definition" in ann:  # Only check resolved annotations if no slot_usage override was found
            spec_def = getattr(ann["spec_table_definition"], "value", None) or ann["spec_table_definition"]
            raw_desc = str(spec_def) or raw_desc

        desc_html = process_description(raw_desc)
        desc = (desc_html or "").replace("'", "&#39;")
        rows.append({
            "slot_name": slot_name,
            "description": desc,
            "assignment": get_assignment(slot_name, class_def, slot_def),
            "range_text": slot_type_text(
                slot_name,
                slot_def,
                class_def,
                effective_range=effective_range_name
            ),
            "range_original": effective_range_name,
        })
    return rows
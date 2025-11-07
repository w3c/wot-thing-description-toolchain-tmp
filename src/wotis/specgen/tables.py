from __future__ import annotations
from typing import Dict, List
from linkml_runtime.utils.schemaview import SchemaView

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

def slot_type_text(slot_name: str, slot_def, class_def) -> str:
    usage = (getattr(class_def, "slot_usage", None) or {}).get(slot_name)
    xo = getattr(usage, "exactly_one_of", None) if usage else None
    if xo:
        alts = []
        for alt in xo:
            rng = getattr(alt, "range", None) or getattr(slot_def, "range", None) or "any type"
            mv = bool(getattr(alt, "multivalued", False))
            alts.append((rng, mv))
        ranges = {r for r, _ in alts}
        for r in ranges:
            flags = {mv for rr, mv in alts if rr == r}
            if flags == {False, True}:
                return f"{r} or Array of {r}"
        pretty = [(f"{r} (Array)" if mv else r) for r, mv in alts]
        # preserve order / dedupe
        seen, out = set(), []
        for p in pretty:
            if p not in seen:
                seen.add(p); out.append(p)
        return " | ".join(out)

    rng = getattr(slot_def, "range", None) or "any type"
    if getattr(slot_def, "inlined", False):
        return f"Map of {rng}"
    if getattr(slot_def, "multivalued", False):
        return f"{rng} (Array)"
    return rng

def collect_slot_rows(sv: SchemaView, class_name: str) -> List[Dict[str, str]]:
    class_def = sv.get_class(class_name)
    rows: List[Dict[str, str]] = []
    for slot_name in class_def.slots or []:
        slot_def = sv.get_slot(slot_name)
        desc = (getattr(slot_def, "description", "") or "").replace("'", "&#39;").replace('"', "&quot;")
        rows.append({
            "slot_name": slot_name,
            "description": desc,
            "assignment": get_assignment(slot_name, class_def, slot_def),
            "range_text": slot_type_text(slot_name, slot_def, class_def),
        })
    return rows

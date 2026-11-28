"""Resolution of the ``$ref`` values the upstream generator leaves dangling or indirect in a class def."""

from typing import Any

from linkml_runtime.utils.schemaview import SchemaView

from .traversal import extract_ref_name, is_linkml_any, walk_schema
from ...errors import SchemaError


def _narrow_string_branches(siblings: dict[str, Any], values: list[str]) -> bool:
    """Put ``values`` as ``enum`` on each string or string array branch of a ``oneOf``/``anyOf`` beside an enum ref.

    Returns False and changes nothing when there is no such branch or a branch of another kind.
    """
    targets: list[dict[str, Any]] = []
    for keyword in ("oneOf", "anyOf"):
        for branch in siblings.get(keyword, []):
            target = branch.get("items") if branch.get("type") == "array" else branch
            if not isinstance(target, dict) or target.get("type") != "string":
                return False
            targets.append(target)
    for target in targets:
        target["enum"] = list(values)
    return bool(targets)


def resolve_refs(schema: dict[str, Any], sv: SchemaView) -> dict[str, Any]:
    """Return ``schema`` with enum references inlined, ``linkml:Any`` references erased, the others on class defs.

    Raises:
        SchemaError: If the slots of a referenced class cannot be resolved.
    """
    class_names = set(sv.all_classes())

    enum_values: dict[str, list[str]] = {}
    for enum_name, enum_def in sv.all_enums().items():
        pvs = list(enum_def.permissible_values.keys()) if enum_def.permissible_values else []
        if pvs:
            enum_values[enum_name] = pvs

    any_class_names = {name for name, cls_def in sv.all_classes().items() if is_linkml_any(sv, cls_def)}

    def _is_string_map(cls_name: str | None) -> bool:
        if cls_name is None or cls_name not in sv.all_classes():
            return False
        try:
            slots = sv.class_induced_slots(cls_name)
        except ValueError as exc:
            raise SchemaError(f"class {cls_name!r}: cannot resolve its slots: {exc}") from exc
        non_id = [s for s in slots if not getattr(s, "identifier", False)]
        return len(slots) == 2 and len(non_id) == 1 and non_id[0].range == "string"

    def _fix_additional_props_anyof(obj: dict[str, Any]) -> None:
        if "additionalProperties" not in obj:
            return
        ap = obj["additionalProperties"]
        if not isinstance(ap, dict) or "anyOf" not in ap:
            return
        items = ap["anyOf"]
        if not isinstance(items, list):
            return

        for item in items:
            if isinstance(item, dict) and "$ref" in item and "__identifier_optional" in item["$ref"]:
                base = item["$ref"].replace("__identifier_optional", "")
                # W3C titles/descriptions are string maps, LinkML also emits the object form, keep only the string
                # form (KNOWN_LINKML_GAPS.md #11).
                if _is_string_map(extract_ref_name(base)):
                    obj["additionalProperties"] = {"type": "string"}
                else:
                    obj["additionalProperties"] = {"$ref": base}
                return

        refs = [i for i in items if isinstance(i, dict) and "$ref" in i]
        non_refs = [i for i in items if not (isinstance(i, dict) and "$ref" in i)]
        if len(refs) == 1 and all(isinstance(i, dict) and i.get("type") in ("null", "string") for i in non_refs):
            obj["additionalProperties"] = refs[0]

    def _resolve(obj: dict[str, Any]) -> dict[str, Any] | None:
        _fix_additional_props_anyof(obj)

        if "$ref" not in obj:
            return None
        ref = obj["$ref"]
        ref_name = extract_ref_name(ref)
        if ref_name is None:
            return None

        if ref_name in enum_values:
            siblings = {key: value for key, value in obj.items() if key != "$ref"}
            if _narrow_string_branches(siblings, enum_values[ref_name]):
                return siblings
            return {"type": "string", "enum": enum_values[ref_name]} | siblings

        if ref_name in any_class_names:
            del obj["$ref"]
        elif ref_name not in class_names:
            base = ref_name.replace("__identifier_optional", "")
            if base in class_names:
                obj["$ref"] = f"#/$defs/{base}"
        elif not ref.startswith("#/$defs/"):
            obj["$ref"] = f"#/$defs/{ref_name}"

        return None

    resolved: dict[str, Any] = walk_schema(schema, _resolve)
    return resolved

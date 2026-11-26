"""Transform that inlines enum ``$ref`` values and repoints or removes ``$ref`` values to deleted definitions."""

from __future__ import annotations

from linkml_runtime.utils.schemaview import SchemaView

from .traversal import _walk_schema


def _resolve_refs(schema: dict, sv: SchemaView) -> None:
    valid_def_names = set(schema.get('$defs', {}).keys())

    enum_values: dict[str, list[str]] = {}
    for enum_name, enum_def in sv.all_enums().items():
        pvs = list(enum_def.permissible_values.keys()) if enum_def.permissible_values else []
        if pvs:
            enum_values[enum_name] = pvs

    def _extract_ref_name(ref: str) -> str | None:
        prefix = '#/$defs/'
        return ref[len(prefix):] if ref.startswith(prefix) else None

    def _is_string_map(cls_name: str | None) -> bool:
        if cls_name is None:
            return False
        try:
            slots = sv.class_induced_slots(cls_name)
        except Exception:
            return False
        non_id = [s for s in slots if not getattr(s, 'identifier', False)]
        return len(slots) == 2 and len(non_id) == 1 and non_id[0].range == 'string'

    def _fix_additional_props_anyof(obj: dict) -> None:
        if 'additionalProperties' not in obj:
            return
        ap = obj['additionalProperties']
        if not isinstance(ap, dict) or 'anyOf' not in ap:
            return
        items = ap['anyOf']
        if not isinstance(items, list):
            return

        for item in items:
            if isinstance(item, dict) and '$ref' in item and '__identifier_optional' in item['$ref']:
                base = item['$ref'].replace('__identifier_optional', '')
                # W3C titles/descriptions are string maps, LinkML also emits the object form, keep only the string form (KNOWN_LINKML_GAPS.md #11).
                if _is_string_map(_extract_ref_name(base)):
                    obj['additionalProperties'] = {'type': 'string'}
                else:
                    obj['additionalProperties'] = {'$ref': base}
                return

        refs = [i for i in items if isinstance(i, dict) and '$ref' in i]
        non_refs = [i for i in items if not (isinstance(i, dict) and '$ref' in i)]
        if len(refs) == 1 and all(
            isinstance(i, dict) and i.get('type') in ('null', 'string') for i in non_refs
        ):
            obj['additionalProperties'] = refs[0]

    def _resolve(obj: dict) -> dict | None:
        _fix_additional_props_anyof(obj)

        if '$ref' not in obj:
            return None
        ref = obj['$ref']
        ref_name = _extract_ref_name(ref)
        if ref_name is None:
            return None

        if ref_name in enum_values:
            result = {"type": "string", "enum": enum_values[ref_name]}
            if 'description' in obj:
                result['description'] = obj['description']
            return result

        if ref_name == 'Any':
            del obj['$ref']
        elif ref_name not in valid_def_names:
            base = ref_name.replace('__identifier_optional', '')
            if base in valid_def_names:
                obj['$ref'] = f'#/$defs/{base}'

        return None

    _walk_schema(schema, _resolve)

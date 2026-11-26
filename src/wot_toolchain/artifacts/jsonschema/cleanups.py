"""Transforms that remove ``type`` next to ``oneOf``, write ``exclusiveMinimum``, drop identifier slots and metadata."""

from __future__ import annotations

from linkml_runtime.utils.schemaview import SchemaView

from .traversal import _walk_schema


def _normalize_types(schema: dict) -> None:
    def _strip_oneof_type(props: dict) -> None:
        for prop in props.values():
            if isinstance(prop, dict) and 'oneOf' in prop:
                prop.pop('type', None)

    _strip_oneof_type(schema.get('properties', {}))
    for defn in schema.get('$defs', {}).values():
        if isinstance(defn, dict) and 'properties' in defn:
            _strip_oneof_type(defn['properties'])


def _simplify_exclusive_minimum(schema: dict) -> None:
    def _fix(obj: dict) -> None:
        if ('minimum' in obj and 'not' in obj
                and isinstance(obj['not'], dict) and 'anyOf' in obj['not']):
            any_of = obj['not']['anyOf']
            if (len(any_of) == 1 and isinstance(any_of[0], dict)
                    and 'const' in any_of[0]
                    and any_of[0]['const'] == obj['minimum']):
                val = obj.pop('minimum')
                del obj['not']
                obj['exclusiveMinimum'] = val

    _walk_schema(schema, _fix)


def _remove_identifier_slots(schema: dict, sv: SchemaView) -> None:
    defs = schema.get('$defs', {})

    for cls_name in list(defs.keys()):
        defn = defs[cls_name]
        if not isinstance(defn, dict) or 'properties' not in defn:
            continue

        try:
            induced_slots = sv.class_induced_slots(cls_name)
        except Exception:
            continue

        for slot in induced_slots:
            if getattr(slot, 'identifier', False) and slot.name in defn['properties']:
                defn['properties'].pop(slot.name)
                req = defn.get('required', [])
                if slot.name in req:
                    req.remove(slot.name)
                if not req:
                    defn.pop('required', None)


def _clean_metadata(schema: dict) -> None:
    for defn in schema.get('$defs', {}).values():
        if isinstance(defn, dict):
            defn.pop('description', None)
            defn.pop('title', None)

    schema.pop('metamodel_version', None)
    schema.pop('version', None)

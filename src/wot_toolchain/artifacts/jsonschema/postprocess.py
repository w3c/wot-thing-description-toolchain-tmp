"""
Annotation-driven post-processor that transforms raw LinkML JSON Schema output
into the W3C WoT Thing Description JSON Schema.
"""

from __future__ import annotations

import copy
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from linkml_runtime.utils.schemaview import SchemaView

from ..transforms import Transform, TransformKind, run_transforms

logger = logging.getLogger(__name__)


@dataclass
class OneOfDispatchConfig:
    class_name: str
    discriminator: str
    include_unknown: bool = False


@dataclass
class FormVariantsConfig:
    class_name: str
    op_slot: str
    variants: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class Annotations:
    flatten_subclass_parents: list[str] = field(default_factory=list)
    oneof_dispatches: list[OneOfDispatchConfig] = field(default_factory=list)
    form_variants: list[FormVariantsConfig] = field(default_factory=list)
    excluded_classes: list[str] = field(default_factory=list)


def _walk_schema(obj: Any, fn: Callable[[dict], dict | None]) -> Any:
    if isinstance(obj, dict):
        result = fn(obj)
        if result is not None:
            obj = result
        for key in list(obj.keys()):
            obj[key] = _walk_schema(obj[key], fn)
    elif isinstance(obj, list):
        return [_walk_schema(item, fn) for item in obj]
    return obj


def _jsonobj_to_dict(obj: Any) -> Any:
    try:
        from jsonasobj2._jsonobj import JsonObj
        if isinstance(obj, JsonObj):
            result = {}
            for key in (k for k in dir(obj) if not k.startswith('_')):
                try:
                    val = getattr(obj, key)
                    if callable(val):
                        continue
                    result[key] = _jsonobj_to_dict(val)
                except AttributeError:
                    continue
            return result
    except ImportError:
        pass
    if isinstance(obj, dict):
        return {k: _jsonobj_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_jsonobj_to_dict(v) for v in obj]
    return obj


def _get_annotation_value(annotatable, key: str) -> Any | None:
    if not hasattr(annotatable, 'annotations') or not annotatable.annotations:
        return None
    for ann in annotatable.annotations.values():
        if ann.tag == key:
            return _jsonobj_to_dict(ann.value)
    return None


def _read_annotations(sv: SchemaView) -> Annotations:
    config = Annotations()

    for cls_name, cls_def in sv.all_classes().items():
        if _get_annotation_value(cls_def, 'jsonschema_flatten_subclasses'):
            config.flatten_subclass_parents.append(cls_name)

        oneof = _get_annotation_value(cls_def, 'jsonschema_oneof_dispatch')
        if oneof:
            config.oneof_dispatches.append(OneOfDispatchConfig(
                class_name=cls_name,
                discriminator=oneof['discriminator'],
                include_unknown=oneof.get('include_unknown', False),
            ))

        fv = _get_annotation_value(cls_def, 'jsonschema_form_variants')
        if fv:
            config.form_variants.append(FormVariantsConfig(
                class_name=cls_name,
                op_slot=fv['op_slot'],
                variants=fv['variants'],
            ))

        if _get_annotation_value(cls_def, 'jsonschema_exclude'):
            config.excluded_classes.append(cls_name)

    return config



def _flatten_subclasses(schema: dict, sv: SchemaView, config: Annotations) -> None:
    defs = schema.get('$defs', {})

    for parent_name in config.flatten_subclass_parents:
        if parent_name not in defs:
            continue

        parent_def = defs[parent_name]
        parent_props = parent_def.get('properties', {})
        subclasses_to_remove = []
        new_props: dict[str, Any] = {}

        for cls_name, cls_def in sv.all_classes().items():
            if cls_def.is_a == parent_name and cls_name in defs:
                sub_def = defs[cls_name]
                sub_props = sub_def.get('properties', {})
                for prop_name, prop_schema in sub_props.items():
                    if prop_name not in parent_props:
                        parent_props[prop_name] = prop_schema
                        new_props[prop_name] = prop_schema
                subclasses_to_remove.append(cls_name)

        for cls_name in subclasses_to_remove:
            del defs[cls_name]
            logger.debug(f"Removed subclass def {cls_name}, merged into {parent_name}")

        if new_props:
            for cls_name, cls_def in sv.all_classes().items():
                if parent_name in (cls_def.mixins or []) and cls_name in defs:
                    target_props = defs[cls_name].get('properties', {})
                    for prop_name, prop_schema in new_props.items():
                        if prop_name not in target_props:
                            target_props[prop_name] = prop_schema
                    logger.debug(f"Propagated flattened props to mixin user {cls_name}")


def _build_oneof_dispatch(schema: dict, sv: SchemaView, config: Annotations) -> None:
    defs = schema.get('$defs', {})

    for dispatch in config.oneof_dispatches:
        cls_name = dispatch.class_name
        if cls_name not in defs:
            continue

        subclass_refs = []
        for sub_name, sub_def in sv.all_classes().items():
            if sub_def.is_a == cls_name and sub_name in defs:
                subclass_refs.append({"$ref": f"#/$defs/{sub_name}"})

        one_of_list: list[dict[str, Any]] = sorted(subclass_refs, key=lambda x: x["$ref"])

        # W3C additionalSecurityScheme: a prefixed scheme, so the catch-all does not overlap the known schemes (KNOWN_LINKML_GAPS.md #9).
        if dispatch.include_unknown:
            one_of_list.append({
                "type": "object",
                "description": f"Additional {cls_name} not covered by known subclasses",
                "properties": {dispatch.discriminator: {"type": "string", "pattern": ".+:.*"}},
                "required": [dispatch.discriminator],
            })

        defs[cls_name] = {"oneOf": one_of_list}


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


def _remove_excluded_defs(schema: dict, sv: SchemaView, config: Annotations) -> None:
    defs = schema.get('$defs', {})
    to_remove = set()

    to_remove.update(config.excluded_classes)

    for name in list(defs.keys()):
        if name.endswith('__identifier_optional'):
            to_remove.add(name)

    for enum_name in sv.all_enums():
        if enum_name in defs:
            to_remove.add(enum_name)

    to_remove.update(['Any', 'Thing', 'InteractionAffordance'])

    for name in to_remove:
        if name in defs:
            del defs[name]
            logger.debug(f"Removed def: {name}")


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


def _clean_metadata(schema: dict) -> None:
    for defn in schema.get('$defs', {}).values():
        if isinstance(defn, dict):
            defn.pop('description', None)
            defn.pop('title', None)

    schema.pop('metamodel_version', None)
    schema.pop('version', None)


JSONSCHEMA_TRANSFORMS: tuple[Transform, ...] = (
    Transform(
        name="flatten_subclasses",
        kind=TransformKind.WOT_SHAPING,
        reason="Merges the properties of the direct subclasses of a class annotated jsonschema_flatten_subclasses "
        "into that class, deletes the subclass defs, and copies the merged properties to the classes that use it "
        "as a mixin.",
        apply=_flatten_subclasses,
    ),
    Transform(
        name="build_oneof_dispatch",
        kind=TransformKind.WOT_SHAPING,
        reason="Replaces a class annotated jsonschema_oneof_dispatch by a oneOf over its direct subclasses. With "
        "include_unknown it adds a branch for objects whose discriminator value has a prefix.",
        apply=_build_oneof_dispatch,
    ),
    Transform(
        name="build_form_variants",
        kind=TransformKind.WOT_SHAPING,
        reason="Replaces a class annotated jsonschema_form_variants by a oneOf over one def per listed group of op "
        "values and a base def that only matches objects without op.",
        apply=lambda schema, sv, config: _build_form_variants(schema, config),
    ),
    Transform(
        name="normalize_types",
        kind=TransformKind.LINKML_BUG,
        reason="LinkML emits type next to oneOf for a property with exactly_one_of. Removes that type, which "
        "rejects the oneOf branches of another type.",
        apply=lambda schema, sv, config: _normalize_types(schema),
    ),
    Transform(
        name="simplify_exclusive_minimum",
        kind=TransformKind.LINKML_GAP,
        reason="LinkML has no exclusive minimum. The schema writes minimum_value plus none_of equals_number with "
        "the same value, which LinkML emits as minimum plus not.anyOf.const. Rewrites that to exclusiveMinimum.",
        apply=lambda schema, sv, config: _simplify_exclusive_minimum(schema),
    ),
    Transform(
        name="remove_identifier_slots",
        kind=TransformKind.WOT_SHAPING,
        reason="Removes identifier slots from properties and required. They are the keys of a map, not members of "
        "the JSON object.",
        apply=lambda schema, sv, config: _remove_identifier_slots(schema, sv),
    ),
    Transform(
        name="remove_excluded_defs",
        kind=TransformKind.COSMETIC,
        reason="Removes the defs of classes annotated jsonschema_exclude, of enums, the __identifier_optional defs, "
        "and the defs Any, Thing and InteractionAffordance.",
        apply=_remove_excluded_defs,
    ),
    Transform(
        name="resolve_refs",
        kind=TransformKind.WOT_SHAPING,
        reason="Repairs references after the removals: inlines enums, removes refs to Any, points "
        "__identifier_optional refs to the base def, and reduces an anyOf in additionalProperties to one schema.",
        apply=lambda schema, sv, config: _resolve_refs(schema, sv),
    ),
    Transform(
        name="clean_metadata",
        kind=TransformKind.COSMETIC,
        reason="Removes description and title from every def, and metamodel_version and version from the root.",
        apply=lambda schema, sv, config: _clean_metadata(schema),
    ),
)


def post_process_jsonschema(raw_schema: dict, schema_view: SchemaView) -> dict:
    schema = copy.deepcopy(raw_schema)
    config = _read_annotations(schema_view)

    logger.info("JSON Schema postprocessor: reading annotations")
    logger.debug(f"  flatten_subclass_parents: {config.flatten_subclass_parents}")
    logger.debug(f"  oneof_dispatches: {[d.class_name for d in config.oneof_dispatches]}")
    logger.debug(f"  form_variants: {[f.class_name for f in config.form_variants]}")

    run_transforms(JSONSCHEMA_TRANSFORMS, schema, schema_view, config)

    return schema

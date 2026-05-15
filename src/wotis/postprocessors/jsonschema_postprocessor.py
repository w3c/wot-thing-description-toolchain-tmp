"""
Annotation-driven post-processor that transforms raw LinkML JSON Schema output
into the W3C WoT Thing Description JSON Schema.

Each transform reads ``jsonschema_*`` annotations from the LinkML schemas via
SchemaView and applies the corresponding structural change to the raw output.
"""

from __future__ import annotations

import copy
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from linkml_runtime.utils.schemaview import SchemaView

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration read from annotations
# ---------------------------------------------------------------------------

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
class LinkDiscriminationConfig:
    class_name: str
    discriminator_slot: str
    icon_variant: dict[str, Any] = field(default_factory=dict)


@dataclass
class DictStyleConfig:
    slot_name: str
    ref: str
    min_properties: int | None = None


@dataclass
class TransformConfig:
    flatten_subclass_parents: list[str] = field(default_factory=list)
    oneof_dispatches: list[OneOfDispatchConfig] = field(default_factory=list)
    form_variants: list[FormVariantsConfig] = field(default_factory=list)
    link_discriminations: list[LinkDiscriminationConfig] = field(default_factory=list)
    merge_from: dict[str, list[str]] = field(default_factory=dict)
    dict_style_slots: list[DictStyleConfig] = field(default_factory=list)
    excluded_classes: list[str] = field(default_factory=list)
    extra_slots_classes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Annotation reader
# ---------------------------------------------------------------------------

def _jsonobj_to_dict(obj: Any) -> Any:
    """Convert LinkML JsonObj values to plain Python dicts/lists."""
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
            val = ann.value
            return _jsonobj_to_dict(val)
    return None


def _read_annotations(sv: SchemaView) -> TransformConfig:
    config = TransformConfig()

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

        ld = _get_annotation_value(cls_def, 'jsonschema_link_discrimination')
        if ld:
            config.link_discriminations.append(LinkDiscriminationConfig(
                class_name=cls_name,
                discriminator_slot=ld['discriminator_slot'],
                icon_variant=ld['icon_variant'],
            ))

        mf = _get_annotation_value(cls_def, 'jsonschema_merge_from')
        if mf:
            config.merge_from[cls_name] = list(mf)

        if _get_annotation_value(cls_def, 'jsonschema_exclude'):
            config.excluded_classes.append(cls_name)

        if hasattr(cls_def, 'extra_slots') and cls_def.extra_slots:
            allowed = getattr(cls_def.extra_slots, 'allowed', None)
            if allowed:
                config.extra_slots_classes.append(cls_name)

        # Check slot_usage for dict_style annotations
        if cls_def.slot_usage:
            for slot_name, slot_usage in cls_def.slot_usage.items():
                ds = _get_annotation_value(slot_usage, 'jsonschema_dict_style')
                if ds:
                    config.dict_style_slots.append(DictStyleConfig(
                        slot_name=slot_name,
                        ref=ds['ref'],
                        min_properties=ds.get('minProperties'),
                    ))

    return config


# ---------------------------------------------------------------------------
# Transform: additionalProperties from extra_slots
# ---------------------------------------------------------------------------

def _apply_additional_properties(schema: dict, config: TransformConfig) -> None:
    defs = schema.get('$defs', {})
    for cls_name in config.extra_slots_classes:
        if cls_name in defs and isinstance(defs[cls_name], dict):
            defs[cls_name]['additionalProperties'] = True

    # Top-level (Thing) — already set by LinkML when not_closed=True
    if schema.get('additionalProperties') is False:
        for cls_name in config.extra_slots_classes:
            if cls_name == 'Thing':
                schema['additionalProperties'] = True


# ---------------------------------------------------------------------------
# Transform: flatten subclasses into parent
# ---------------------------------------------------------------------------

def _flatten_subclasses(schema: dict, sv: SchemaView, config: TransformConfig) -> None:
    defs = schema.get('$defs', {})

    for parent_name in config.flatten_subclass_parents:
        if parent_name not in defs:
            continue

        parent_def = defs[parent_name]
        parent_props = parent_def.get('properties', {})
        subclasses_to_remove = []

        for cls_name, cls_def in sv.all_classes().items():
            if cls_def.is_a == parent_name and cls_name in defs:
                sub_def = defs[cls_name]
                sub_props = sub_def.get('properties', {})
                for prop_name, prop_schema in sub_props.items():
                    if prop_name not in parent_props:
                        parent_props[prop_name] = prop_schema
                subclasses_to_remove.append(cls_name)

        for cls_name in subclasses_to_remove:
            del defs[cls_name]
            logger.debug(f"Removed subclass def {cls_name}, merged into {parent_name}")


# ---------------------------------------------------------------------------
# Transform: oneOf dispatch for SecurityScheme
# ---------------------------------------------------------------------------

def _build_oneof_dispatch(schema: dict, sv: SchemaView, config: TransformConfig) -> None:
    defs = schema.get('$defs', {})

    for dispatch in config.oneof_dispatches:
        cls_name = dispatch.class_name
        if cls_name not in defs:
            continue

        subclass_refs = []
        for sub_name, sub_def in sv.all_classes().items():
            if sub_def.is_a == cls_name and sub_name in defs:
                subclass_refs.append({"$ref": f"#/$defs/{sub_name}"})

        one_of_list = sorted(subclass_refs, key=lambda x: x["$ref"])

        if dispatch.include_unknown:
            one_of_list.append({
                "type": "object",
                "description": f"Additional {cls_name} not covered by known subclasses"
            })

        # Replace parent def with oneOf dispatch
        defs[cls_name] = {"oneOf": one_of_list}


# ---------------------------------------------------------------------------
# Transform: Form variants
# ---------------------------------------------------------------------------

def _build_form_variants(schema: dict, config: TransformConfig) -> None:
    defs = schema.get('$defs', {})

    for fv in config.form_variants:
        cls_name = fv.class_name
        if cls_name not in defs:
            continue

        original = defs[cls_name]
        original_props = original.get('properties', {})
        original_required = original.get('required', [])

        # Build base: all properties except op
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

        # The main Form def becomes a oneOf over all variants (plus base for no-op case)
        defs[cls_name] = {
            "oneOf": variant_refs + [{"$ref": f"#/$defs/{base_name}"}]
        }

        # Update Thing-level forms ref to point to the new dispatch def
        thing_props = schema.get('properties', {})
        if 'forms' in thing_props:
            forms_prop = thing_props['forms']
            if isinstance(forms_prop, dict) and 'items' in forms_prop:
                forms_prop['items'] = {"$ref": f"#/$defs/{cls_name}"}


# ---------------------------------------------------------------------------
# Transform: Link discrimination
# ---------------------------------------------------------------------------

def _build_link_discrimination(schema: dict, config: TransformConfig) -> None:
    defs = schema.get('$defs', {})

    for ld in config.link_discriminations:
        cls_name = ld.class_name
        if cls_name not in defs:
            continue

        original = defs[cls_name]
        base_name = f"base_{cls_name.lower()}_element"

        # base_link_element = copy of the original Link def
        base_def = copy.deepcopy(original)
        base_def['additionalProperties'] = original.get('additionalProperties', True)
        defs[base_name] = base_def

        required_slots = ld.icon_variant.get('required_slots', [])
        rel_value = ld.icon_variant.get('rel_value')

        # link_element: base + not requiring icon-specific slots
        link_element_name = f"{cls_name.lower()}_element"
        link_element_def = {
            "allOf": [
                {"$ref": f"#/$defs/{base_name}"},
                {"not": {"required": required_slots}}
            ]
        }
        defs[link_element_name] = link_element_def

        # icon_link_element: base + requires icon-specific slots + restricts rel
        icon_element_name = f"icon_{cls_name.lower()}_element"
        icon_constraints: dict[str, Any] = {
            "type": "object",
            "required": required_slots,
        }
        if rel_value:
            icon_constraints["properties"] = {
                ld.discriminator_slot: {"enum": [rel_value]}
            }
        icon_element_def = {
            "allOf": [
                {"$ref": f"#/$defs/{base_name}"},
                icon_constraints,
            ]
        }
        defs[icon_element_name] = icon_element_def

        del defs[cls_name]

        # Update Thing-level links ref to point to discriminated variants
        thing_props = schema.get('properties', {})
        if 'links' in thing_props:
            links_prop = thing_props['links']
            if isinstance(links_prop, dict) and 'items' in links_prop:
                links_prop['items'] = {"oneOf": [
                    {"$ref": f"#/$defs/{link_element_name}"},
                    {"$ref": f"#/$defs/{icon_element_name}"},
                ]}


# ---------------------------------------------------------------------------
# Transform: merge class properties (e.g. DataSchema → PropertyAffordance)
# ---------------------------------------------------------------------------

def _merge_class_properties(schema: dict, config: TransformConfig) -> None:
    defs = schema.get('$defs', {})

    for target_cls, source_classes in config.merge_from.items():
        if target_cls not in defs:
            continue

        target_def = defs[target_cls]
        target_props = target_def.get('properties', {})

        for source_cls in source_classes:
            if source_cls not in defs:
                continue
            source_props = defs[source_cls].get('properties', {})
            for prop_name, prop_schema in source_props.items():
                if prop_name not in target_props:
                    target_props[prop_name] = prop_schema


# ---------------------------------------------------------------------------
# Transform: dict-style slots
# ---------------------------------------------------------------------------

def _fix_dict_style_slots(schema: dict, config: TransformConfig) -> None:
    thing_props = schema.get('properties', {})
    defs = schema.get('$defs', {})

    for ds in config.dict_style_slots:
        if ds.slot_name not in thing_props:
            continue

        # Resolve ref — the ref names a LinkML class, find the actual def name
        ref_target = ds.ref
        if ref_target not in defs:
            # Try __identifier_optional variant
            alt = f"{ref_target}__identifier_optional"
            if alt in defs:
                ref_target = alt

        new_prop: dict[str, Any] = {
            "type": "object",
            "additionalProperties": {"$ref": f"#/$defs/{ref_target}"},
        }
        if ds.min_properties:
            new_prop["minProperties"] = ds.min_properties

        # Preserve description from original
        original = thing_props[ds.slot_name]
        if 'description' in original:
            new_prop['description'] = original['description']

        thing_props[ds.slot_name] = new_prop


# ---------------------------------------------------------------------------
# Transform: strip spurious top-level type from oneOf properties
# ---------------------------------------------------------------------------

def _fix_oneof_type_conflict(schema: dict) -> None:
    """LinkML adds a top-level ``type`` alongside ``oneOf`` for exactly_one_of
    slots. That conflicts when the branches have different types (e.g. string
    vs array), so strip the top-level ``type`` from any property that has
    ``oneOf``.
    """
    def _fix_in_props(props: dict) -> None:
        for prop in props.values():
            if isinstance(prop, dict) and 'oneOf' in prop:
                prop.pop('type', None)

    _fix_in_props(schema.get('properties', {}))
    for defn in schema.get('$defs', {}).values():
        if isinstance(defn, dict) and 'properties' in defn:
            _fix_in_props(defn['properties'])


# ---------------------------------------------------------------------------
# Transform: simplify exclusiveMinimum pattern
# ---------------------------------------------------------------------------

def _simplify_exclusive_minimum(schema: dict) -> None:
    """Convert LinkML's none_of/minimum_value pattern to exclusiveMinimum.

    LinkML generates ``{minimum: 0, not: {anyOf: [{const: 0}]}}`` for
    ``minimum_value: 0`` + ``none_of: [{equals_number: 0}]``.
    Simplify to ``{exclusiveMinimum: 0}``.
    """
    def _walk(obj: Any) -> Any:
        if isinstance(obj, dict):
            if ('minimum' in obj and 'not' in obj
                    and isinstance(obj['not'], dict)
                    and 'anyOf' in obj['not']):
                any_of = obj['not']['anyOf']
                if (len(any_of) == 1 and isinstance(any_of[0], dict)
                        and 'const' in any_of[0]
                        and any_of[0]['const'] == obj['minimum']):
                    val = obj.pop('minimum')
                    del obj['not']
                    obj['exclusiveMinimum'] = val
            for key in list(obj.keys()):
                obj[key] = _walk(obj[key])
        elif isinstance(obj, list):
            return [_walk(item) for item in obj]
        return obj

    _walk(schema)


# ---------------------------------------------------------------------------
# Cleanup: remove excluded, __identifier_optional, standalone enums
# ---------------------------------------------------------------------------

def _remove_excluded_defs(schema: dict, sv: SchemaView, config: TransformConfig) -> None:
    defs = schema.get('$defs', {})
    to_remove = set()

    # Explicitly excluded classes
    to_remove.update(config.excluded_classes)

    # __identifier_optional variants
    for name in list(defs.keys()):
        if name.endswith('__identifier_optional'):
            to_remove.add(name)

    # Standalone enum definitions (LinkML generates them as separate $defs)
    for enum_name in sv.all_enums():
        if enum_name in defs:
            to_remove.add(enum_name)

    # The 'Any' definition — not needed in output
    to_remove.add('Any')

    # 'Thing' def inside $defs (if present) — Thing is the top-level schema
    to_remove.add('Thing')

    # InteractionAffordance — abstract, not directly referenced
    to_remove.add('InteractionAffordance')

    for name in to_remove:
        if name in defs:
            del defs[name]
            logger.debug(f"Removed def: {name}")


# ---------------------------------------------------------------------------
# Cleanup: strip metadata from definitions (description, title)
# ---------------------------------------------------------------------------

def _strip_def_metadata(schema: dict) -> None:
    defs = schema.get('$defs', {})
    for name, defn in defs.items():
        if isinstance(defn, dict):
            defn.pop('description', None)
            defn.pop('title', None)


# ---------------------------------------------------------------------------
# Cleanup: remove identifier slots from class defs
# ---------------------------------------------------------------------------

def _remove_identifier_slots(schema: dict, sv: SchemaView) -> None:
    """Remove identifier properties from class defs (they're internal to LinkML)."""
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


# ---------------------------------------------------------------------------
# Cleanup: resolve $refs (inline enums, fix paths, remove Any)
# ---------------------------------------------------------------------------

def _resolve_refs(schema: dict, sv: SchemaView) -> None:
    """Single-pass $ref resolution: inline enums, fix broken paths, remove Any."""
    valid_def_names = set(schema.get('$defs', {}).keys())

    enum_values: dict[str, list[str]] = {}
    for enum_name, enum_def in sv.all_enums().items():
        pvs = list(enum_def.permissible_values.keys()) if enum_def.permissible_values else []
        if pvs:
            enum_values[enum_name] = pvs

    def _extract_ref_name(ref: str) -> str | None:
        for prefix in ('#/$defs/', '#/definitions/'):
            if ref.startswith(prefix):
                return ref[len(prefix):]
        return None

    def _walk(obj: Any) -> Any:
        if isinstance(obj, dict):
            if '$ref' in obj:
                ref = obj['$ref']
                ref_name = _extract_ref_name(ref)

                if ref_name is not None:
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
                    elif not ref.startswith('#/$defs/'):
                        obj['$ref'] = f'#/$defs/{ref_name}'

            for key, val in list(obj.items()):
                obj[key] = _walk(val)
        elif isinstance(obj, list):
            return [_walk(item) for item in obj]
        return obj

    _walk(schema)


# ---------------------------------------------------------------------------
# Cleanup: remove top-level metadata noise
# ---------------------------------------------------------------------------

def _clean_top_level(schema: dict) -> None:
    schema.pop('metamodel_version', None)
    schema.pop('version', None)

    # Ensure required fields
    if 'required' in schema:
        req = schema['required']
        if 'name' in req:
            req.remove('name')


# ---------------------------------------------------------------------------
# Cleanup: fix anyOf wrapping in additionalProperties
# ---------------------------------------------------------------------------

def _fix_anyof_additional_props(schema: dict) -> None:
    """Fix anyOf patterns in additionalProperties generated by LinkML for
    identifier-keyed inlined maps. Replace with direct $ref."""

    def _walk(obj: Any) -> Any:
        if isinstance(obj, dict):
            if 'additionalProperties' in obj and isinstance(obj['additionalProperties'], dict):
                ap = obj['additionalProperties']
                if 'anyOf' in ap and isinstance(ap['anyOf'], list):
                    refs = [item for item in ap['anyOf']
                            if isinstance(item, dict) and '$ref' in item]
                    non_refs = [item for item in ap['anyOf']
                                if not (isinstance(item, dict) and '$ref' in item)]
                    # If there's exactly one $ref and the rest are null/string types,
                    # simplify to just the $ref
                    if len(refs) == 1:
                        null_or_simple = all(
                            isinstance(item, dict) and item.get('type') in ('null', 'string')
                            for item in non_refs
                        )
                        if null_or_simple:
                            obj['additionalProperties'] = refs[0]

            for key, val in list(obj.items()):
                obj[key] = _walk(val)
        elif isinstance(obj, list):
            return [_walk(item) for item in obj]
        return obj

    _walk(schema)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def post_process_jsonschema(raw_schema: dict, schema_view: SchemaView) -> dict:
    schema = copy.deepcopy(raw_schema)
    config = _read_annotations(schema_view)

    logger.info("JSON Schema postprocessor: reading annotations")
    logger.debug(f"  flatten_subclass_parents: {config.flatten_subclass_parents}")
    logger.debug(f"  oneof_dispatches: {[d.class_name for d in config.oneof_dispatches]}")
    logger.debug(f"  form_variants: {[f.class_name for f in config.form_variants]}")
    logger.debug(f"  link_discriminations: {[l.class_name for l in config.link_discriminations]}")
    logger.debug(f"  merge_from: {config.merge_from}")
    logger.debug(f"  dict_style_slots: {[d.slot_name for d in config.dict_style_slots]}")
    logger.debug(f"  extra_slots_classes: {config.extra_slots_classes}")

    # Order matters: structural transforms first, then cleanup
    _apply_additional_properties(schema, config)
    _flatten_subclasses(schema, schema_view, config)
    _merge_class_properties(schema, config)
    _build_oneof_dispatch(schema, schema_view, config)
    _build_form_variants(schema, config)
    _build_link_discrimination(schema, config)
    _fix_dict_style_slots(schema, config)
    _fix_oneof_type_conflict(schema)
    _simplify_exclusive_minimum(schema)
    _remove_identifier_slots(schema, schema_view)
    _remove_excluded_defs(schema, schema_view, config)
    _fix_anyof_additional_props(schema)
    _resolve_refs(schema, schema_view)
    _strip_def_metadata(schema)
    _clean_top_level(schema)

    return schema

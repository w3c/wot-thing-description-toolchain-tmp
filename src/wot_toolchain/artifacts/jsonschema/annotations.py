"""Reads the ``jsonschema_*`` class annotations of a schema into an ``Annotations`` config."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from linkml_runtime.utils.schemaview import SchemaView


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

    return config

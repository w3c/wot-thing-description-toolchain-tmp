"""Transforms that merge the direct subclasses of a class into it or replace it by a ``oneOf`` over them."""

from __future__ import annotations

import logging
from typing import Any

from linkml_runtime.utils.schemaview import SchemaView

from .annotations import Annotations

logger = logging.getLogger(__name__)


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

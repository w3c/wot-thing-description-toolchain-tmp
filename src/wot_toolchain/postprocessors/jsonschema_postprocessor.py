"""Annotation-driven post-processor for raw LinkML JSON Schema output.

Transforms the output of gen-jsonschema into the published JSON Schema, as requested by the schema's annotations.
"""

from __future__ import annotations

import copy
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from linkml_runtime.linkml_model.meta import ClassDefinition
from linkml_runtime.utils.schemaview import SchemaView

from ..errors import SchemaError
from ..schema_utils import annotation_tag_value as _get_annotation_value

logger = logging.getLogger(__name__)

LINKML_ANY_URI = "https://w3id.org/linkml/Any"


@dataclass
class OneOfDispatchConfig:
    """A class whose definition becomes a ``oneOf`` of its direct subclasses (``jsonschema_oneof_dispatch``)."""

    class_name: str
    discriminator: str
    include_unknown: bool = False


@dataclass
class EnumSubsetPartitionConfig:
    """A class split into one variant per subset of an enum slot's values (``jsonschema_enum_subset_partition``)."""

    class_name: str
    slot_name: str
    enum_name: str
    subsets: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class FormSubsetNarrowConfig:
    """A slot whose array items narrow to one subset variant of a partitioned class (``jsonschema_form_subset``)."""

    class_name: str
    slot_name: str
    subset_name: str
    partition_class: str


@dataclass
class TransformConfig:
    """The transforms requested by the ``jsonschema_*`` annotations of a schema."""

    flatten_subclass_parents: list[str] = field(default_factory=list)
    oneof_dispatches: list[OneOfDispatchConfig] = field(default_factory=list)
    enum_subset_partitions: list[EnumSubsetPartitionConfig] = field(default_factory=list)
    form_subset_narrows: list[FormSubsetNarrowConfig] = field(default_factory=list)
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


def _read_annotations(sv: SchemaView) -> TransformConfig:
    config = TransformConfig()

    for cls_name, cls_def in sv.all_classes().items():
        if _get_annotation_value(cls_def, "jsonschema_flatten_subclasses"):
            config.flatten_subclass_parents.append(cls_name)

        oneof = _get_annotation_value(cls_def, "jsonschema_oneof_dispatch")
        if oneof:
            config.oneof_dispatches.append(
                OneOfDispatchConfig(
                    class_name=cls_name,
                    discriminator=oneof["discriminator"],
                    include_unknown=oneof.get("include_unknown", False),
                )
            )

        esp = _get_annotation_value(cls_def, "jsonschema_enum_subset_partition")
        if esp:
            enum_name = esp["enum"]
            slot_name = esp["slot"]
            enum_def = sv.get_enum(enum_name)
            subsets: dict[str, list[str]] = {}
            if enum_def and enum_def.permissible_values:
                for pv_name, pv in enum_def.permissible_values.items():
                    for subset in pv.in_subset or []:
                        subsets.setdefault(subset, []).append(pv_name)
            config.enum_subset_partitions.append(
                EnumSubsetPartitionConfig(
                    class_name=cls_name,
                    slot_name=slot_name,
                    enum_name=enum_name,
                    subsets=subsets,
                )
            )

        if _get_annotation_value(cls_def, "jsonschema_exclude"):
            config.excluded_classes.append(cls_name)

    for cls_name, cls_def in sv.all_classes().items():
        if not cls_def.slot_usage:
            continue
        for slot_name, slot_usage in cls_def.slot_usage.items():
            subset_val = _get_annotation_value(slot_usage, "jsonschema_form_subset")
            if subset_val:
                partition_class = None
                for esp in config.enum_subset_partitions:
                    if subset_val in esp.subsets:
                        partition_class = esp.class_name
                        break
                if partition_class:
                    config.form_subset_narrows.append(
                        FormSubsetNarrowConfig(
                            class_name=cls_name,
                            slot_name=slot_name,
                            subset_name=subset_val,
                            partition_class=partition_class,
                        )
                    )

    return config


def _flatten_subclasses(schema: dict, sv: SchemaView, config: TransformConfig) -> None:
    defs = schema.get("$defs", {})

    for parent_name in config.flatten_subclass_parents:
        if parent_name not in defs:
            continue

        parent_def = defs[parent_name]
        parent_props = parent_def.get("properties", {})
        subclasses_to_remove = []
        new_props: dict[str, Any] = {}

        for cls_name, cls_def in sv.all_classes().items():
            if cls_def.is_a == parent_name and cls_name in defs:
                sub_def = defs[cls_name]
                sub_props = sub_def.get("properties", {})
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
                    target_props = defs[cls_name].get("properties", {})
                    for prop_name, prop_schema in new_props.items():
                        if prop_name not in target_props:
                            target_props[prop_name] = prop_schema
                    logger.debug(f"Propagated flattened props to mixin user {cls_name}")


def _build_oneof_dispatch(schema: dict, sv: SchemaView, config: TransformConfig) -> None:
    defs = schema.get("$defs", {})

    for dispatch in config.oneof_dispatches:
        cls_name = dispatch.class_name
        if cls_name not in defs:
            continue

        subclass_refs: list[dict[str, Any]] = []
        for sub_name, sub_def in sv.all_classes().items():
            if sub_def.is_a == cls_name and sub_name in defs:
                subclass_refs.append({"$ref": f"#/$defs/{sub_name}"})

        one_of_list = sorted(subclass_refs, key=lambda x: x["$ref"])

        # W3C additionalSecurityScheme: a prefixed scheme, so the catch-all does not overlap the known schemes
        # (KNOWN_LINKML_GAPS.md #9).
        if dispatch.include_unknown:
            one_of_list.append(
                {
                    "type": "object",
                    "description": f"Additional {cls_name} not covered by known subclasses",
                    "properties": {dispatch.discriminator: {"type": "string", "pattern": ".+:.*"}},
                    "required": [dispatch.discriminator],
                }
            )

        defs[cls_name] = {"oneOf": one_of_list}


def _build_enum_subset_partitions(schema: dict, config: TransformConfig) -> None:
    defs = schema.get("$defs", {})

    for esp in config.enum_subset_partitions:
        cls_name = esp.class_name
        if cls_name not in defs:
            continue

        original = defs[cls_name]
        original_props = original.get("properties", {})
        original_required = original.get("required", [])

        base_props = {k: v for k, v in original_props.items() if k != esp.slot_name}
        base_def = {
            "type": "object",
            "properties": base_props,
            "required": original_required,
            "additionalProperties": original.get("additionalProperties", True),
        }
        base_name = f"{cls_name}_element_base"
        defs[base_name] = base_def

        variant_refs = []
        for subset_name, ops in esp.subsets.items():
            variant_def_name = f"{cls_name}_element_{subset_name}"
            op_schema = {"oneOf": [{"const": op} for op in ops] + [{"type": "array", "items": {"enum": ops}}]}
            variant_def = {
                "allOf": [
                    {"$ref": f"#/$defs/{base_name}"},
                    {
                        "type": "object",
                        "properties": {esp.slot_name: op_schema},
                    },
                ]
            }
            defs[variant_def_name] = variant_def
            variant_refs.append({"$ref": f"#/$defs/{variant_def_name}"})

        defs[cls_name] = {"oneOf": variant_refs}


def _narrow_slot_items(props: dict, slot_name: str, items: dict) -> None:
    """Replace the array ``items`` of ``slot_name`` in ``props``, if that slot is an array property.

    Args:
        props: The ``properties`` of a class definition or of the top-level schema.
        slot_name: The name of the slot to narrow.
        items: The new ``items`` schema.
    """
    slot_prop = props.get(slot_name)
    if isinstance(slot_prop, dict) and "items" in slot_prop:
        slot_prop["items"] = items


def _narrow_form_subsets(schema: dict, sv: SchemaView, config: TransformConfig) -> None:
    """Narrow the array items of each ``jsonschema_form_subset`` slot to its subset variant.

    The tree root class is also narrowed in the top-level ``properties``, which hold the tree root's content.

    Args:
        schema: The JSON Schema being post-processed, after its enum-subset partitions are built.
        sv: The schema view of the LinkML schema.
        config: The transforms read from the ``jsonschema_*`` annotations.
    """
    defs = schema.get("$defs", {})
    for narrow in config.form_subset_narrows:
        base_name = f"{narrow.partition_class}_element_base"
        variant_def_name = f"{narrow.partition_class}_element_{narrow.subset_name}"
        if variant_def_name not in defs or base_name not in defs:
            continue
        narrowed_items = {"$ref": f"#/$defs/{variant_def_name}"}

        cls_def = defs.get(narrow.class_name)
        if isinstance(cls_def, dict) and "properties" in cls_def:
            _narrow_slot_items(cls_def["properties"], narrow.slot_name, narrowed_items)
        if sv.get_class(narrow.class_name).tree_root:
            _narrow_slot_items(schema.get("properties", {}), narrow.slot_name, narrowed_items)


def _dedup_oneof(schema: dict) -> None:
    """Deduplicate identical oneOf branches (e.g. string vs langString both map to {"type":"string"})."""

    def _dedup(obj: dict) -> None:
        if "oneOf" not in obj or not isinstance(obj["oneOf"], list):
            return
        unique: list[dict] = []
        for item in obj["oneOf"]:
            if item not in unique:
                unique.append(item)
        if len(unique) == 1:
            obj.pop("oneOf")
            obj.update(unique[0])
        elif len(unique) < len(obj["oneOf"]):
            obj["oneOf"] = unique

    _walk_schema(schema, _dedup)


def _normalize_types(schema: dict) -> None:
    def _strip_oneof_type(props: dict) -> None:
        for prop in props.values():
            if isinstance(prop, dict) and "oneOf" in prop:
                prop.pop("type", None)

    _strip_oneof_type(schema.get("properties", {}))
    for defn in schema.get("$defs", {}).values():
        if isinstance(defn, dict) and "properties" in defn:
            _strip_oneof_type(defn["properties"])


def _simplify_exclusive_minimum(schema: dict) -> None:
    def _fix(obj: dict) -> None:
        if "minimum" in obj and "not" in obj and isinstance(obj["not"], dict) and "anyOf" in obj["not"]:
            any_of = obj["not"]["anyOf"]
            if (
                len(any_of) == 1
                and isinstance(any_of[0], dict)
                and "const" in any_of[0]
                and any_of[0]["const"] == obj["minimum"]
            ):
                val = obj.pop("minimum")
                del obj["not"]
                obj["exclusiveMinimum"] = val

    _walk_schema(schema, _fix)


def _extract_ref_name(ref: str) -> str | None:
    for prefix in ("#/$defs/", "#/definitions/"):
        if ref.startswith(prefix):
            return ref[len(prefix) :]
    return None


def _is_linkml_any(sv: SchemaView, cls_def: ClassDefinition) -> bool:
    """Return whether the class stands for ``linkml:Any``, written as a CURIE or as the expanded URI."""
    return bool(cls_def.class_uri) and sv.expand_curie(str(cls_def.class_uri)) == LINKML_ANY_URI


def _drop_candidate_defs(defs: dict, sv: SchemaView, config: TransformConfig) -> set[str]:
    """Return the defs of classes with no standalone use in the published JSON Schema.

    These are classes for ``linkml:Any``, the tree root (its content is the top-level schema), abstract classes, and
    enum-subset-partitioned classes (replaced by their per-subset variants).

    Args:
        defs: The ``$defs`` of the schema being post-processed.
        sv: The schema view of the LinkML schema.
        config: The transforms read from the ``jsonschema_*`` annotations.

    Returns:
        The names of the candidate defs present in ``defs``.
    """
    partitioned = {esp.class_name for esp in config.enum_subset_partitions}
    return {
        name
        for name, cls_def in sv.all_classes().items()
        if name in defs
        and (_is_linkml_any(sv, cls_def) or cls_def.tree_root or cls_def.abstract or name in partitioned)
    }


def _referenced_def_names(obj: Any) -> set[str]:
    """Return the names of all defs that a ``$ref`` anywhere in ``obj`` points to.

    Args:
        obj: A JSON Schema fragment.

    Returns:
        The referenced def names.
    """
    if isinstance(obj, list):
        return set().union(*(_referenced_def_names(item) for item in obj))
    if not isinstance(obj, dict):
        return set()
    names = set().union(*(_referenced_def_names(value) for value in obj.values()))
    ref = obj.get("$ref")
    ref_name = _extract_ref_name(ref) if isinstance(ref, str) else None
    if ref_name is not None:
        names.add(ref_name)
    return names


def _unreferenced_candidates(schema: dict, candidates: set[str]) -> set[str]:
    """Return the candidate defs that no ``$ref`` outside the dropped defs points to.

    Starts from dropping every candidate and keeps each one still referenced, until no kept def references a dropped
    one, so dropping the result can never leave a dangling ``$ref``.

    Args:
        schema: The JSON Schema being post-processed.
        candidates: The names of the defs that may be dropped.

    Returns:
        The names of the candidates that can be dropped.
    """
    top_level = {key: value for key, value in schema.items() if key != "$defs"}
    dropped = set(candidates)
    while True:
        kept_defs = {name: defn for name, defn in schema.get("$defs", {}).items() if name not in dropped}
        still_referenced = dropped & _referenced_def_names([top_level, kept_defs])
        if not still_referenced:
            return dropped
        dropped -= still_referenced


def _remove_unreferenced_candidate_defs(schema: dict, sv: SchemaView, config: TransformConfig) -> None:
    """Delete the defs of drop-candidate classes that no ``$ref`` in the schema points to.

    Args:
        schema: The JSON Schema being post-processed, after its ``$ref`` values are resolved.
        sv: The schema view of the LinkML schema.
        config: The transforms read from the ``jsonschema_*`` annotations.
    """
    defs = schema.get("$defs", {})
    for name in _unreferenced_candidates(schema, _drop_candidate_defs(defs, sv, config)):
        del defs[name]
        logger.debug(f"Removed unreferenced def: {name}")


def _remove_excluded_defs(schema: dict, sv: SchemaView, config: TransformConfig) -> None:
    defs = schema.get("$defs", {})
    to_remove = set()

    to_remove.update(config.excluded_classes)

    for name in list(defs.keys()):
        if name.endswith("__identifier_optional"):
            to_remove.add(name)

    for enum_name in sv.all_enums():
        if enum_name in defs:
            to_remove.add(enum_name)

    for name in to_remove:
        if name in defs:
            del defs[name]
            logger.debug(f"Removed def: {name}")


def _remove_identifier_slots(schema: dict, sv: SchemaView) -> None:
    """Drop identifier slots from the properties and required lists of each class definition.

    Definitions that are not LinkML classes (e.g. generated ``__identifier_optional`` variants) are left untouched.

    Raises:
        SchemaError: If the slots of a class definition cannot be resolved.
    """
    defs = schema.get("$defs", {})
    all_classes = sv.all_classes()

    for cls_name in list(defs.keys()):
        defn = defs[cls_name]
        if not isinstance(defn, dict) or "properties" not in defn or cls_name not in all_classes:
            continue

        try:
            induced_slots = sv.class_induced_slots(cls_name)
        except ValueError as exc:
            raise SchemaError(f"class {cls_name!r}: cannot resolve its slots: {exc}") from exc

        for slot in induced_slots:
            if getattr(slot, "identifier", False) and slot.name in defn["properties"]:
                defn["properties"].pop(slot.name)
                req = defn.get("required", [])
                if slot.name in req:
                    req.remove(slot.name)
                if not req:
                    defn.pop("required", None)


def _resolve_refs(schema: dict, sv: SchemaView) -> None:
    valid_def_names = set(schema.get("$defs", {}).keys())

    enum_values: dict[str, list[str]] = {}
    for enum_name, enum_def in sv.all_enums().items():
        pvs = list(enum_def.permissible_values.keys()) if enum_def.permissible_values else []
        if pvs:
            enum_values[enum_name] = pvs

    any_class_names = {name for name, cls_def in sv.all_classes().items() if _is_linkml_any(sv, cls_def)}

    def _is_string_map(cls_name: str | None) -> bool:
        if cls_name is None or cls_name not in sv.all_classes():
            return False
        try:
            slots = sv.class_induced_slots(cls_name)
        except ValueError as exc:
            raise SchemaError(f"class {cls_name!r}: cannot resolve its slots: {exc}") from exc
        non_id = [s for s in slots if not getattr(s, "identifier", False)]
        return len(slots) == 2 and len(non_id) == 1 and non_id[0].range == "string"

    def _fix_additional_props_anyof(obj: dict) -> None:
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
                if _is_string_map(_extract_ref_name(base)):
                    obj["additionalProperties"] = {"type": "string"}
                else:
                    obj["additionalProperties"] = {"$ref": base}
                return

        refs = [i for i in items if isinstance(i, dict) and "$ref" in i]
        non_refs = [i for i in items if not (isinstance(i, dict) and "$ref" in i)]
        if len(refs) == 1 and all(isinstance(i, dict) and i.get("type") in ("null", "string") for i in non_refs):
            obj["additionalProperties"] = refs[0]

    def _resolve(obj: dict) -> dict | None:
        _fix_additional_props_anyof(obj)

        if "$ref" not in obj:
            return None
        ref = obj["$ref"]
        ref_name = _extract_ref_name(ref)
        if ref_name is None:
            return None

        if ref_name in enum_values:
            result = {"type": "string", "enum": enum_values[ref_name]}
            if "description" in obj:
                result["description"] = obj["description"]
            return result

        if ref_name in any_class_names:
            del obj["$ref"]
        elif ref_name not in valid_def_names:
            base = ref_name.replace("__identifier_optional", "")
            if base in valid_def_names:
                obj["$ref"] = f"#/$defs/{base}"
        elif not ref.startswith("#/$defs/"):
            obj["$ref"] = f"#/$defs/{ref_name}"

        return None

    _walk_schema(schema, _resolve)


def _clean_metadata(schema: dict, sv: SchemaView) -> None:
    for defn in schema.get("$defs", {}).values():
        if isinstance(defn, dict):
            defn.pop("description", None)
            defn.pop("title", None)

    schema.pop("metamodel_version", None)
    if sv.schema.version:
        schema["version"] = sv.schema.version
    else:
        schema.pop("version", None)


def post_process_jsonschema(raw_schema: dict, schema_view: SchemaView) -> dict:
    """Return a transformed copy of raw LinkML JSON Schema output; ``raw_schema`` is not modified.

    Applies the transforms requested by the ``jsonschema_*`` annotations of ``schema_view`` and fixed clean-ups,
    and takes ``version`` and ``title`` from ``schema_view``.
    """
    schema = copy.deepcopy(raw_schema)
    config = _read_annotations(schema_view)

    logger.info("JSON Schema postprocessor: reading annotations")
    logger.debug(f"  flatten_subclass_parents: {config.flatten_subclass_parents}")
    logger.debug(f"  oneof_dispatches: {[d.class_name for d in config.oneof_dispatches]}")
    logger.debug(f"  enum_subset_partitions: {[e.class_name for e in config.enum_subset_partitions]}")
    logger.debug(f"  form_subset_narrows: {[n.class_name for n in config.form_subset_narrows]}")

    _flatten_subclasses(schema, schema_view, config)
    _build_oneof_dispatch(schema, schema_view, config)
    _build_enum_subset_partitions(schema, config)
    _narrow_form_subsets(schema, schema_view, config)
    _dedup_oneof(schema)
    _normalize_types(schema)
    _simplify_exclusive_minimum(schema)
    _remove_identifier_slots(schema, schema_view)
    _remove_excluded_defs(schema, schema_view, config)
    _resolve_refs(schema, schema_view)
    # After _resolve_refs: it erases refs to linkml:Any defs and drops anyOf branches that still reference candidates.
    _remove_unreferenced_candidate_defs(schema, schema_view, config)
    _clean_metadata(schema, schema_view)

    if schema_view.schema.title:
        schema["title"] = schema_view.schema.title

    return schema

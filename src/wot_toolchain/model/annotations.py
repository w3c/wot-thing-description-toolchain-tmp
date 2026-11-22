"""Shape checks for the jsonschema_, jsonld_ and spec_ annotations whose readers need a specific value shape."""

from collections.abc import Callable, Iterator, Mapping
from typing import Any

from linkml_runtime.linkml_model.meta import ClassDefinition, EnumDefinition, SchemaDefinition, SlotDefinition
from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.errors import SchemaError
from wot_toolchain.schema_utils import annotation_tag_value, get_schema

type _Check = Callable[[Any], str | None]
type _Element = ClassDefinition | SlotDefinition | EnumDefinition


def _string(value: Any) -> str | None:
    return None if isinstance(value, str) else f"expected a string, got {type(value).__name__}"


def _mapping(required: Mapping[str, type], optional: Mapping[str, type]) -> _Check:
    def check(value: Any) -> str | None:
        if not isinstance(value, dict):
            return f"expected a mapping, got {type(value).__name__}"
        problems = [f"{key!r} must be a {kind.__name__}" for key, kind in required.items() if not _is(value, key, kind)]
        problems += [
            f"{key!r} must be a {kind.__name__}"
            for key, kind in optional.items()
            if key in value and not _is(value, key, kind)
        ]
        return "; ".join(problems) or None

    return check


def _is(record: dict[str, Any], key: str, kind: type) -> bool:
    return isinstance(record.get(key), kind)


def _blocks(value: Any) -> str | None:
    # generators/respec.py _as_block_list: a mapping or a list of mappings; anything else is dropped silently.
    if isinstance(value, dict) or (isinstance(value, list) and all(isinstance(block, dict) for block in value)):
        return None
    return "expected a mapping or a list of mappings"


_CHECKS: Mapping[str, _Check] = {
    "jsonschema_oneof_dispatch": _mapping({"discriminator": str}, {"include_unknown": bool}),
    "jsonschema_enum_subset_partition": _mapping({"enum": str, "slot": str}, {}),
    "jsonschema_form_subset": _string,
    "jsonld_index": _string,
    "jsonld_container": _string,
    "jsonld_context": _string,
    "spec_description": _string,
    "spec_content": _blocks,
    "spec_intro_content": _blocks,
    "spec_subsections": _blocks,
    "spec_type_values": _mapping({}, {"mode": str, "values": list}),
}


def _annotated_elements(schema: SchemaDefinition) -> Iterator[tuple[str, str, _Element]]:
    for class_name, class_def in schema.classes.items():
        yield "class", str(class_name), class_def
        for slot_name, usage in (class_def.slot_usage or {}).items():
            yield "slot_usage", f"{class_name}.{slot_name}", usage
        for slot_name, attribute in (class_def.attributes or {}).items():
            yield "attribute", f"{class_name}.{slot_name}", attribute
    for slot_name, slot_def in schema.slots.items():
        yield "slot", str(slot_name), slot_def
    for enum_name, enum_def in schema.enums.items():
        yield "enum", str(enum_name), enum_def


def validate_annotations(schema_view: SchemaView) -> None:
    """Check the shape of every annotation listed in ``_CHECKS``; unknown and absent annotations are legal.

    Raises:
        SchemaError: One or more annotations are malformed; the message lists each with element kind, element name
            and annotation key.
    """
    problems = [
        f"{kind} {name!r}: annotation {key!r}: {problem}"
        for kind, name, element in _annotated_elements(get_schema(schema_view))
        for key in element.annotations or {}
        if (check := _CHECKS.get(str(key))) and (problem := check(annotation_tag_value(element, str(key))))
    ]
    if problems:
        raise SchemaError(f"{len(problems)} malformed annotation(s):\n  " + "\n  ".join(problems))

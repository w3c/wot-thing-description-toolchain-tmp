"""The transforms a schema requests through its ``jsonschema_*`` annotations."""

from dataclasses import dataclass, field

from linkml_runtime.utils.schemaview import SchemaView

from ...schema_utils import annotation_tag_value as _get_annotation_value


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
    # Class whose content is the top-level schema; set by the caller, not by an annotation.
    top_class: str | None = None


def read_annotations(sv: SchemaView) -> TransformConfig:
    """Return the transforms requested by the ``jsonschema_*`` annotations of the schema of ``sv``."""
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

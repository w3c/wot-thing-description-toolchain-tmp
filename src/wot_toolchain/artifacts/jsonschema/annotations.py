"""What the JSON Schema post-steps read from the ``jsonschema_*`` annotations of a schema."""

from dataclasses import dataclass, field

from linkml_runtime.utils.schemaview import SchemaView

from ...schema_utils import annotation_tag_value

ENUM_SUBSET_PARTITION = "jsonschema_enum_subset_partition"


@dataclass
class TransformConfig:
    """The classes the post-steps treat specially."""

    # Classes the generator states as a oneOf of per-subset variants (``jsonschema_enum_subset_partition``).
    partitioned_classes: list[str] = field(default_factory=list)
    # Class whose content is the top-level schema; set by the caller, not by an annotation.
    top_class: str | None = None


def read_annotations(sv: SchemaView) -> TransformConfig:
    """Return the classes of the schema of ``sv`` annotated ``jsonschema_enum_subset_partition``."""
    partitioned = [name for name, cls in sv.all_classes().items() if annotation_tag_value(cls, ENUM_SUBSET_PARTITION)]
    return TransformConfig(partitioned_classes=partitioned)

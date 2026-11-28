"""Ordered post-processing transforms that turn raw LinkML JSON Schema output into the published JSON Schema."""

import copy
import logging
from typing import Any

from linkml_runtime.utils.schemaview import SchemaView

from .annotations import read_annotations
from .cleanups import (
    clean_metadata,
)
from .pruning import remove_excluded_defs, remove_unreferenced_candidate_defs
from ..transforms import Transform, TransformKind, run_transforms

logger = logging.getLogger(__name__)

JSONSCHEMA_TRANSFORMS: tuple[Transform, ...] = (
    Transform(
        name="remove_excluded_defs",
        kind=TransformKind.COSMETIC,
        reason="Removes leftover LinkML defs: __identifier_optional defs.",
        apply=remove_excluded_defs,
    ),
    Transform(
        name="remove_unreferenced_candidate_defs",
        kind=TransformKind.COSMETIC,
        reason="Drops defs that nothing references any more (linkml:Any, the top class, partitioned classes), "
        "based on schema markers rather than hard-coded names.",
        apply=remove_unreferenced_candidate_defs,
    ),
    Transform(
        name="clean_metadata",
        kind=TransformKind.COSMETIC,
        reason="Removes per-def description/title.",
        apply=lambda schema, sv, config: clean_metadata(schema),
    ),
)


def post_process_jsonschema(
    raw_schema: dict[str, Any], schema_view: SchemaView, top_class: str | None = None
) -> dict[str, Any]:
    """Return a transformed copy of raw LinkML JSON Schema output; ``raw_schema`` is not modified.

    Applies the transforms requested by the ``jsonschema_*`` annotations of ``schema_view`` and fixed clean-ups,
    and takes ``title`` from ``schema_view``. ``top_class`` names the class whose content is the
    top-level schema; its own def is dropped when nothing references it.
    """
    schema = copy.deepcopy(raw_schema)
    config = read_annotations(schema_view)
    config.top_class = top_class

    logger.info("JSON Schema postprocessor: reading annotations")
    logger.debug(f"  partitioned_classes: {config.partitioned_classes}")

    run_transforms(JSONSCHEMA_TRANSFORMS, schema, schema_view, config)

    if schema_view.schema.title:
        schema["title"] = schema_view.schema.title

    return schema

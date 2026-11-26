"""Transform that deletes the definitions of excluded classes, enums and identifier-optional variants."""

from __future__ import annotations

import logging

from linkml_runtime.utils.schemaview import SchemaView

from .annotations import Annotations

logger = logging.getLogger(__name__)


def _remove_excluded_defs(schema: dict, sv: SchemaView, config: Annotations) -> None:
    defs = schema.get('$defs', {})
    to_remove = set()

    for name in list(defs.keys()):
        if name.endswith('__identifier_optional'):
            to_remove.add(name)

    for enum_name in sv.all_enums():
        if enum_name in defs:
            to_remove.add(enum_name)

    to_remove.add('Any')

    for name in to_remove:
        if name in defs:
            del defs[name]
            logger.debug(f"Removed def: {name}")

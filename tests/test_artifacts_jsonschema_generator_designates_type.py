"""WotJsonSchemaGenerator ignores designates_type itself and leaves the schema it is handed untouched."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.artifacts.jsonschema.generator import WotJsonSchemaGenerator
from wot_toolchain.artifacts.jsonschema.options import JsonSchemaOptions

DESIGNATOR = "    designates_type: true\n"

# ``kind`` is an enum-ranged designator (upstream raises on it); ``part`` is an inlined
# reference to a class carrying it (upstream would expand the range to its descendants).
SCHEMA = f"""
id: https://example.org/probe
name: probe
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/ex#
default_prefix: ex
imports: [linkml:types]
enums:
  Kind:
    permissible_values:
      base: {{}}
      sub: {{}}
slots:
  kind:
    range: Kind
{DESIGNATOR}  part:
    range: Base
    inlined: true
classes:
  Base:
    slots: [kind]
  Sub:
    is_a: Base
  Holder:
    slots: [part]
"""


def _view(tmp_path: Path, name: str, text: str) -> SchemaView:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return SchemaView(str(path))


def _generate(view: SchemaView) -> dict[str, Any]:
    generator = WotJsonSchemaGenerator.from_options(view.schema, JsonSchemaOptions())
    raw: dict[str, Any] = json.loads(generator.serialize())
    return raw


def test_designator_schema_generates_as_if_the_flag_were_absent(tmp_path: Path) -> None:
    assert DESIGNATOR in SCHEMA
    with_flag = _generate(_view(tmp_path, "probe.yaml", SCHEMA))
    without_flag = _generate(_view(tmp_path, "plain.yaml", SCHEMA.replace(DESIGNATOR, "")))
    assert with_flag == without_flag


def test_no_type_designator_constraint_is_emitted(tmp_path: Path) -> None:
    defs = _generate(_view(tmp_path, "probe.yaml", SCHEMA))["$defs"]
    assert defs["Base"]["properties"]["kind"] == {"$ref": "#/$defs/Kind"}
    assert defs["Holder"]["properties"]["part"] == {"$ref": "#/$defs/Base"}


def test_generation_leaves_the_schema_view_flag_set(tmp_path: Path) -> None:
    view = _view(tmp_path, "probe.yaml", SCHEMA)
    _generate(view)
    assert view.schema.slots["kind"].designates_type is True
    assert view.induced_slot("kind", "Base").designates_type is True

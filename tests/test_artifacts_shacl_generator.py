import copy
import dataclasses
from pathlib import Path

import pytest
from linkml.generators.shaclgen import ShaclGenerator
from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.artifacts.shacl.generator import WotShaclGenerator
from wot_toolchain.artifacts.shacl.options import ShaclOptions

ROOT_SCHEMA = """\
id: https://example.org/root
name: root
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/
default_prefix: ex
default_range: string
imports:
  - linkml:types
  - other
classes:
  Thing:
    attributes:
      title:
        required: true
      part:
        range: Part
"""

OTHER_SCHEMA = """\
id: https://example.org/other
name: other
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/
default_prefix: ex
default_range: string
imports:
  - linkml:types
classes:
  Part:
    attributes:
      label:
"""

PART_SHAPE = "ex:PartShape a sh:NodeShape"
THING_SHAPE = "ex:ThingShape a sh:NodeShape"


@pytest.fixture
def schema(tmp_path: Path) -> object:
    (tmp_path / "root.yaml").write_text(ROOT_SCHEMA, encoding="utf-8")
    (tmp_path / "other.yaml").write_text(OTHER_SCHEMA, encoding="utf-8")
    return SchemaView(str(tmp_path / "root.yaml")).schema


def _upstream(schema: object, **kwargs: object) -> str:
    return ShaclGenerator(copy.deepcopy(schema), mergeimports=False, suffix="Shape", **kwargs).serialize()


def _wot(schema: object, options: ShaclOptions) -> str:
    return WotShaclGenerator.from_options(copy.deepcopy(schema), options).serialize()


def test_options_are_frozen_with_exactly_two_fields() -> None:
    options = ShaclOptions()
    assert [f.name for f in dataclasses.fields(ShaclOptions)] == ["only_root_schema_classes", "open"]
    with pytest.raises(dataclasses.FrozenInstanceError):
        options.open = True  # type: ignore[misc]


def test_default_options_match_todays_pipeline_arguments(schema: object) -> None:
    out = _wot(schema, ShaclOptions())
    assert out == _upstream(schema, closed=True)
    assert "sh:closed true" in out
    assert PART_SHAPE in out


def test_open_matches_upstream_non_closed(schema: object) -> None:
    out = _wot(schema, ShaclOptions(open=True))
    assert out == _upstream(schema, closed=False)
    assert "sh:closed true" not in out
    assert "sh:closed false" in out


def test_only_root_schema_classes_drops_imported_class_shapes(schema: object) -> None:
    out = _wot(schema, ShaclOptions(only_root_schema_classes=True))
    assert out == _upstream(schema, closed=True, exclude_imports=True)
    assert THING_SHAPE in out
    assert PART_SHAPE not in out

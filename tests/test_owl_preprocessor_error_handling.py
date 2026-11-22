"""The OWL preprocessor must report unresolvable prefix declarations instead of silently skipping elements."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from wot_toolchain.artifacts.owl.preprocess import preprocess_for_gen_owl
from wot_toolchain.errors import SchemaError

_HEADER = """\
id: https://example.org/s
name: s
default_prefix: ex
{curi_maps}
prefixes:
  ex: https://example.org/s#
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
"""

# Each body reaches exactly one CURIE expansion site of the preprocessor before any other.
_SLOT_URI = """\
slots:
  foo:
    slot_uri: ex:bar
    range: string
classes:
  Thing:
    class_uri: ex:Thing
    slots: [foo]
"""

_ATTRIBUTE_SLOT_URI = """\
classes:
  Thing:
    class_uri: ex:Thing
    attributes:
      foo:
        slot_uri: ex:bar
        range: string
"""

_MIXIN_CLASS_URI = """\
classes:
  Named:
    mixin: true
    class_uri: ex:Named
  Thing:
    class_uri: ex:Thing
    mixins: [Named]
"""

_PERMISSIBLE_VALUE_MEANING = """\
enums:
  Color:
    enum_uri: ex:Color
    permissible_values:
      red:
        meaning: ex:Red
classes:
  Thing:
    class_uri: ex:Thing
"""

_OTHER_SCHEMA = """\
id: https://example.org/other
name: other
default_prefix: ex
prefixes:
  ex: https://example.org/s#
enums:
  Shade:
    enum_uri: ex:Shade
    permissible_values:
      dark: {}
"""

_CASES = {
    "slot_uri": (_SLOT_URI, "slot_uri 'ex:bar' of slot 'foo'"),
    "attribute_slot_uri": (_ATTRIBUTE_SLOT_URI, "slot_uri 'ex:bar' of attribute 'foo'"),
    "mixin_class_uri": (_MIXIN_CLASS_URI, "class_uri 'ex:Named' of mixin 'Named'"),
    "permissible_value_meaning": (_PERMISSIBLE_VALUE_MEANING, "meaning 'ex:Red' of permissible value 'Color.red'"),
}


def _write_schema(tmp_path: Path, body: str, *, curi_maps: str) -> Path:
    header = _HEADER.format(curi_maps=curi_maps)
    schema = tmp_path / "s.yaml"
    schema.write_text(header + textwrap.dedent(body), encoding="utf-8")
    return schema


@pytest.mark.parametrize("case", sorted(_CASES))
def test_unknown_curi_map_raises_schema_error_naming_schema_and_element(tmp_path: Path, case: str) -> None:
    body, element = _CASES[case]
    schema = _write_schema(tmp_path, body, curi_maps="default_curi_maps:\n  - no_such_map")

    with pytest.raises(SchemaError) as excinfo:
        preprocess_for_gen_owl(str(schema))

    message = str(excinfo.value)
    assert str(schema) in message
    assert element in message
    assert "Unknown prefix map: no_such_map" in message
    assert isinstance(excinfo.value.__cause__, ValueError)


@pytest.mark.parametrize("case", sorted(_CASES))
def test_same_schema_without_bad_curi_map_preprocesses(tmp_path: Path, case: str) -> None:
    body, _ = _CASES[case]
    schema = _write_schema(tmp_path, body, curi_maps="")

    assert "name: s" in preprocess_for_gen_owl(str(schema))


def test_slot_is_renamed_to_local_name_of_its_slot_uri(tmp_path: Path) -> None:
    schema = _write_schema(tmp_path, _SLOT_URI, curi_maps="")

    output = preprocess_for_gen_owl(str(schema))

    assert "  bar:\n" in output
    assert "  foo:\n" not in output


def _write_root_schema(tmp_path: Path, header_overrides: str, imports: str) -> Path:
    schema = tmp_path / "root.yaml"
    schema.write_text(
        textwrap.dedent(
            f"""\
            id: https://example.org/root
            name: root
            {header_overrides}
            prefixes:
              ex: https://example.org/root#
              linkml: https://w3id.org/linkml/
            imports:
              - linkml:types
            {imports}
            classes:
              Thing:
                class_uri: ex:Thing
            """
        ),
        encoding="utf-8",
    )
    return schema


def test_undeclared_default_prefix_raises_schema_error_naming_prefix_and_schema(tmp_path: Path) -> None:
    schema = _write_root_schema(tmp_path, "default_prefix: zz", "")

    with pytest.raises(SchemaError, match=r"default_prefix 'zz' is not declared") as excinfo:
        preprocess_for_gen_owl(str(schema))

    assert str(schema) in str(excinfo.value)


def test_omitted_default_prefix_raises_schema_error_naming_schema(tmp_path: Path) -> None:
    # LinkML substitutes the schema id for an omitted default_prefix, which is never a declared prefix.
    schema = _write_root_schema(tmp_path, "", "")

    with pytest.raises(SchemaError, match=r"default_prefix .* is not declared") as excinfo:
        preprocess_for_gen_owl(str(schema))

    assert str(schema) in str(excinfo.value)


def test_missing_local_import_raises_schema_error_naming_importer_and_path(tmp_path: Path) -> None:
    schema = _write_root_schema(tmp_path, "default_prefix: ex", "  - missing_module")

    with pytest.raises(SchemaError, match=r"imports 'missing_module'") as excinfo:
        preprocess_for_gen_owl(str(schema))

    message = str(excinfo.value)
    assert str(schema) in message
    assert str(tmp_path / "missing_module.yaml") in message


def test_missing_transitive_local_import_names_the_importing_sub_schema(tmp_path: Path) -> None:
    (tmp_path / "middle.yaml").write_text(_OTHER_SCHEMA + "imports:\n  - gone\n", encoding="utf-8")
    schema = _write_root_schema(tmp_path, "default_prefix: ex", "  - middle")

    with pytest.raises(SchemaError, match=r"imports 'gone'") as excinfo:
        preprocess_for_gen_owl(str(schema))

    message = str(excinfo.value)
    assert str(tmp_path / "middle.yaml") in message
    assert str(tmp_path / "gone.yaml") in message


def test_missing_root_schema_raises_schema_error_naming_path(tmp_path: Path) -> None:
    schema = tmp_path / "absent.yaml"

    with pytest.raises(SchemaError, match=r"LinkML schema file not found") as excinfo:
        preprocess_for_gen_owl(str(schema))

    assert str(schema) in str(excinfo.value)


def _write_sub_schema(tmp_path: Path, name: str, imports: str, enum: str) -> None:
    (tmp_path / f"{name}.yaml").write_text(
        textwrap.dedent(
            f"""\
            id: https://example.org/{name}
            name: {name}
            default_prefix: ex
            prefixes:
              ex: https://example.org/root#
            imports:
              - {imports}
            enums:
              {enum}:
                enum_uri: ex:{enum}
                permissible_values:
                  dark: {{}}
            """
        ),
        encoding="utf-8",
    )


def test_cyclic_local_imports_are_walked_once(tmp_path: Path) -> None:
    _write_sub_schema(tmp_path, "a", "b", "Shade")
    _write_sub_schema(tmp_path, "b", "a", "Tone")
    schema = _write_root_schema(tmp_path, "default_prefix: ex", "  - a")

    output = preprocess_for_gen_owl(str(schema))

    assert "Shade:" in output
    assert "Tone:" in output

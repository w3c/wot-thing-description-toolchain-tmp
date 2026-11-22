import pytest
from linkml_runtime.linkml_model.meta import EnumDefinition, SchemaDefinition, SlotDefinition
from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.artifacts.owl.pre_passes import _attr_slot_name, _strip_non_ontological_enums
from wot_toolchain.model.names import is_non_ontological_enum, local_name

LOCAL_NAME_CASES = {
    "hash_namespace": ("https://www.w3.org/2019/wot/td#name", "name"),
    "slash_namespace": ("https://example.org/vocab/term", "term"),
    "slash_after_hash": ("https://example.org/a#b/c", "c"),
    "trailing_hash": ("https://example.org/a#", ""),
    "trailing_slash": ("https://example.org/a/", ""),
    "no_separator": ("term", "term"),
}

ENUM_URI_CASES = {
    "missing": (None, True),
    "linkml_curie": ("linkml:TypeDiscriminator", True),
    "local_curie": ("ex:Color", False),
    "absolute_iri": ("https://example.org/ex#Color", False),
    "linkml_absolute_iri": ("https://w3id.org/linkml/Any", False),
}


def _probe_view() -> SchemaView:
    return SchemaView(SchemaDefinition(id="https://example.org/probe", name="probe"))


@pytest.mark.parametrize(("iri", "expected"), LOCAL_NAME_CASES.values(), ids=LOCAL_NAME_CASES.keys())
def test_local_name(iri: str, expected: str) -> None:
    assert local_name(iri) == expected


@pytest.mark.parametrize(("iri", "_expected"), LOCAL_NAME_CASES.values(), ids=LOCAL_NAME_CASES.keys())
def test_local_name_matches_owl_preprocessor(iri: str, _expected: str) -> None:
    slot = SlotDefinition(name="probe", slot_uri=iri)
    assert local_name(iri) == _attr_slot_name("probe", slot, _probe_view())


@pytest.mark.parametrize(("enum_uri", "expected"), ENUM_URI_CASES.values(), ids=ENUM_URI_CASES.keys())
def test_is_non_ontological_enum(enum_uri: str | None, expected: bool) -> None:
    assert is_non_ontological_enum(EnumDefinition(name="Probe", enum_uri=enum_uri)) is expected


@pytest.mark.parametrize(("enum_uri", "_expected"), ENUM_URI_CASES.values(), ids=ENUM_URI_CASES.keys())
def test_is_non_ontological_enum_matches_owl_preprocessor(enum_uri: str | None, _expected: bool) -> None:
    enum = EnumDefinition(name="Probe", enum_uri=enum_uri)
    schema = SchemaDefinition(id="https://example.org/probe", name="probe", enums={"Probe": enum})
    _strip_non_ontological_enums(schema)
    assert is_non_ontological_enum(enum) is ("Probe" not in schema.enums)

"""Test the property domains and ranges read from the Thing Description schema."""

from pathlib import Path

import pytest
from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.artifacts.rdf_terms import (
    class_valued_properties,
    domain_classes_by_property,
    indexed_classes_by_property,
    language_map_property_iris,
    most_general_classes,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
TD = "https://www.w3.org/2019/wot/td#"
HCTL = "https://www.w3.org/2019/wot/hypermedia#"
WOTSEC = "https://www.w3.org/2019/wot/security#"
JSONSCHEMA = "https://www.w3.org/2019/wot/json-schema#"


@pytest.fixture(scope="module")
def schema_view() -> SchemaView:
    return SchemaView(str(REPO_ROOT / "resources" / "schemas" / "thing_description.yaml"), merge_imports=True)


def test_property_domain_is_every_class_that_uses_it(schema_view: SchemaView) -> None:
    domains = domain_classes_by_property(schema_view)

    assert domains[WOTSEC + "scopes"] == {HCTL + "Form", WOTSEC + "OAuth2SecurityScheme"}
    assert domains[TD + "name"] == {TD + "InteractionAffordance"}


def test_index_property_is_stated_on_the_indexed_classes(schema_view: SchemaView) -> None:
    assert indexed_classes_by_property(schema_view) == {
        TD + "name": {"DataSchema"},
        JSONSCHEMA + "propertyName": {"DataSchema"},
    }


def test_most_general_classes_drops_subclasses(schema_view: SchemaView) -> None:
    names = {"Thing", "PropertyAffordance", "InteractionAffordance"}

    assert most_general_classes(schema_view, names) == {"Thing", "InteractionAffordance"}


def test_language_map_properties(schema_view: SchemaView) -> None:
    assert language_map_property_iris(schema_view) == {TD + "titleInLanguage", TD + "descriptionInLanguage"}


def test_class_valued_properties_name_the_classes_of_their_enum_values(schema_view: SchemaView) -> None:
    properties = class_valued_properties(schema_view)

    assert set(properties) == {JSONSCHEMA + "type", WOTSEC + "scheme"}
    assert WOTSEC + "BasicSecurityScheme" in properties[WOTSEC + "scheme"]
    assert JSONSCHEMA + "ObjectSchema" in properties[JSONSCHEMA + "type"]

"""ResolvedProject.validate rejects malformed jsonschema_, jsonld_ and spec_ annotations before any pass runs."""

from pathlib import Path

import pytest
import yaml

from wot_toolchain.config import load_project
from wot_toolchain.errors import SchemaError
from wot_toolchain.model.resolved import ResolvedProject

TESTS = Path(__file__).resolve().parent
REPO_CONFIG = TESTS.parent / "wot-toolchain.yaml"
SECOND_PROJECT_CONFIG = TESTS / "fixtures" / "mini-project" / "wot-toolchain.yaml"


def _schema(
    tmp_path: Path,
    *,
    class_annotations: dict | None = None,
    slot_annotations: dict | None = None,
    usage_annotations: dict | None = None,
) -> Path:
    usage = {"label": {"annotations": usage_annotations}} if usage_annotations else {}
    schema = {
        "id": "https://example.org/box",
        "name": "box",
        "prefixes": {"linkml": "https://w3id.org/linkml/", "box": "https://example.org/box/"},
        "default_prefix": "box",
        "default_range": "string",
        "imports": ["linkml:types"],
        "classes": {
            "Box": {
                "slots": ["label"],
                **({"annotations": class_annotations} if class_annotations else {}),
                **({"slot_usage": usage} if usage else {}),
            }
        },
        "slots": {"label": {"annotations": slot_annotations} if slot_annotations else {}},
    }
    path = tmp_path / "box.yaml"
    path.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")
    return path


MALFORMED = [
    ("class", "Box", "jsonschema_oneof_dispatch", {"value": {"include_unknown": True}}),
    ("class", "Box", "jsonschema_oneof_dispatch", {"value": {"discriminator": "kind", "include_unknown": "yes"}}),
    ("class", "Box", "jsonschema_enum_subset_partition", {"value": {"enum": "Kinds"}}),
    ("slot_usage", "Box.label", "jsonschema_form_subset", {"value": ["a", "b"]}),
    ("slot", "label", "jsonld_index", {"value": {"term": "box:name"}}),
    ("slot", "label", "jsonld_container", {"value": ["@language"]}),
    ("slot", "label", "jsonld_context", {"value": {"prefix": "box"}}),
    ("slot", "label", "spec_description", {"value": {"text": "A label."}}),
    ("class", "Box", "spec_description", {"value": ["A box."]}),
    ("class", "Box", "spec_content", {"value": "Plain text instead of blocks."}),
    ("class", "Box", "spec_intro_content", {"value": ["text", "more text"]}),
    ("class", "Box", "spec_subsections", {"value": "A subsection."}),
    ("slot_usage", "Box.label", "spec_type_values", {"value": {"mode": "one_of", "values": "a"}}),
    ("slot", "label", "spec_type_values", {"value": ["a", "b"]}),
]


@pytest.mark.parametrize(("kind", "name", "key", "annotation"), MALFORMED)
def test_malformed_annotation_names_element_and_key(
    tmp_path: Path, kind: str, name: str, key: str, annotation: dict
) -> None:
    placement = {"class": "class_annotations", "slot": "slot_annotations", "slot_usage": "usage_annotations"}[kind]
    resolved = ResolvedProject(_schema(tmp_path, **{placement: {key: annotation}}))

    with pytest.raises(SchemaError) as excinfo:
        resolved.validate()

    assert f"{kind} {name!r}" in str(excinfo.value)
    assert repr(key) in str(excinfo.value)


def test_every_problem_is_reported_in_one_error(tmp_path: Path) -> None:
    resolved = ResolvedProject(
        _schema(
            tmp_path,
            class_annotations={"spec_content": {"value": "not blocks"}},
            slot_annotations={"jsonld_index": {"value": {"term": "box:name"}}},
        )
    )

    with pytest.raises(SchemaError) as excinfo:
        resolved.validate()

    message = str(excinfo.value)
    assert "class 'Box'" in message and "'spec_content'" in message
    assert "slot 'label'" in message and "'jsonld_index'" in message


def test_unknown_annotation_keys_are_ignored(tmp_path: Path) -> None:
    unknown = {"value": {"anything": ["goes"]}}
    resolved = ResolvedProject(
        _schema(tmp_path, class_annotations={"jsonld_unknown_feature": unknown, "other_tool": unknown})
    )

    resolved.validate()


def test_well_formed_annotations_pass(tmp_path: Path) -> None:
    resolved = ResolvedProject(
        _schema(
            tmp_path,
            class_annotations={
                "jsonschema_oneof_dispatch": {"value": {"discriminator": "label", "include_unknown": True}},
                "spec_description": "A box.",
                "spec_content": {"value": [{"type": "markdown", "text": "Boxes hold things."}]},
            },
            slot_annotations={"jsonld_index": "box:name", "jsonld_container": "@language", "jsonld_context": "none"},
            usage_annotations={"spec_type_values": {"value": {"mode": "one_of", "values": ["a", "b"]}}},
        )
    )

    resolved.validate()


def test_reading_the_merged_view_does_not_validate(tmp_path: Path) -> None:
    resolved = ResolvedProject(_schema(tmp_path, class_annotations={"spec_content": {"value": "not blocks"}}))

    assert "Box" in resolved.merged.all_classes()


@pytest.mark.parametrize("config", [REPO_CONFIG, SECOND_PROJECT_CONFIG], ids=["td", "second-project"])
def test_current_projects_validate_clean(config: Path) -> None:
    ResolvedProject(load_project(config).root_schema).validate()

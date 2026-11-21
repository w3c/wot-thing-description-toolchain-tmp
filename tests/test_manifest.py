"""The project manifest is loaded into immutable, absolute settings or rejected with a precise ManifestError."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml

from wot_toolchain.config import Module, Project, SpecConfig, SpecSection, load_project
from wot_toolchain.errors import ManifestError, WotToolchainError

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_NAME = "wot-toolchain.yaml"

BASE_MANIFEST: dict[str, Any] = {
    "main_schema": "schemas/core.yaml",
    "output_dir": "out",
    "generators": ["jsonschema", "owl"],
    "jsonschema": {"top_class": "Root"},
    "modules": [
        {
            "schema": "schemas/core.yaml",
            "prefix": "core",
            "ontology": "core.ttl",
            "context": "core.jsonld",
            "diagram": "core.svg",
        },
        {"schema": "schemas/extra.yaml", "prefix": "extra"},
    ],
    "spec": {
        "template": "spec/template.html",
        "output": "out/index.html",
        "placeholder": "%s",
        "vocab_id_prefix": "core",
        "first_class": "Root",
        "sections": [
            {"id": "sec-extra", "schema": "schemas/extra.yaml"},
            {"id": "sec-core", "schema": "schemas/core.yaml"},
        ],
        "snippets": "spec/snippets",
        "glossary": "spec/glossary.yaml",
        "extra_asserts": "spec/extra-asserts.html",
        "assertions_csv": "out/assertions.csv",
        "snippet_validation_schemas": {"instance": "spec/instance-schema.json"},
    },
}

INPUT_FILES = (
    "schemas/core.yaml",
    "schemas/extra.yaml",
    "spec/template.html",
    "spec/glossary.yaml",
    "spec/extra-asserts.html",
    "spec/instance-schema.json",
)
INPUT_DIRS = ("spec/snippets",)


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a project directory holding every input file BASE_MANIFEST references."""
    root = tmp_path / "project"
    for name in INPUT_FILES:
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text("", encoding="utf-8")
    for name in INPUT_DIRS:
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


@pytest.fixture
def manifest() -> dict[str, Any]:
    """Return a fresh, valid manifest document that a test may mutate."""
    return copy.deepcopy(BASE_MANIFEST)


def write_manifest(project_dir: Path, document: Any) -> Path:
    path = project_dir / MANIFEST_NAME
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def load_expecting_error(project_dir: Path, document: Any, *fragments: str) -> ManifestError:
    path = write_manifest(project_dir, document)
    with pytest.raises(ManifestError) as excinfo:
        load_project(path)
    message = str(excinfo.value)
    assert str(path) in message
    for fragment in fragments:
        assert fragment in message
    return excinfo.value


# --- valid manifests -------------------------------------------------------------------------------------------------


def test_valid_manifest_resolves_paths_against_manifest_directory(project_dir: Path, manifest: dict[str, Any]) -> None:
    project = load_project(write_manifest(project_dir, manifest))

    assert project == Project(
        manifest_path=project_dir / MANIFEST_NAME,
        main_schema=project_dir / "schemas/core.yaml",
        output_dir=project_dir / "out",
        generators=("jsonschema", "owl"),
        top_class="Root",
        modules=(
            Module(project_dir / "schemas/core.yaml", "core", "core.ttl", "core.jsonld", "core.svg"),
            Module(project_dir / "schemas/extra.yaml", "extra", None, None, None),
        ),
        spec=SpecConfig(
            template=project_dir / "spec/template.html",
            output=project_dir / "out/index.html",
            placeholder="%s",
            vocab_id_prefix="core",
            first_class="Root",
            sections=(
                SpecSection("sec-extra", project_dir / "schemas/extra.yaml", "extra"),
                SpecSection("sec-core", project_dir / "schemas/core.yaml", "core"),
            ),
            snippets=project_dir / "spec/snippets",
            glossary=project_dir / "spec/glossary.yaml",
            extra_asserts=project_dir / "spec/extra-asserts.html",
            assertions_csv=project_dir / "out/assertions.csv",
            snippet_validation_schemas={"instance": project_dir / "spec/instance-schema.json"},
        ),
    )


def test_paths_are_absolute_even_when_cwd_is_elsewhere(
    project_dir: Path, manifest: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = write_manifest(project_dir, manifest)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    project = load_project(Path("..") / "project" / MANIFEST_NAME)

    assert project.manifest_path == path.resolve()
    assert project.main_schema == (project_dir / "schemas/core.yaml").resolve()
    assert project.main_schema.is_absolute()
    assert project.output_dir.is_absolute()


def test_optional_parts_may_be_omitted(project_dir: Path, manifest: dict[str, Any]) -> None:
    del manifest["spec"]
    del manifest["jsonschema"]

    project = load_project(write_manifest(project_dir, manifest))

    assert project.spec is None
    assert project.top_class is None


def test_optional_spec_keys_may_be_omitted(project_dir: Path, manifest: dict[str, Any]) -> None:
    for key in ("first_class", "extra_asserts", "assertions_csv", "snippet_validation_schemas"):
        del manifest["spec"][key]

    spec = load_project(write_manifest(project_dir, manifest)).spec

    assert spec is not None
    assert spec.first_class is None
    assert spec.extra_asserts is None
    assert spec.assertions_csv is None
    assert dict(spec.snippet_validation_schemas) == {}


def test_output_paths_need_not_exist(project_dir: Path, manifest: dict[str, Any]) -> None:
    project = load_project(write_manifest(project_dir, manifest))

    assert project.spec is not None
    assert not project.output_dir.exists()
    assert not project.spec.output.exists()


def test_project_is_immutable(project_dir: Path, manifest: dict[str, Any]) -> None:
    project = load_project(write_manifest(project_dir, manifest))

    assert isinstance(project.generators, tuple)
    assert isinstance(project.modules, tuple)
    with pytest.raises(AttributeError):
        project.output_dir = project_dir  # type: ignore[misc]
    assert project.spec is not None
    with pytest.raises(TypeError):
        project.spec.snippet_validation_schemas["other"] = project_dir  # type: ignore[index]


# --- the repository's own manifest -----------------------------------------------------------------------------------


def test_repository_manifest_loads() -> None:
    project = load_project(REPO_ROOT / MANIFEST_NAME)

    assert project.main_schema == REPO_ROOT / "resources/schemas/thing_description.yaml"
    assert project.output_dir == REPO_ROOT / "resources/gens"
    assert project.generators == ("jsonschema", "shacl", "jsonldcontext", "owl", "linkml", "visualization")
    assert project.top_class == "Thing"
    assert [module.prefix for module in project.modules] == ["td", "hctl", "wotsec", "jsonschema", "tm"]
    assert [module.ontology for module in project.modules] == [
        "td.ttl",
        "hctl.ttl",
        "wotsec.ttl",
        "jsonschema.ttl",
        "tm.ttl",
    ]
    assert project.spec is not None
    assert project.spec.vocab_id_prefix == "td"


# --- unreadable manifests --------------------------------------------------------------------------------------------


def test_missing_manifest_file(tmp_path: Path) -> None:
    path = tmp_path / MANIFEST_NAME
    with pytest.raises(ManifestError, match="not found") as excinfo:
        load_project(path)
    assert str(path) in str(excinfo.value)


def test_manifest_error_is_a_toolchain_error() -> None:
    assert issubclass(ManifestError, WotToolchainError)


def test_invalid_yaml(project_dir: Path) -> None:
    path = project_dir / MANIFEST_NAME
    path.write_text("modules: [unclosed\n", encoding="utf-8")
    with pytest.raises(ManifestError, match="not valid YAML") as excinfo:
        load_project(path)
    assert str(path) in str(excinfo.value)


@pytest.mark.parametrize("document", [None, ["a", "b"], "text"])
def test_top_level_must_be_mapping(project_dir: Path, document: Any) -> None:
    load_expecting_error(project_dir, document, "mapping")


# --- unknown keys ----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("where", "key_path"),
    [
        ((), "colour"),
        (("jsonschema",), "jsonschema.colour"),
        (("modules", 1), "modules[1].colour"),
        (("spec",), "spec.colour"),
        (("spec", "sections", 0), "spec.sections[0].colour"),
    ],
)
def test_unknown_key_is_rejected(
    project_dir: Path, manifest: dict[str, Any], where: tuple[str | int, ...], key_path: str
) -> None:
    node: Any = manifest
    for step in where:
        node = node[step]
    node["colour"] = "blue"

    load_expecting_error(project_dir, manifest, key_path, "unknown key")


# --- missing required keys -------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("where", "key", "key_path"),
    [
        ((), "main_schema", "main_schema"),
        ((), "output_dir", "output_dir"),
        ((), "generators", "generators"),
        ((), "modules", "modules"),
        (("modules", 0), "schema", "modules[0].schema"),
        (("modules", 0), "prefix", "modules[0].prefix"),
        (("spec",), "template", "spec.template"),
        (("spec",), "output", "spec.output"),
        (("spec",), "sections", "spec.sections"),
        (("spec",), "snippets", "spec.snippets"),
        (("spec",), "glossary", "spec.glossary"),
        (("spec",), "placeholder", "spec.placeholder"),
        (("spec",), "vocab_id_prefix", "spec.vocab_id_prefix"),
        (("spec", "sections", 1), "id", "spec.sections[1].id"),
        (("spec", "sections", 1), "schema", "spec.sections[1].schema"),
    ],
)
def test_missing_required_key_is_rejected(
    project_dir: Path, manifest: dict[str, Any], where: tuple[str | int, ...], key: str, key_path: str
) -> None:
    node: Any = manifest
    for step in where:
        node = node[step]
    del node[key]

    load_expecting_error(project_dir, manifest, key_path, "missing required key")


# --- wrong value types -----------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("key_path", "value"),
    [
        ("modules", {"schema": "schemas/core.yaml"}),
        ("generators", "owl"),
        ("main_schema", 42),
        ("jsonschema", "Root"),
        ("spec", ["template.html"]),
        ("modules[0]", "schemas/core.yaml"),
        ("modules[0].prefix", ["core"]),
        ("modules[0].ontology", True),
        ("spec.sections", "sec-core"),
        ("spec.placeholder", 7),
        ("spec.vocab_id_prefix", 7),
        ("spec.vocab_id_prefix", ""),
        ("spec.snippet_validation_schemas", ["spec/instance-schema.json"]),
        ("spec.snippet_validation_schemas.instance", 3),
        ("generators[0]", {"name": "owl"}),
    ],
)
def test_wrong_value_type_is_rejected(project_dir: Path, manifest: dict[str, Any], key_path: str, value: Any) -> None:
    set_by_key_path(manifest, key_path, value)

    load_expecting_error(project_dir, manifest, key_path, "must be")


@pytest.mark.parametrize("key_path", ["modules", "generators", "spec.sections"])
def test_empty_list_is_rejected(project_dir: Path, manifest: dict[str, Any], key_path: str) -> None:
    set_by_key_path(manifest, key_path, [])

    load_expecting_error(project_dir, manifest, key_path, "must not be empty")


@pytest.mark.parametrize("key_path", ["main_schema", "modules[1].prefix", "spec.sections[0].id"])
def test_empty_string_is_rejected(project_dir: Path, manifest: dict[str, Any], key_path: str) -> None:
    set_by_key_path(manifest, key_path, "")

    load_expecting_error(project_dir, manifest, key_path, "non-empty string")


@pytest.mark.parametrize("key", ["ontology", "context", "diagram"])
def test_module_output_name_must_be_bare_file_name(project_dir: Path, manifest: dict[str, Any], key: str) -> None:
    manifest["modules"][0][key] = "sub/dir.out"

    load_expecting_error(project_dir, manifest, f"modules[0].{key}", "file name")


def set_by_key_path(document: dict[str, Any], key_path: str, value: Any) -> None:
    steps: list[str | int] = []
    for part in key_path.split("."):
        name, _, index = part.partition("[")
        steps.append(name)
        if index:
            steps.append(int(index.rstrip("]")))
    node: Any = document
    for step in steps[:-1]:
        node = node[step]
    node[steps[-1]] = value


# --- semantic errors -------------------------------------------------------------------------------------------------


def test_unknown_generator_is_rejected(project_dir: Path, manifest: dict[str, Any]) -> None:
    manifest["generators"] = ["owl", "pdf"]

    error = load_expecting_error(project_dir, manifest, "generators[1]", "'pdf'")
    assert "jsonschema" in str(error)


def test_duplicate_generator_is_rejected(project_dir: Path, manifest: dict[str, Any]) -> None:
    manifest["generators"] = ["owl", "owl"]

    load_expecting_error(project_dir, manifest, "generators[1]", "duplicate")


@pytest.mark.parametrize(
    ("key_path", "missing"),
    [
        ("main_schema", "schemas/absent.yaml"),
        ("modules[1].schema", "schemas/absent.yaml"),
        ("spec.template", "spec/absent.html"),
        ("spec.snippets", "spec/absent"),
        ("spec.glossary", "spec/absent.yaml"),
        ("spec.extra_asserts", "spec/absent.html"),
        ("spec.snippet_validation_schemas.instance", "spec/absent.json"),
    ],
)
def test_missing_input_path_is_rejected(
    project_dir: Path, manifest: dict[str, Any], key_path: str, missing: str
) -> None:
    set_by_key_path(manifest, key_path, missing)

    load_expecting_error(project_dir, manifest, key_path, str(project_dir / missing), "does not exist")


@pytest.mark.parametrize(
    ("key_path", "wrong_kind", "expected_kind"),
    [("spec.template", "spec/snippets", "file"), ("spec.snippets", "spec/glossary.yaml", "directory")],
)
def test_input_path_of_wrong_kind_is_rejected(
    project_dir: Path, manifest: dict[str, Any], key_path: str, wrong_kind: str, expected_kind: str
) -> None:
    set_by_key_path(manifest, key_path, wrong_kind)

    load_expecting_error(project_dir, manifest, key_path, f"is not a {expected_kind}")


def test_duplicate_module_schema_is_rejected(project_dir: Path, manifest: dict[str, Any]) -> None:
    manifest["modules"][1]["schema"] = "schemas/core.yaml"

    load_expecting_error(project_dir, manifest, "modules[1].schema", "duplicate")


def test_duplicate_module_prefix_is_rejected(project_dir: Path, manifest: dict[str, Any]) -> None:
    manifest["modules"][1]["prefix"] = "core"

    load_expecting_error(project_dir, manifest, "modules[1].prefix", "duplicate", "'core'")


def test_section_schema_must_belong_to_a_module(project_dir: Path, manifest: dict[str, Any]) -> None:
    (project_dir / "schemas/orphan.yaml").write_text("", encoding="utf-8")
    manifest["spec"]["sections"][0]["schema"] = "schemas/orphan.yaml"

    load_expecting_error(project_dir, manifest, "spec.sections[0].schema", "not the schema of any module")


# --- snippet validation against the schema generated in the same run -------------------------------------------------


def test_generated_validation_schema_is_kept_apart_from_static_files(
    project_dir: Path, manifest: dict[str, Any]
) -> None:
    manifest["spec"]["snippet_validation_schemas"]["generated"] = {"generated": "jsonschema"}

    spec = load_project(write_manifest(project_dir, manifest)).spec

    assert spec is not None
    assert dict(spec.snippet_validation_schemas) == {"instance": project_dir / "spec/instance-schema.json"}
    assert dict(spec.generated_snippet_validation_schemas) == {"generated": "jsonschema"}
    with pytest.raises(TypeError):
        spec.generated_snippet_validation_schemas["other"] = "jsonschema"  # type: ignore[index]


def test_static_only_manifest_has_no_generated_validation_schemas(project_dir: Path, manifest: dict[str, Any]) -> None:
    spec = load_project(write_manifest(project_dir, manifest)).spec

    assert spec is not None
    assert dict(spec.generated_snippet_validation_schemas) == {}


@pytest.mark.parametrize("generator", ["owl", "pdf"])
def test_generated_validation_schema_must_name_a_json_schema_generator(
    project_dir: Path, manifest: dict[str, Any], generator: str
) -> None:
    manifest["spec"]["snippet_validation_schemas"]["instance"] = {"generated": generator}

    load_expecting_error(
        project_dir, manifest, "spec.snippet_validation_schemas.instance.generated", repr(generator), "jsonschema"
    )


@pytest.mark.parametrize(
    ("entry", "fragment"),
    [
        ({"generated": "jsonschema", "colour": "blue"}, "unknown key"),
        ({}, "missing required key"),
        ({"generated": 3}, "must be"),
        ({"generated": ""}, "non-empty string"),
        (["jsonschema"], "must be"),
    ],
)
def test_malformed_generated_validation_schema_is_rejected(
    project_dir: Path, manifest: dict[str, Any], entry: Any, fragment: str
) -> None:
    manifest["spec"]["snippet_validation_schemas"]["instance"] = entry

    load_expecting_error(project_dir, manifest, "spec.snippet_validation_schemas.instance", fragment)


# --- labels of LinkML ranges in the vocabulary tables ----------------------------------------------------------------


def test_range_labels_are_loaded_read_only(project_dir: Path, manifest: dict[str, Any]) -> None:
    manifest["spec"]["range_labels"] = {"uri": "anyURI", "Any": "any type"}

    spec = load_project(write_manifest(project_dir, manifest)).spec

    assert spec is not None
    assert dict(spec.range_labels) == {"uri": "anyURI", "Any": "any type"}
    with pytest.raises(TypeError):
        spec.range_labels["decimal"] = "double"  # type: ignore[index]


def test_range_labels_default_to_empty(project_dir: Path, manifest: dict[str, Any]) -> None:
    spec = load_project(write_manifest(project_dir, manifest)).spec

    assert spec is not None
    assert dict(spec.range_labels) == {}


def test_repository_manifest_labels_ranges_as_the_published_specification() -> None:
    spec = load_project(REPO_ROOT / MANIFEST_NAME).spec

    assert spec is not None
    assert dict(spec.range_labels) == {
        "Any": "any type",
        "linkml:Any": "any type",
        "langString": "rdf:langString",
        "uri": "anyURI",
        "uriorcurie": "anyURI",
        "datetime": "dateTime",
        "NonNegativeInteger": "unsignedInt",
        "decimal": "double",
    }


@pytest.mark.parametrize(
    ("range_labels", "key_path", "fragment"),
    [
        (["uri", "anyURI"], "spec.range_labels", "must be a mapping"),
        ({7: "anyURI"}, "spec.range_labels", "must be a non-empty string"),
        ({"uri": 7}, "spec.range_labels.uri", "must be a non-empty string"),
        ({"uri": ""}, "spec.range_labels.uri", "must be a non-empty string"),
        ({"uri": ["anyURI"]}, "spec.range_labels.uri", "must be a non-empty string"),
    ],
)
def test_invalid_range_labels_are_rejected(
    project_dir: Path, manifest: dict[str, Any], range_labels: Any, key_path: str, fragment: str
) -> None:
    manifest["spec"]["range_labels"] = range_labels

    load_expecting_error(project_dir, manifest, key_path, fragment)


# --- JSON-LD root context terms --------------------------------------------------------------------------------------


def test_extra_root_terms_are_loaded_in_manifest_order(project_dir: Path, manifest: dict[str, Any]) -> None:
    manifest["jsonld"] = {"extra_root_terms": ["schema", "created", "modified"]}

    project = load_project(write_manifest(project_dir, manifest))

    assert project.extra_root_terms == ("schema", "created", "modified")


def test_extra_root_terms_default_to_empty(project_dir: Path, manifest: dict[str, Any]) -> None:
    project = load_project(write_manifest(project_dir, manifest))

    assert project.extra_root_terms == ()


def test_repository_manifest_keeps_upstream_root_terms() -> None:
    assert load_project(REPO_ROOT / MANIFEST_NAME).extra_root_terms == ("schema", "created", "modified")


@pytest.mark.parametrize(
    ("jsonld", "key_path", "fragment"),
    [
        (["schema"], "jsonld", "must be a mapping"),
        ({"extra_root_terms": "schema"}, "jsonld.extra_root_terms", "must be a list"),
        ({"extra_root_terms": [7]}, "jsonld.extra_root_terms[0]", "must be a non-empty string"),
        ({"extra_root_terms": []}, "jsonld.extra_root_terms", "must not be empty"),
        ({"extra_root_terms": ["schema", "schema"]}, "jsonld.extra_root_terms[1]", "duplicate extra root term"),
        ({"colour": "blue"}, "jsonld.colour", "unknown key"),
    ],
)
def test_invalid_extra_root_terms_are_rejected(
    project_dir: Path, manifest: dict[str, Any], jsonld: Any, key_path: str, fragment: str
) -> None:
    manifest["jsonld"] = jsonld

    load_expecting_error(project_dir, manifest, key_path, fragment)

"""Project configuration: the project manifest loader and the gen-owl options.

A project manifest (``wot-toolchain.yaml``) declares which LinkML schemas make up a vocabulary, which
generators run, where artifacts are written and, optionally, how the specification is assembled.
``load_project`` validates the manifest completely and returns an immutable ``Project`` whose paths are
absolute and resolved relative to the manifest file's directory, never to the current working directory.
Every problem is reported as a ``ManifestError`` naming the manifest, the offending key and the fix.

``GEN_OWL_OPTIONS`` are the options the pipeline passes to LinkML's OWL generator.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal

import yaml

from .errors import ManifestError

GEN_OWL_OPTIONS = {
    "metaclasses": False,
    "type_objects": False,
    "use_native_uris": False,
    "skip_vacuous_local_range_axioms": True,
    "skip_vacuous_min_zero_cardinality_axioms": True,
    "consolidate_cardinality_axioms": False,
    "skip_abstract_class_as_unionof_subclasses": True,
}

KNOWN_GENERATORS = ("jsonschema", "shacl", "jsonldcontext", "owl", "linkml", "visualization")

JSON_SCHEMA_FILES: Mapping[str, str] = MappingProxyType({"jsonschema": "jsonschema.json"})
"""File name of the JSON Schema that a generator writes into its output subdirectory, per generator."""


@dataclass(frozen=True)
class Module:
    """One LinkML schema of the vocabulary and the artifact file names generated from it.

    Attributes:
        schema: Absolute path of the module's LinkML schema.
        prefix: Unique short name of the module.
        ontology: File name of the generated ontology, or ``None`` if the module gets none.
        context: File name of the generated JSON-LD context, or ``None`` if the module gets none.
        diagram: File name of the generated class diagram, or ``None`` if the module gets none.
    """

    schema: Path
    prefix: str
    ontology: str | None
    context: str | None
    diagram: str | None


@dataclass(frozen=True)
class SpecSection:
    """A specification section filled with the vocabulary tables of one module.

    Attributes:
        id: HTML id of the section in the specification template.
        schema: Absolute path of the module schema rendered into the section.
    """

    id: str
    schema: Path


@dataclass(frozen=True)
class SpecConfig:
    """Inputs and outputs of the specification build.

    Attributes:
        template: Absolute path of the HTML specification template.
        output: Absolute path of the rendered specification.
        placeholder: Placeholder in the template that marks where generated content goes.
        vocab_id_prefix: Leading part of every vocabulary-table assertion ID, ``<vocab_id_prefix>-vocab-...``,
            shared by all sections regardless of the module that defines the class.
        first_class: Class whose table is rendered first, or ``None`` to keep schema order.
        sections: Sections to fill, in template order.
        snippets: Directory holding the example snippets.
        glossary: Glossary file used for cross-references.
        extra_asserts: HTML file with assertions not stated as separate sentences in the text, or ``None``.
        assertions_csv: Absolute path of the extracted assertions CSV, or ``None`` if none is written.
        snippet_validation_schemas: Static JSON Schema file per snippet kind, read-only.
        generated_snippet_validation_schemas: Snippet kinds validated against the JSON Schema generated in the
            same run, mapped to the generator that writes it, read-only. Written ``kind: {generated: GENERATOR}``
            under ``snippet_validation_schemas`` in the manifest.
    """

    template: Path
    output: Path
    placeholder: str
    vocab_id_prefix: str
    first_class: str | None
    sections: tuple[SpecSection, ...]
    snippets: Path
    glossary: Path
    extra_asserts: Path | None
    assertions_csv: Path | None
    snippet_validation_schemas: Mapping[str, Path] = field(hash=False)
    generated_snippet_validation_schemas: Mapping[str, str] = field(
        default_factory=lambda: MappingProxyType({}), hash=False
    )


@dataclass(frozen=True)
class Project:
    """A fully validated project manifest.

    Attributes:
        manifest_path: Absolute path of the manifest file.
        main_schema: Absolute path of the schema that imports all modules.
        output_dir: Absolute path of the directory that receives generated artifacts.
        generators: Names of the generators to run, in manifest order.
        top_class: Root class of the generated JSON Schema, or ``None`` for the generator default.
        modules: Vocabulary modules, in manifest order.
        spec: Specification build settings, or ``None`` if the project builds no specification.
        extra_root_terms: Terms outside the main schema's default prefix that stay in the root of the merged
            JSON-LD context, in manifest order. Written under ``jsonld`` in the manifest.
    """

    manifest_path: Path
    main_schema: Path
    output_dir: Path
    generators: tuple[str, ...]
    top_class: str | None
    modules: tuple[Module, ...]
    spec: SpecConfig | None
    extra_root_terms: tuple[str, ...] = ()


@dataclass(frozen=True)
class _Keys:
    required: tuple[str, ...]
    optional: tuple[str, ...] = ()

    @property
    def allowed(self) -> tuple[str, ...]:
        return self.required + self.optional


_PROJECT_KEYS = _Keys(("main_schema", "output_dir", "generators", "modules"), ("jsonschema", "jsonld", "spec"))
_JSONSCHEMA_KEYS = _Keys((), ("top_class",))
_JSONLD_KEYS = _Keys((), ("extra_root_terms",))
_MODULE_KEYS = _Keys(("schema", "prefix"), ("ontology", "context", "diagram"))
_SPEC_KEYS = _Keys(
    ("template", "output", "placeholder", "vocab_id_prefix", "sections", "snippets", "glossary"),
    ("first_class", "extra_asserts", "assertions_csv", "snippet_validation_schemas"),
)
_SECTION_KEYS = _Keys(("id", "schema"))
_GENERATED_SCHEMA_KEYS = _Keys(("generated",))

_PathKind = Literal["file", "directory"]


def load_project(manifest_path: Path) -> Project:
    """Load and validate a project manifest.

    Args:
        manifest_path: Path of the manifest file; relative paths inside it are resolved against its directory.

    Returns:
        The validated project with absolute, resolved paths.

    Raises:
        ManifestError: The manifest is missing, unreadable, not valid YAML or describes an invalid project.
    """
    manifest_path = manifest_path.resolve()
    document = _read_yaml(manifest_path)
    root = _Node.root(manifest_path, document, _PROJECT_KEYS)
    main_schema = root.input_path("main_schema", "file")
    output_dir = root.output_path("output_dir")
    generators = _parse_generators(root)
    top_class = _parse_top_class(root)
    modules = _parse_modules(root)
    return Project(
        manifest_path=manifest_path,
        main_schema=main_schema,
        output_dir=output_dir,
        generators=generators,
        top_class=top_class,
        modules=modules,
        spec=_parse_spec(root, modules),
        extra_root_terms=_parse_extra_root_terms(root),
    )


def _read_yaml(manifest_path: Path) -> object:
    try:
        text = manifest_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ManifestError(
            f"{manifest_path}: manifest file not found. Create it or pass the path of an existing manifest."
        ) from None
    except OSError as exc:
        raise ManifestError(f"{manifest_path}: manifest file could not be read: {exc.strerror}.") from exc
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ManifestError(f"{manifest_path}: manifest is not valid YAML. Fix the syntax error: {exc}") from exc


def _parse_generators(root: _Node) -> tuple[str, ...]:
    generators: list[str] = []
    for key_path, value in root.list_items("generators"):
        name = root.as_string(value, key_path)
        if name not in KNOWN_GENERATORS:
            raise root.error(key_path, f"unknown generator {name!r}", f"Use one of: {', '.join(KNOWN_GENERATORS)}.")
        if name in generators:
            raise root.error(key_path, f"duplicate generator {name!r}", "List each generator once.")
        generators.append(name)
    return tuple(generators)


def _parse_top_class(root: _Node) -> str | None:
    jsonschema = root.optional_mapping("jsonschema", _JSONSCHEMA_KEYS)
    return None if jsonschema is None else jsonschema.optional_string("top_class")


def _parse_extra_root_terms(root: _Node) -> tuple[str, ...]:
    jsonld = root.optional_mapping("jsonld", _JSONLD_KEYS)
    if jsonld is None or "extra_root_terms" not in jsonld.values:
        return ()
    terms: list[str] = []
    for key_path, value in jsonld.list_items("extra_root_terms"):
        term = jsonld.as_string(value, key_path)
        if term in terms:
            raise jsonld.error(key_path, f"duplicate extra root term {term!r}", "List each term once.")
        terms.append(term)
    return tuple(terms)


def _parse_modules(root: _Node) -> tuple[Module, ...]:
    modules: list[Module] = []
    for node in root.mappings("modules", _MODULE_KEYS):
        module = Module(
            schema=node.input_path("schema", "file"),
            prefix=node.string("prefix"),
            ontology=node.optional_file_name("ontology"),
            context=node.optional_file_name("context"),
            diagram=node.optional_file_name("diagram"),
        )
        if any(other.prefix == module.prefix for other in modules):
            raise node.error(
                node.child("prefix"), f"duplicate module prefix {module.prefix!r}", "Give every module a unique prefix."
            )
        if any(other.schema == module.schema for other in modules):
            raise node.error(node.child("schema"), f"duplicate module schema {module.schema}", "List each schema once.")
        modules.append(module)
    return tuple(modules)


def _parse_spec(root: _Node, modules: tuple[Module, ...]) -> SpecConfig | None:
    spec = root.optional_mapping("spec", _SPEC_KEYS)
    if spec is None:
        return None
    module_schemas = {module.schema for module in modules}
    static_schemas, generated_schemas = _parse_validation_schemas(spec)
    return SpecConfig(
        template=spec.input_path("template", "file"),
        output=spec.output_path("output"),
        placeholder=spec.string("placeholder"),
        vocab_id_prefix=spec.string("vocab_id_prefix"),
        first_class=spec.optional_string("first_class"),
        sections=tuple(_parse_section(node, module_schemas) for node in spec.mappings("sections", _SECTION_KEYS)),
        snippets=spec.input_path("snippets", "directory"),
        glossary=spec.input_path("glossary", "file"),
        extra_asserts=spec.optional_input_path("extra_asserts", "file"),
        assertions_csv=spec.optional_output_path("assertions_csv"),
        snippet_validation_schemas=static_schemas,
        generated_snippet_validation_schemas=generated_schemas,
    )


def _parse_section(node: _Node, module_schemas: set[Path]) -> SpecSection:
    schema = node.input_path("schema", "file")
    if schema not in module_schemas:
        raise node.error(
            node.child("schema"),
            f"{schema} is not the schema of any module",
            "Use the schema path of one of the entries under 'modules'.",
        )
    return SpecSection(id=node.string("id"), schema=schema)


def _parse_validation_schemas(spec: _Node) -> tuple[Mapping[str, Path], Mapping[str, str]]:
    key = "snippet_validation_schemas"
    static: dict[str, Path] = {}
    generated: dict[str, str] = {}
    if key in spec.values:
        key_path = spec.child(key)
        for kind, entry in spec.as_mapping(spec.values[key], key_path).items():
            entry_path = f"{key_path}.{spec.as_string(kind, key_path)}"
            if isinstance(entry, dict):
                generated[kind] = _parse_generated_schema(spec, entry, entry_path)
            else:
                static[kind] = spec.resolve_input(entry, entry_path, "file")
    return MappingProxyType(static), MappingProxyType(generated)


def _parse_generated_schema(spec: _Node, entry: object, entry_path: str) -> str:
    node = spec.checked(entry, entry_path, _GENERATED_SCHEMA_KEYS)
    generator = node.string("generated")
    if generator not in JSON_SCHEMA_FILES:
        raise node.error(
            node.child("generated"),
            f"generator {generator!r} does not generate a JSON Schema",
            f"Use one of: {', '.join(JSON_SCHEMA_FILES)}.",
        )
    return generator


@dataclass(frozen=True)
class _Node:
    """A manifest mapping whose keys are already checked, plus its location for precise error messages."""

    manifest_path: Path
    path: str
    values: Mapping[Any, Any]

    @classmethod
    def root(cls, manifest_path: Path, document: object, keys: _Keys) -> _Node:
        return cls(manifest_path, "", {}).checked(document, "", keys)

    def child(self, key: str | int) -> str:
        if isinstance(key, int):
            return f"{self.path}[{key}]"
        return f"{self.path}.{key}" if self.path else key

    def error(self, key_path: str, problem: str, fix: str) -> ManifestError:
        return ManifestError(f"{self.manifest_path}: {key_path or 'top level'}: {problem}. {fix}")

    def type_error(self, key_path: str, expected: str, value: object) -> ManifestError:
        return self.error(key_path, f"must be {expected}, got {_describe(value)}", f"Change the value to {expected}.")

    def checked(self, value: object, key_path: str, keys: _Keys) -> _Node:
        mapping = self.as_mapping(value, key_path)
        node = _Node(self.manifest_path, key_path, mapping)
        for key in mapping:
            if key not in keys.allowed:
                raise self.error(
                    node.child(str(key)), f"unknown key {key!r}", f"Allowed keys here: {', '.join(keys.allowed)}."
                )
        for key in keys.required:
            if key not in mapping:
                raise self.error(node.child(key), "missing required key", "Add it.")
        return node

    def as_mapping(self, value: object, key_path: str) -> Mapping[Any, Any]:
        if not isinstance(value, dict):
            raise self.type_error(key_path, "a mapping", value)
        return value

    def as_string(self, value: object, key_path: str) -> str:
        if not isinstance(value, str) or not value:
            raise self.type_error(key_path, "a non-empty string", value)
        return value

    def string(self, key: str) -> str:
        return self.as_string(self.values[key], self.child(key))

    def optional_string(self, key: str) -> str | None:
        return self.string(key) if key in self.values else None

    def optional_file_name(self, key: str) -> str | None:
        name = self.optional_string(key)
        if name is not None and (Path(name).name != name or name == ".."):
            raise self.error(
                self.child(key),
                f"must be a plain file name without directories, got {name!r}",
                "Remove the directory part; the file is written below 'output_dir'.",
            )
        return name

    def list_items(self, key: str) -> list[tuple[str, object]]:
        key_path = self.child(key)
        value = self.values[key]
        if not isinstance(value, list):
            raise self.type_error(key_path, "a list", value)
        if not value:
            raise self.error(key_path, "must not be empty", "List at least one entry.")
        return [(f"{key_path}[{index}]", item) for index, item in enumerate(value)]

    def mappings(self, key: str, keys: _Keys) -> tuple[_Node, ...]:
        return tuple(self.checked(item, key_path, keys) for key_path, item in self.list_items(key))

    def optional_mapping(self, key: str, keys: _Keys) -> _Node | None:
        return self.checked(self.values[key], self.child(key), keys) if key in self.values else None

    def resolve_input(self, value: object, key_path: str, kind: _PathKind) -> Path:
        path = self.manifest_path.parent / self.as_string(value, key_path)
        path = path.resolve()
        if not path.exists():
            raise self.error(
                key_path, f"{path} does not exist", f"Fix the path; it is relative to {self.manifest_path.parent}."
            )
        if (kind == "file" and not path.is_file()) or (kind == "directory" and not path.is_dir()):
            raise self.error(key_path, f"{path} is not a {kind}", f"Point it at an existing {kind}.")
        return path

    def input_path(self, key: str, kind: _PathKind) -> Path:
        return self.resolve_input(self.values[key], self.child(key), kind)

    def optional_input_path(self, key: str, kind: _PathKind) -> Path | None:
        return self.input_path(key, kind) if key in self.values else None

    def output_path(self, key: str) -> Path:
        return (self.manifest_path.parent / self.string(key)).resolve()

    def optional_output_path(self, key: str) -> Path | None:
        return self.output_path(key) if key in self.values else None


_YAML_TYPE_NAMES: tuple[tuple[type, str], ...] = (
    (bool, "a boolean"),
    (int, "a number"),
    (float, "a number"),
    (str, "a string"),
    (list, "a list"),
    (dict, "a mapping"),
)


def _describe(value: object) -> str:
    if value is None:
        return "null"
    if value == "":
        return "an empty string"
    return next((name for kind, name in _YAML_TYPE_NAMES if isinstance(value, kind)), type(value).__name__)

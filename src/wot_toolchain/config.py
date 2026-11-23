"""The config file loader and the gen-owl options."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal

import yaml
from linkml.validator import validate

from .artifacts.registry import artifact_names
from .errors import ConfigError

GEN_OWL_OPTIONS = {
    "metaclasses": False,
    "type_objects": False,
    "use_native_uris": False,
    "skip_vacuous_local_range_axioms": True,
    "skip_vacuous_min_zero_cardinality_axioms": True,
    "consolidate_cardinality_axioms": False,
    "skip_abstract_class_as_unionof_subclasses": True,
}

CONFIG_SCHEMA = files("wot_toolchain") / "schemas" / "config.yaml"
"""The LinkML schema that a config file conforms to."""

"""File name of the JSON Schema that a generator writes into its output subdirectory, per generator."""


@dataclass(frozen=True)
class Vocabulary:
    """One LinkML schema of the vocabulary and the artifact file names generated from it.

    Attributes:
        schema: Absolute path of the vocabulary's LinkML schema.
        prefix: Unique short name of the vocabulary.
        ontology: File names of the generated ontology, one per serialization; empty if the vocabulary gets none.
        context: File name of the generated JSON-LD context, or ``None`` if the vocabulary gets none.
        diagram: File name of the generated class diagram, or ``None`` if the vocabulary gets none.
    """

    schema: Path
    prefix: str
    ontology: tuple[str, ...]
    context: str | None
    diagram: str | None


@dataclass(frozen=True)
class SpecSection:
    """A specification section filled with the vocabulary tables of one vocabulary.

    Attributes:
        id: HTML id of the section in the specification template.
        schema: Absolute path of the vocabulary schema rendered into the section.
        prefix: Prefix of that vocabulary.
    """

    id: str
    schema: Path
    prefix: str


@dataclass(frozen=True)
class SpecConfig:
    """Inputs and outputs of the specification build.

    Attributes:
        template: Absolute path of the HTML specification template.
        output: Absolute path of the rendered specification.
        vocab_id_prefix: Leading part of every vocabulary-table assertion ID, ``<vocab_id_prefix>-vocab-...``,
            shared by all sections regardless of the vocabulary that defines the class.
        first_class: Class whose table is rendered first, or ``None`` to keep schema order.
        sections: Sections to fill, each into the template's ``%section('<id>')%`` marker.
        snippets: Directory holding the example snippets.
        glossary: Glossary file used for cross-references.
        extra_asserts: HTML file with assertions not stated as separate sentences in the text, or ``None``.
        assertions_csv: Absolute path of the extracted assertions CSV, or ``None`` if none is written.
        snippet_validation_schemas: Static JSON Schema file per snippet kind, read-only.
        generated_snippet_validation_schemas: Snippet kinds validated against the JSON Schema generated in the
            same run, mapped to the generator that writes it, read-only.
        range_labels: Text shown in the vocabulary tables' type column for a LinkML range, keyed by range name,
            read-only; ranges without an entry are shown under their own name.
        default_values_anchor: Fragment id of the section the "with default" assignment links to, or ``None`` to
            show it as plain text.
    """

    template: Path
    output: Path
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
    range_labels: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}), hash=False)
    default_values_anchor: str | None = None


@dataclass(frozen=True)
class JsonSchemaSettings:
    """The ``generators.jsonschema`` settings.

    Attributes:
        top_class: Class that the root of the JSON Schema describes.
        id: Value of the ``$id`` keyword.
        description: Value of the ``description`` keyword at the root of the JSON Schema.
        dialect: JSON Schema dialect, a permissible value of ``JsonSchemaDialect`` in the config schema.
        output: File name of the JSON Schema.
    """

    top_class: str
    id: str
    description: str
    dialect: str
    output: str


@dataclass(frozen=True)
class Project:
    """A validated config file.

    Attributes:
        config_path: Absolute path of the config file.
        root_schema: Absolute path of the schema that imports all vocabularies.
        output_dir: Absolute path of the directory that receives generated artifacts.
        generators: Names of the generators to run, in the order in which they run.
        jsonschema: JSON Schema settings, or ``None`` if the config file has no ``generators.jsonschema``.
        vocabularies: Vocabularies, in config file order.
        spec: Specification build settings, or ``None`` if the project builds no specification.
        extra_root_terms: Terms outside the root schema's default prefix that stay in the root of the merged
            JSON-LD context, in config file order.
    """

    config_path: Path
    root_schema: Path
    output_dir: Path
    generators: tuple[str, ...]
    jsonschema: JsonSchemaSettings | None
    vocabularies: tuple[Vocabulary, ...]
    spec: SpecConfig | None
    extra_root_terms: tuple[str, ...] = ()


_PathKind = Literal["file", "directory"]

SPEC_GENERATOR = "spec"
_GENERATORS_WITH_REQUIRED_SETTINGS = ("jsonschema", SPEC_GENERATOR)


def load_project(config_path: Path) -> Project:
    """Load a config file.

    Args:
        config_path: Path of the config file; relative paths inside it are resolved against its directory.

    Returns:
        The project with absolute, resolved paths.

    Raises:
        ConfigError: The config file is missing, unreadable, not valid YAML, does not conform to the config
            schema or describes an invalid project.
    """
    source = _Source(config_path.resolve())
    document = source.read()
    generators = document["generators"]
    for name in _GENERATORS_WITH_REQUIRED_SETTINGS:
        if name in generators and generators[name] is None:
            raise source.error(f"/generators/{name}", "settings are required")
    vocabularies = _vocabularies(source, document["vocabularies"])
    return Project(
        config_path=source.config_path,
        root_schema=source.input(document["root_schema"], "/root_schema", "file"),
        output_dir=source.output(document["output_dir"]),
        generators=tuple(name for name in (*artifact_names(), SPEC_GENERATOR) if name in generators),
        jsonschema=JsonSchemaSettings(**generators["jsonschema"]) if "jsonschema" in generators else None,
        vocabularies=vocabularies,
        spec=_spec(source, generators["spec"], vocabularies) if "spec" in generators else None,
        extra_root_terms=tuple((generators.get("jsonldcontext") or {}).get("extra_root_terms") or ()),
    )


@dataclass(frozen=True)
class _Source:
    """A config file: reads it and resolves the paths written in it."""

    config_path: Path

    def error(self, location: str, problem: str) -> ConfigError:
        return ConfigError(f"{self.config_path}: {problem} in {location}")

    def read(self) -> dict[str, Any]:
        document = self._read_yaml()
        messages = [result.message for result in validate(document, str(CONFIG_SCHEMA), "Config").results]
        if messages:
            raise ConfigError("\n".join(f"{self.config_path}: {message}" for message in messages))
        return document

    def _read_yaml(self) -> Any:
        try:
            text = self.config_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise ConfigError(f"{self.config_path}: config file not found.") from None
        except OSError as exc:
            raise ConfigError(f"{self.config_path}: config file could not be read: {exc.strerror}.") from exc
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise ConfigError(f"{self.config_path}: config file is not valid YAML: {exc}") from exc

    def output(self, value: str) -> Path:
        return (self.config_path.parent / value).resolve()

    def input(self, value: str, location: str, kind: _PathKind) -> Path:
        path = self.output(value)
        if not path.exists():
            raise self.error(location, f"{path} does not exist")
        if (kind == "file" and not path.is_file()) or (kind == "directory" and not path.is_dir()):
            raise self.error(location, f"{path} is not a {kind}")
        return path


def _vocabularies(source: _Source, entries: list[dict[str, Any]]) -> tuple[Vocabulary, ...]:
    vocabularies: list[Vocabulary] = []
    for index, entry in enumerate(entries):
        location = f"/vocabularies/{index}"
        vocabulary = Vocabulary(
            schema=source.input(entry["schema"], f"{location}/schema", "file"),
            prefix=entry["prefix"],
            ontology=tuple(entry.get("ontology") or ()),
            context=entry.get("context"),
            diagram=entry.get("diagram"),
        )
        if any(other.prefix == vocabulary.prefix for other in vocabularies):
            raise source.error(
                f"{location}/prefix", f"prefix {vocabulary.prefix!r} is used by more than one vocabulary"
            )
        if any(other.schema == vocabulary.schema for other in vocabularies):
            raise source.error(f"{location}/schema", f"{vocabulary.schema} is the schema of more than one vocabulary")
        vocabularies.append(vocabulary)
    return tuple(vocabularies)


def _spec(source: _Source, spec: dict[str, Any], vocabularies: tuple[Vocabulary, ...]) -> SpecConfig:
    location = "/generators/spec"
    static_schemas, generated_schemas = _snippet_validation_schemas(source, spec.get("snippet_validation_schemas"))
    return SpecConfig(
        template=source.input(spec["template"], f"{location}/template", "file"),
        output=source.output(spec["output"]),
        vocab_id_prefix=spec["vocab_id_prefix"],
        first_class=spec.get("first_class"),
        sections=_sections(source, spec["sections"], vocabularies),
        snippets=source.input(spec["snippets"], f"{location}/snippets", "directory"),
        glossary=source.input(spec["glossary"], f"{location}/glossary", "file"),
        extra_asserts=_optional(spec, "extra_asserts", lambda v: source.input(v, f"{location}/extra_asserts", "file")),
        assertions_csv=_optional(spec, "assertions_csv", source.output),
        snippet_validation_schemas=static_schemas,
        generated_snippet_validation_schemas=generated_schemas,
        range_labels=_range_labels(spec.get("range_labels")),
        default_values_anchor=spec.get("default_values_anchor"),
    )


def _optional(mapping: Mapping[str, Any], key: str, convert: Callable[[str], Path]) -> Path | None:
    value = mapping.get(key)
    return None if value is None else convert(value)


def _sections(
    source: _Source, entries: list[dict[str, str]], vocabularies: tuple[Vocabulary, ...]
) -> tuple[SpecSection, ...]:
    prefixes = {vocabulary.schema: vocabulary.prefix for vocabulary in vocabularies}
    sections: list[SpecSection] = []
    for index, entry in enumerate(entries):
        location = f"/generators/spec/sections/{index}/schema"
        schema = source.input(entry["schema"], location, "file")
        if schema not in prefixes:
            raise source.error(location, f"{schema} is not the schema of a vocabulary")
        sections.append(SpecSection(id=entry["id"], schema=schema, prefix=prefixes[schema]))
    return tuple(sections)


def _snippet_validation_schemas(
    source: _Source, entries: Mapping[str, Any] | None
) -> tuple[Mapping[str, Path], Mapping[str, str]]:
    static: dict[str, Path] = {}
    generated: dict[str, str] = {}
    for kind, entry in (entries or {}).items():
        location = f"/generators/spec/snippet_validation_schemas/{kind}"
        path, generator = (entry or {}).get("path"), (entry or {}).get("generated")
        if (path is None) == (generator is None):
            raise source.error(location, "exactly one of 'path' and 'generated' is required")
        if path is None:
            generated[kind] = generator
        else:
            static[kind] = source.input(path, f"{location}/path", "file")
    return MappingProxyType(static), MappingProxyType(generated)


def _range_labels(entries: Mapping[str, Any] | None) -> Mapping[str, str]:
    """Return the label of each range; a label is written as ``range: label`` or ``range: {label: label}``."""
    return MappingProxyType(
        {name: entry if isinstance(entry, str) else entry["label"] for name, entry in (entries or {}).items()}
    )

"""Load the config file and validate it against the LinkML config schema."""

from collections.abc import Mapping
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal

import yaml
from linkml.validator import validate

from .errors import ConfigError

DEFAULT_CONFIG = Path("wot-toolchain.yaml")
CONFIG_SCHEMA = files("wot_toolchain") / "schemas" / "config.yaml"
JSON_SCHEMA_FILE = "jsonschema.json"
GENERATORS = ("jsonschema", "shacl", "jsonldcontext", "owl", "linkml", "visualization", "spec")

type _Kind = Literal["file", "directory"]


@dataclass(frozen=True)
class Vocabulary:
    """A LinkML schema of the vocabulary, its prefix and its class diagram file name, if any."""

    schema: Path
    prefix: str
    diagram: str | None


@dataclass(frozen=True)
class SpecConfig:
    """Inputs and outputs of the spec build."""

    template: Path
    output: Path
    sections: Mapping[str, Path]
    prose: Path | None
    snippets: Path
    thing_model_schema: Path
    glossary: Path
    extra_asserts: Path | None
    assertions_csv: Path | None
    range_labels: Mapping[str, str]
    default_values_anchor: str | None


@dataclass(frozen=True)
class Config:
    """A validated config; its paths are relative to the config file's directory."""

    path: Path
    root_schema: Path
    output_dir: Path
    generators: tuple[str, ...]
    top_class: str | None
    jsonschema_profile: Path | None
    vocabularies: tuple[Vocabulary, ...]
    spec: SpecConfig | None

    @property
    def json_schema(self) -> Path:
        """Path of the JSON Schema that the jsonschema generator writes."""
        return self.output_dir / "jsonschema" / JSON_SCHEMA_FILE

    @property
    def schema_prefixes(self) -> Mapping[Path, str]:
        """Prefix of each vocabulary, keyed by its schema path."""
        return MappingProxyType({vocabulary.schema: vocabulary.prefix for vocabulary in self.vocabularies})


def load_config(path: Path) -> Config:
    """Load and validate a config file, raising ConfigError on the first problem."""
    data = _read(path)
    generators = data["generators"]
    for name in ("jsonschema", "spec"):
        if name in generators and generators[name] is None:
            raise _error(path, f"/generators/{name}", "settings are required")
    if "spec" in generators and "jsonschema" not in generators:
        problem = "generators.jsonschema is missing (the snippets are validated against the JSON Schema it writes)"
        raise _error(path, "/generators/spec", problem)
    vocabularies = _vocabularies(path, data["vocabularies"])
    return Config(
        path=path,
        root_schema=_input(path, data["root_schema"], "/root_schema", "file"),
        output_dir=_output(path, data["output_dir"]),
        generators=tuple(name for name in GENERATORS if name in generators),
        top_class=generators["jsonschema"]["top_class"] if "jsonschema" in generators else None,
        jsonschema_profile=_input(path, generators["jsonschema"]["schema"], "/generators/jsonschema/schema", "file")
        if generators.get("jsonschema", {}).get("schema")
        else None,
        vocabularies=vocabularies,
        spec=_spec(path, generators["spec"], vocabularies) if "spec" in generators else None,
    )


def _read(path: Path) -> dict[str, Any]:
    data = _read_yaml(path)
    messages = [result.message for result in validate(data, str(CONFIG_SCHEMA), "Config").results]
    if messages:
        raise ConfigError("\n".join(f"{path}: {message}" for message in messages))
    return data


def _read_yaml(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ConfigError(f"{path}: config file not found. Create it or pass one with --config.") from None
    except OSError as exc:
        raise ConfigError(f"{path}: config file could not be read: {exc.strerror}.") from exc
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path}: config file is not valid YAML: {exc}") from exc


def _vocabularies(path: Path, entries: list[dict[str, Any]]) -> tuple[Vocabulary, ...]:
    vocabularies: list[Vocabulary] = []
    for index, entry in enumerate(entries):
        where = f"/vocabularies/{index}"
        vocabulary = Vocabulary(
            schema=_input(path, entry["schema"], f"{where}/schema", "file"),
            prefix=entry["prefix"],
            diagram=entry.get("diagram"),
        )
        if any(other.prefix == vocabulary.prefix for other in vocabularies):
            raise _error(path, f"{where}/prefix", f"prefix {vocabulary.prefix!r} is used by more than one vocabulary")
        if any(other.schema == vocabulary.schema for other in vocabularies):
            raise _error(path, f"{where}/schema", f"{vocabulary.schema} is the schema of more than one vocabulary")
        vocabularies.append(vocabulary)
    return tuple(vocabularies)


def _spec(path: Path, spec: dict[str, Any], vocabularies: tuple[Vocabulary, ...]) -> SpecConfig:
    where = "/generators/spec"
    extra_asserts, assertions_csv = spec.get("extra_asserts"), spec.get("assertions_csv")
    prose = spec.get("prose")
    return SpecConfig(
        template=_input(path, spec["template"], f"{where}/template", "file"),
        output=_output(path, spec["output"]),
        sections=_sections(path, spec["sections"], {vocabulary.schema for vocabulary in vocabularies}),
        prose=None if prose is None else _input(path, prose, f"{where}/prose", "directory"),
        snippets=_input(path, spec["snippets"], f"{where}/snippets", "directory"),
        thing_model_schema=_input(path, spec["thing_model_schema"], f"{where}/thing_model_schema", "file"),
        glossary=_input(path, spec["glossary"], f"{where}/glossary", "file"),
        extra_asserts=None if extra_asserts is None else _input(path, extra_asserts, f"{where}/extra_asserts", "file"),
        assertions_csv=None if assertions_csv is None else _output(path, assertions_csv),
        range_labels=_range_labels(spec.get("range_labels")),
        default_values_anchor=spec.get("default_values_anchor"),
    )


def _range_labels(entries: Mapping[str, Any] | None) -> Mapping[str, str]:
    """Return the label of each range; a label is written as ``range: label`` or ``range: {label: label}``."""
    return MappingProxyType(
        {name: entry if isinstance(entry, str) else entry["label"] for name, entry in (entries or {}).items()}
    )


def _sections(path: Path, entries: list[dict[str, str]], schemas: set[Path]) -> Mapping[str, Path]:
    sections: dict[str, Path] = {}
    for index, entry in enumerate(entries):
        where = f"/generators/spec/sections/{index}"
        schema = _input(path, entry["schema"], f"{where}/schema", "file")
        if schema not in schemas:
            raise _error(path, f"{where}/schema", f"{schema} is not the schema of a vocabulary")
        if entry["id"] in sections:
            raise _error(path, f"{where}/id", f"section id {entry['id']!r} is used more than once")
        sections[entry["id"]] = schema
    return MappingProxyType(sections)


def _error(path: Path, where: str, problem: str) -> ConfigError:
    return ConfigError(f"{path}: {problem} in {where}")


def _input(path: Path, value: str, where: str, kind: _Kind) -> Path:
    resolved = _output(path, value)
    if not resolved.exists():
        raise _error(path, where, f"{resolved} does not exist (paths are relative to {path.parent.resolve()})")
    if not (resolved.is_file() if kind == "file" else resolved.is_dir()):
        raise _error(path, where, f"{resolved} is not a {kind}")
    return resolved


def _output(path: Path, value: str) -> Path:
    return path.parent / value

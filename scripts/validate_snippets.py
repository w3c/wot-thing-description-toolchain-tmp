#!/usr/bin/env python3
"""Validate the specification snippets against the Thing Description and Thing Model JSON Schemas."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema.exceptions import SchemaError
from jsonschema.protocols import Validator
from jsonschema.validators import validator_for

REPO_ROOT = Path(__file__).resolve().parent.parent
SNIPPETS = REPO_ROOT / "resources" / "snippets"
TD_SCHEMA = REPO_ROOT / "resources" / "gens" / "jsonschema" / "jsonschema.json"
TM_SCHEMA = REPO_ROOT / "resources" / "upstream" / "schemas" / "tm-json-schema-validation.json"
METADATA_FILE = "_snippets.yaml"
THING_MODEL_TYPE = "tm:ThingModel"

EXIT_INVALID_SNIPPETS = 1
EXIT_UNUSABLE_INPUT = 2


class UnusableInput(Exception):
    """A JSON Schema or the snippet metadata cannot be used."""


def load_validator(schema_path: Path) -> Validator:
    """Return a validator of the dialect that the JSON Schema at ``schema_path`` declares in ``$schema``."""
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UnusableInput(f"{schema_path}: JSON Schema could not be read: {exc}") from exc
    validator_class = validator_for(schema, default=None)
    if validator_class is None:
        raise UnusableInput(f'{schema_path}: "$schema" is missing or names an unsupported JSON Schema dialect.')
    try:
        validator_class.check_schema(schema)
    except SchemaError as exc:
        raise UnusableInput(f"{schema_path}: not a valid JSON Schema: {exc.message}") from exc
    return validator_class(schema)


def load_metadata(snippets_dir: Path) -> dict[str, dict[str, Any]]:
    """Return the metadata of every snippet that ``_snippets.yaml`` lists."""
    path = snippets_dir / METADATA_FILE
    try:
        metadata = yaml.safe_load(path.read_text(encoding="utf-8"))
        return {name: entry or {} for name, entry in metadata["snippets"].items()}
    except (OSError, yaml.YAMLError, AttributeError, KeyError, TypeError) as exc:
        raise UnusableInput(f"{path}: snippet metadata could not be read: {exc!r}") from exc


def snippet_errors(path: Path, td_validator: Validator, tm_validator: Validator) -> list[str]:
    """Return one message for each reason the snippet at ``path`` is invalid."""
    try:
        snippet = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return [f"{path.name}: could not be read: {exc}"]
    except json.JSONDecodeError as exc:
        return [f"{path.name}: not JSON: {exc}"]
    is_thing_model = isinstance(snippet, dict) and snippet.get("@type") == THING_MODEL_TYPE
    validator = tm_validator if is_thing_model else td_validator
    return [
        f"{path.name}: {'.'.join(map(str, error.absolute_path)) or '(root)'} — {error.message}"
        f" [schema: {'/'.join(map(str, error.absolute_schema_path))}]"
        for error in validator.iter_errors(snippet)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snippets", type=Path, default=SNIPPETS, help="directory with the snippets")
    parser.add_argument("--td-schema", type=Path, default=TD_SCHEMA, help="JSON Schema for Thing Descriptions")
    parser.add_argument("--tm-schema", type=Path, default=TM_SCHEMA, help="JSON Schema for Thing Models")
    args = parser.parse_args()

    try:
        td_validator, tm_validator = load_validator(args.td_schema), load_validator(args.tm_schema)
        metadata = load_metadata(args.snippets)
    except UnusableInput as exc:
        print(exc, file=sys.stderr)
        return EXIT_UNUSABLE_INPUT

    validated = [name for name, entry in metadata.items() if entry.get("validate") is not False]
    errors = [
        message
        for name in validated
        for message in snippet_errors(args.snippets / f"{name}.json", td_validator, tm_validator)
    ]
    for message in errors:
        print(message, file=sys.stderr)
    print(f"{len(validated)} snippets validated, {len(metadata) - len(validated)} skipped, {len(errors)} errors")
    return EXIT_INVALID_SNIPPETS if errors else 0


if __name__ == "__main__":
    sys.exit(main())

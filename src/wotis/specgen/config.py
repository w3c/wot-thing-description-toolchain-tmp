from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass(frozen=True)
class Config:
    resources_path: Path
    jinja_templates: Path
    glossary_path: Path
    placeholder: str
    section_schemas: Dict[str, Path]
    schema_prefixes: Dict[str, str]

    @classmethod
    def from_resources_dir(cls, resources: Path, placeholder: str = "%s") -> "Config":
        terms = resources / "xref"
        schema_dir = resources / "schemas"
        section_map = {
            "sec-core-vocabulary-definition": schema_dir / "thing_description.yaml",
            "sec-data-schema-vocabulary-definition": schema_dir / "jsonschema.yaml",
            "sec-security-vocabulary-definition": schema_dir / "wot_security.yaml",
            "sec-hypermedia-vocabulary-definition": schema_dir / "hypermedia.yaml",
        }
        schema_prefixes = {
            "thing_description": "td",
            "hypermedia": "hctl",
            "jsonschema": "jsonschema",
            "wot_security": "wotsec",
            "tm": "tm",
        }

        return cls(
            resources_path=resources,
            jinja_templates=resources / "jinja_templates",
            glossary_path=terms / "glossary.yaml",
            placeholder=placeholder,
            section_schemas=section_map,
            schema_prefixes=schema_prefixes,
        )

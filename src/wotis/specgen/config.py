from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

@dataclass(frozen=True)
class Config:
    resources_path: Path
    jinja_templates: Path
    glossary_path: Path
    biblio_path: Path
    placeholder: str
    section_schemas: Dict[str, Path]

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

        return cls(
            resources_path=resources,
            jinja_templates=resources / "jinja_templates",
            glossary_path=terms / "glossary.yaml",
            biblio_path=terms / "bibliography.yaml",
            placeholder=placeholder,
            section_schemas=section_map,
        )

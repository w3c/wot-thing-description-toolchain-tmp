from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Config:
    resources_path: Path
    jinja_templates: Path
    glossary_path: Path
    biblio_path: Path
    placeholder: str

    @classmethod
    def from_resources_dir(cls, resources: Path, placeholder: str = "%s") -> "Config":
        terms = resources / "xref"
        return cls(
            resources_path=resources,
            jinja_templates=resources / "jinja_templates",
            glossary_path=terms / "glossary.yaml",
            biblio_path=terms / "bibliography.yaml",
            placeholder=placeholder,
        )

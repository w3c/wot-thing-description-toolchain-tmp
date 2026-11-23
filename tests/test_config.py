"""``load_project`` turns a config file into a ``Project``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from wot_toolchain.config import JsonSchemaSettings, Project, SpecConfig, SpecSection, Vocabulary, load_project

INPUT_FILES = (
    "schemas/core.yaml",
    "schemas/extra.yaml",
    "spec/template.html",
    "spec/glossary.yaml",
    "spec/extra-asserts.html",
    "spec/extra.schema.json",
)

CONFIG: dict[str, Any] = {
    "root_schema": "schemas/core.yaml",
    "output_dir": "out",
    "vocabularies": [
        {
            "schema": "schemas/core.yaml",
            "prefix": "core",
            "ontology": ["core.ttl"],
            "context": "core.jsonld",
            "diagram": "core.svg",
        },
        {"schema": "schemas/extra.yaml", "prefix": "extra"},
    ],
    "generators": {
        "owl": {},
        "jsonschema": {
            "top_class": "Root",
            "id": "https://example.org/core.schema.json",
            "description": "JSON Schema for validating instances of Root.",
            "dialect": "draft-07",
            "output": "core.schema.json",
        },
        "jsonldcontext": {"extra_root_terms": ["created", "modified"]},
        "spec": {
            "template": "spec/template.html",
            "output": "out/index.html",
            "vocab_id_prefix": "core",
            "first_class": "Root",
            "sections": [{"id": "sec-extra", "schema": "schemas/extra.yaml"}],
            "snippets": "spec/snippets",
            "glossary": "spec/glossary.yaml",
            "extra_asserts": "spec/extra-asserts.html",
            "assertions_csv": "out/assertions.csv",
            "default_values_anchor": "sec-default-values",
            "range_labels": {"uri": "anyURI"},
            "snippet_validation_schemas": {
                "core": {"generated": "jsonschema"},
                "extra": {"path": "spec/extra.schema.json"},
            },
        },
    },
}


def test_config_is_loaded_with_paths_resolved_against_its_directory(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    for name in INPUT_FILES:
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text("", encoding="utf-8")
    (root / "spec" / "snippets").mkdir()
    config = root / "wot-toolchain.yaml"
    config.write_text(yaml.safe_dump(CONFIG), encoding="utf-8")

    assert load_project(config) == Project(
        config_path=config,
        root_schema=root / "schemas/core.yaml",
        output_dir=root / "out",
        generators=("jsonschema", "jsonldcontext", "owl", "spec"),
        jsonschema=JsonSchemaSettings(
            top_class="Root",
            id="https://example.org/core.schema.json",
            description="JSON Schema for validating instances of Root.",
            dialect="draft-07",
            output="core.schema.json",
        ),
        vocabularies=(
            Vocabulary(
                schema=root / "schemas/core.yaml",
                prefix="core",
                ontology=("core.ttl",),
                context="core.jsonld",
                diagram="core.svg",
            ),
            Vocabulary(schema=root / "schemas/extra.yaml", prefix="extra", ontology=(), context=None, diagram=None),
        ),
        spec=SpecConfig(
            template=root / "spec/template.html",
            output=root / "out/index.html",
            vocab_id_prefix="core",
            first_class="Root",
            sections=(SpecSection(id="sec-extra", schema=root / "schemas/extra.yaml", prefix="extra"),),
            snippets=root / "spec/snippets",
            glossary=root / "spec/glossary.yaml",
            extra_asserts=root / "spec/extra-asserts.html",
            assertions_csv=root / "out/assertions.csv",
            snippet_validation_schemas={"extra": root / "spec/extra.schema.json"},
            generated_snippet_validation_schemas={"core": "jsonschema"},
            range_labels={"uri": "anyURI"},
            default_values_anchor="sec-default-values",
        ),
        extra_root_terms=("created", "modified"),
    )

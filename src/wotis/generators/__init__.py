import json
import logging

from pathlib import Path
from typing import Optional

from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml.generators.shaclgen import ShaclGenerator
from linkml.generators.owlgen import OwlSchemaGenerator
from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml.generators.linkmlgen import LinkmlGenerator
from linkml_runtime.utils.schemaview import SchemaView

from .. import (SCHEMA_PATH, GENS_PATH, GENERATORS,
                RESPEC_TEMPLATE_PATH, FINAL_SPEC_PATH,
                CORE_SCHEMA_PLACEHOLDER, ASSERTION_PATH)
from .visualization import generate_visualizations
from .respec import generate_respec_spec


RESOURCE_GENERATORS = [g for g in GENERATORS if g != "visualization"]


def _run_linkml_generator(schema_view: SchemaView, generator: str, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    if generator == 'jsonschema':
        logging.info("Proceeding with LinkML to JSON Schema conversion")
        json_schema_generator = JsonSchemaGenerator(schema_view.schema, mergeimports=True)
        processed_content = json_schema_generator.serialize()
        output_file = output_dir / 'jsonschema.json'
        with output_file.open('w', encoding='utf-8') as f:
            json.dump(processed_content, f, indent=2, ensure_ascii=False)
        logging.info(f"JSON Schema saved to {output_file}")

    elif generator == 'shacl':
        logging.info("Proceeding with LinkML to SHACL conversion")
        shacl_generator = ShaclGenerator(schema_view.schema, mergeimports=False, closed=True, suffix='Shape')
        (output_dir / 'shapes.shacl.ttl').write_text(shacl_generator.serialize())
        logging.info(f"SHACL shapes saved to {output_dir / 'shapes.shacl.ttl'}")

    elif generator == 'owl':
        logging.info("Proceeding with LinkML to OWL conversion")
        owl_generator = OwlSchemaGenerator(schema_view.schema)
        (output_dir / 'ontology.owl.ttl').write_text(owl_generator.serialize())
        logging.info(f"OWL ontology saved to {output_dir / 'ontology.owl.ttl'}")

    elif generator == 'jsonldcontext':
        logging.info("Proceeding with LinkML to JSON-LD Context conversion")
        context_generator = ContextGenerator(schema_view.schema, mergeimports=True)
        (output_dir / 'context.jsonld').write_text(context_generator.serialize())
        logging.info(f"JSON-LD context saved to {output_dir / 'context.jsonld'}")

    elif generator == 'linkml':
        logging.info("Proceeding with LinkML to LinkML YAML conversion (merged)")
        linkml_generator = LinkmlGenerator(schema_view.schema, mergeimports=True, format='yaml')
        (output_dir / 'linkml.yaml').write_text(linkml_generator.serialize())
        logging.info(f"Merged LinkML schema saved to {output_dir / 'linkml.yaml'}")

    else:
        logging.warning(f"Unknown generator: {generator}")


def run_pipeline(
    input_path: Path,
    *,
    generate_docs: bool = False,
    assertions_csv_path: Optional[Path] = None,
    extra_asserts_path: Optional[Path] = None,
) -> None:
    schema_view = SchemaView(input_path, merge_imports=True)
    logging.info(f"Input schema {input_path} loaded successfully!")

    for generator in RESOURCE_GENERATORS:
        output_dir = GENS_PATH / generator
        logging.info(f"Proceeding with WoT resource generation for {generator}")
        _run_linkml_generator(schema_view, generator, output_dir)

    generate_visualizations(SCHEMA_PATH, GENS_PATH / "visualization")

    if generate_docs:
        logging.info("Starting ReSpec specification generation...")
        generate_respec_spec(
            input_path,
            RESPEC_TEMPLATE_PATH,
            FINAL_SPEC_PATH,
            CORE_SCHEMA_PLACEHOLDER,
            assertions_csv_path=assertions_csv_path or ASSERTION_PATH,
            extra_asserts_path=extra_asserts_path,
        )
        logging.info("ReSpec specification generation complete.")

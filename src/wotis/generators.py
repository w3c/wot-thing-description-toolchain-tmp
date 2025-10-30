import json
import logging
from pathlib import Path

from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml.generators.shaclgen import ShaclGenerator
from linkml.generators.owlgen import OwlSchemaGenerator
from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml.generators.linkmlgen import LinkmlGenerator
from linkml_runtime.utils.schemaview import SchemaView


def run_generator(schema_view: SchemaView, generator: str, output_dir: Path):
    """
    Runs the LinkML generator (JSON Schema, SHACL, OWL, JSON-LD Context,
    or LinkML YAML) and saves the output to the designated directory.

    :param schema_view: The loaded SchemaView object.
    :param generator: The name of the generator to run (e.g., 'jsonschema').
    :param output_dir: The target output directory.
    """
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

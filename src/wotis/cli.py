"""Command line interface for WoTIS."""
import click
import json
import logging
import subprocess
import yaml

from pathlib import Path

from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml.generators.shaclgen import ShaclGenerator
from linkml.generators.owlgen import OwlSchemaGenerator
from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml.generators.docgen import DocGenerator
from linkml.generators.linkmlgen import LinkmlGenerator
from linkml_runtime.utils.schemaview import SchemaView

from src.wotis import (YAML_SCHEMA_PATH, GENS_PATH, GENERATORS,
                       RESPEC_TEMPLATE_PATH, RESPEC_FRAGMENT_PATH, FINAL_SPEC_PATH,
                       CORE_SCHEMA_PLACEHOLDER, RDF_DEFINITIONS_PLACEHOLDER_V1)

from src.wotis.postprocessors.jsonld_context_postprocessor import post_process_jsonld_context
from src.wotis.postprocessors.jsonschema_postprocessor import post_process_jsonschema

CUSTOM_TEMPLATE_DIR = Path(__file__).parent.parent.parent / 'templates'


input_option = click.option('-i', '--input_schema',
                            type=str,
                            show_default=True,
                            help="Path to the input schema specified as LinkML yaml.",
                            default=YAML_SCHEMA_PATH)
respec_option = click.option('-r',
                             '--generate_spec',
                             type=bool,
                             is_flag=True,
                             default=False,
                             show_default=True,
                             help="Boolean for generating the final Respec HTML specification.")


def serve_documentation():
    subprocess.run(['mkdocs', 'serve'], check=True)


def assemble_respec_spec(template_path: Path, final_path: Path):
    """
    Reads the Respec template and saves it directly to the final path.
    """
    logging.info("Assembling final Respec specification (Simple Copy)...")

    if not template_path.exists():
        logging.error(f"Respec template not found at {template_path}. Cannot assemble spec.")
        return
    respec_template = template_path.read_text(encoding='utf-8')
    final_path.write_text(respec_template, encoding='utf-8')
    logging.info(f"Final Respec specification saved to {final_path}")


def generate_respec_spec(input_path: Path, gens_path: Path):
    """
    Generates the Respec specification by simply copying the template.
    We only need the path to the template and the desired final output path.
    """
    assemble_respec_spec(RESPEC_TEMPLATE_PATH, FINAL_SPEC_PATH)


def run_generator(schema_view, generator, output_dir):
    if generator == 'jsonschema':
        logging.info(f"Proceeding with LinkML to JSON Schema convertion")
        json_schema_generator = JsonSchemaGenerator(schema_view.schema, mergeimports=True)
        processed_content  = json_schema_generator.serialize()
        #processed_content = post_process_jsonschema(schema_view, raw_content)
        output_file = output_dir / 'jsonschema.json'
        with output_file.open('w', encoding='utf-8') as f:
            json.dump(processed_content, f, indent=2, ensure_ascii=False)
        logging.info(f"Post-processed JSON Schema saved to {output_file}")
    elif generator == 'shacl':
        logging.info(f"Proceeding with LinkML to SHACL convertion")
        shacl_generator = ShaclGenerator(schema_view.schema, mergeimports=False, closed=True, suffix='Shape')
        (output_dir / 'shapes.shacl.ttl').write_text(shacl_generator.serialize())
    elif generator == 'owl':
        logging.info(f"Proceeding with LinkML to OWL convertion")
        owl_generator = OwlSchemaGenerator(schema_view.schema, )
        (output_dir / 'ontology.owl.ttl').write_text(owl_generator.serialize())
    elif generator == 'jsonldcontext':
        logging.info(f"Proceeding with LinkML to JSON-LD Context convertion")
        context_generator = ContextGenerator(schema_view.schema, mergeimports=True)
        (output_dir / 'context.jsonld').write_text(context_generator.serialize())
        # (output_dir / 'context.jsonld').write_text(post_process_jsonld_context(schema_view,
        #                                                                        context_generator.serialize()))
    elif generator == 'linkml':
        linkml_generator = LinkmlGenerator(schema_view.schema, mergeimports=True, format='yaml', output='linkml.yaml')
        (output_dir / 'linkml.yaml').write_text(linkml_generator.serialize())
    else:
        print(f"Unknown generator: {generator}")


@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet")
def main(verbose: int, quiet: bool):
    """CLI for WOTIS (Web of Things Integrated Schemas) toolchain.

    :param verbose: Verbosity while running.
    :param quiet: Boolean to be quiet or verbose.
    """
    logger = logging.getLogger()
    if verbose >= 2:
        logger.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logger.setLevel(level=logging.INFO)
    else:
        logger.setLevel(level=logging.WARNING)
    if quiet:
        logger.setLevel(level=logging.ERROR)
    logger.info(f"Logger {logger.name} set to level {logger.level}")


@main.command()
@input_option
@respec_option
def generate_wot_resources(input_schema: str, generate_spec: bool):
    """
    Generating WoT resources (RDF, JSON-LD Context, SHACL Shapes, and JSON Schema)
    and the final Respec specification from LinkML schemas.
    """
    input_path = Path(input_schema)
    if not input_path.exists():
        raise FileNotFoundError(f"Cannot find input LinkML schema file {input_schema}.")

    try:
        linkml_schema_view = SchemaView(input_path, merge_imports=True)
        logging.info(f"Input schema {input_schema} loaded successfully!")

        for generator in GENERATORS:
            output_dir = GENS_PATH / generator
            output_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Proceeding with WoT resource generation for {generator}")
            run_generator(linkml_schema_view, generator, output_dir)

        if generate_spec:
            generate_respec_spec(input_path, GENS_PATH)

    except yaml.YAMLError as e:
        logging.error(f"LinkML schema validation failed: {e}")


if __name__ == "__main__":
    main()
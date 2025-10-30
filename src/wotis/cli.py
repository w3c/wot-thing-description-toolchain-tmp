import click
import logging
import subprocess
import yaml

from pathlib import Path

from .generators import run_generator as run_standard_generator
from .respec_doc_generator import generate_respec_spec

from linkml_runtime.utils.schemaview import SchemaView

from src.wotis import (YAML_SCHEMA_PATH, GENS_PATH, GENERATORS,
                       RESPEC_TEMPLATE_PATH, FINAL_SPEC_PATH,
                       CORE_SCHEMA_PLACEHOLDER)

from src.wotis.postprocessors.jsonld_context_postprocessor import post_process_jsonld_context
from src.wotis.postprocessors.jsonschema_postprocessor import post_process_jsonschema


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
            logging.info(f"Proceeding with WoT resource generation for {generator}")
            run_standard_generator(linkml_schema_view, generator, output_dir)

        if generate_spec:
            logging.info("Starting Respec specification generation...")
            generate_respec_spec(
                input_path,
                GENS_PATH,
                RESPEC_TEMPLATE_PATH,
                FINAL_SPEC_PATH,
                CORE_SCHEMA_PLACEHOLDER
            )
            logging.info("Respec specification generation complete.")

    except yaml.YAMLError as e:
        logging.error(f"LinkML schema validation failed: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during resource generation: {e}", exc_info=True)


if __name__ == "__main__":
    main()

"""Command line interface for WoTIS."""

import click
import logging
from pathlib import Path
import subprocess

import yaml
from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml.generators.shaclgen import ShaclGenerator
from linkml.generators.owlgen import OwlSchemaGenerator
from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml.generators.docgen import DocGenerator
from linkml.generators.linkmlgen import LinkmlGenerator
from linkml_runtime.utils.schemaview import SchemaView

from src import YAML_SCHEMA_PATH, GENS_PATH, GENERATORS, DOCDIR


input_option = click.option('i', '--input_schema', help="Path to the input schema specified as LinkML yaml.", default=YAML_SCHEMA_PATH)
docs_option = click.option('-d', '--generate_docs', help="Boolean for local documentation generation.")
serve_docs_option = click.option('-s', '--serve_docs', help="Boolean for serving the generated documentation.")


# Documentation serving function
def serve_docs():
    subprocess.run(['mkdocs', 'serve'], check=True)


def generate_docs():
    DOCDIR.mkdir(parents=True, exist_ok=True)
    doc_generator = DocGenerator(YAML_SCHEMA_PATH, mergeimports=False)
    doc_generator.serialize(directory=str(DOCDIR))


# Main generation function
def run_generator(schema_view, generator, output_dir):
    if generator == 'jsonschema':
        logging.info(f"JSON Schema generation")
        # json_schema_generator = JsonSchemaGenerator(yaml_content, top_class="Thing")
        json_schema_generator = JsonSchemaGenerator(schema_view.schema, mergeimports=True)
        (output_dir / 'jsonschema.json').write_text(json_schema_generator.serialize())
    elif generator == 'shacl':
        shacl_generator = ShaclGenerator(schema_view.schema, mergeimports=False, closed=True, suffix='Shape')
        (output_dir / 'shapes.shacl.ttl').write_text(shacl_generator.serialize())
    elif generator == 'owl':
        owl_generator = OwlSchemaGenerator(schema_view.schema, )
        (output_dir / 'ontology.owl.ttl').write_text(owl_generator.serialize())
    elif generator == 'jsonldcontext':
        context_generator = ContextGenerator(schema_view.schema, mergeimports=True)
        # (output_dir / 'context.jsonld').write_text(post_process_jsonld_context(linkml_schema_view,
        #                                                                        context_generator.serialize()))
    elif generator == 'linkml':
        linkml_generator = LinkmlGenerator(schema_view.schema, mergeimports=True, format='yaml',
                                           output='linkml.yaml')
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
@docs_option
@serve_docs_option
def generate_wot_resources(input_schema, generate_docs, serve_docs):
    """
    Toolchain for generating WoT resources (RDF, JSON-LD Context, SHACL Shapes, and JSON Schema) from manually
    constructed LinkML-based schemas.
    """
    if input_schema and not Path(input_schema).exists():
        raise FileNotFoundError(f"Cannot find input LinkML schema file {input_schema}.")
    elif not input_schema and not YAML_SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Cannot find the default LinkML schema file {YAML_SCHEMA_PATH}.")
    else:
        try:
            linkml_schema_view = SchemaView(input_schema, merge_imports=True)
            logging.info(f"Input schema {input_schema} loaded successfully!")
            for generator in GENERATORS:
                output_dir = GENS_PATH / generator
                output_dir.mkdir(parents=True, exist_ok=True)
                logging.info(f"Proceeding with WoT resource generation")
                run_generator(linkml_schema_view, generator, output_dir)
        except yaml.YAMLError as e:
            logging.info(f"LinkML schema validation failed: {e}")
        if generate_docs:
            generate_docs()
        if serve_docs:
            serve_docs()


if __name__ == "__main__":
    main()

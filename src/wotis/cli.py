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
                       RESPEC_TEMPLATE_PATH, FINAL_SPEC_PATH,
                       CORE_SCHEMA_PLACEHOLDER)

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


def generate_doc_fragment(schema_view: SchemaView, output_dir: Path) -> Path:
    """
    Generates the documentation files using the custom Jinja template
    and the LinkML DocGenerator, saving them into the specified output_dir.
    Returns the path to the generated directory. (Kept for other uses, but bypassed for Respec)
    """
    logging.info("Generating documentation fragments using DocGenerator...")

    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    doc_generator = DocGenerator(
        schema=schema_view.schema,
        directory=CUSTOM_TEMPLATE_DIR,
        gen_slots=False,
        gen_classvars=True
    )

    doc_generator.serialize(output_dir)
    logging.info(f"Documentation fragments saved to directory: {output_dir}")
    return output_dir


def assemble_respec_spec(template_path: Path, fragment_content: str, final_path: Path, placeholder: str):
    """
    Reads the Respec template and injects the pre-formatted content into the final HTML spec.

    NOTE: The 'fragment_content' here is the final HTML table string.
    """
    logging.info("Assembling final Respec specification by injecting pre-formatted content...")

    if not template_path.exists():
        logging.error(f"Respec template not found at {template_path}. Cannot assemble spec.")
        return

    respec_template = template_path.read_text(encoding='utf-8')

    if placeholder not in respec_template:
        logging.error(
            f"Placeholder '{placeholder}' was NOT found in the template: {template_path}. "
            f"This is why the replacement failed and the placeholder is still visible."
        )
        return

    final_content = respec_template.replace(placeholder, fragment_content)

    final_path.write_text(final_content, encoding='utf-8')
    logging.info(f"Final Respec specification saved to {final_path}. Injected content length: {len(fragment_content)}.")


def generate_respec_spec(input_path: Path, gens_path: Path):
    """
    Generates the documentation fragment and assembles the final Respec specification.
    This function now generates the table content directly as HTML.
    """
    try:
        linkml_schema_view = SchemaView(input_path, merge_imports=True)
    except yaml.YAMLError as e:
        logging.error(f"Failed to load LinkML schema for Respec generation: {e}")
        return

    CLASS_NAME = 'Thing'
    class_def = linkml_schema_view.get_class(CLASS_NAME)

    if not class_def:
        logging.error(f"Class '{CLASS_NAME}' not found in the schema. Cannot generate table.")
        return

    # Using the "def numbered" class from the STTL template for styling
    html_table = (
        '<table class="def numbered">\n'
        '  <caption>Table 3 Vocabulary Terms in Thing Level</caption>\n'
        '  <thead>\n'
        '    <tr>\n'
        '      <th>Vocabulary term</th>\n'
        '      <th>Description</th>\n'
        '      <th>Assignment</th>\n'
        '      <th>Type</th>\n'
        '    </tr>\n'
        '  </thead>\n'
        '  <tbody>\n'
    )

    def get_assignment(slot_name, slot_def):
        # Check for slot_usage override first
        slot_usage = class_def.slot_usage.get(slot_name) if class_def.slot_usage else None

        if slot_def.required or (slot_usage and slot_usage.required):
            return 'mandatory'

        # Check for minimum_value requirement (cardinality 1..* etc.)
        min_value = slot_def.minimum_value
        if slot_usage and slot_usage.minimum_value is not None:
            min_value = slot_usage.minimum_value

        if min_value is not None and min_value > 0:
            return 'mandatory'

        return 'optional'

    for slot_name in class_def.slots:
        slot_def = linkml_schema_view.get_slot(slot_name)

        description = slot_def.description or ""

        range_name = slot_def.range

        if slot_name in ['@context', '@type']:
            if slot_name == '@context':
                range_text = 'anyURI or Array'
            else:  # @type
                range_text = 'string or Array of string'
        else:
            range_text = range_name

        is_multivalued = slot_def.multivalued
        if slot_def.inlined:
            range_text = f'Map of {range_name}'
        elif is_multivalued:
            range_text = f'{range_name} (Array)'

        assignment = get_assignment(slot_name, slot_def)

        # Updated: Using the "rfc2119-table-assertion" class from the STTL template for styling
        html_table += (
            f'    <tr class="rfc2119-table-assertion">\n'
            f'      <td><code>{slot_name}</code></td>\n'
            f'      <td>{description.replace("'", "&#39;").replace('"', '&quot;')}</td>\n'  # Escape quotes for HTML
            f'      <td>{assignment}</td>\n'
            f'      <td>{range_text}</td>\n'
            f'    </tr>\n'
        )

    html_table += (
        '  </tbody>\n'
        '</table>\n'
    )

    logging.info(f"Generated HTML table for '{CLASS_NAME}' slots. Length: {len(html_table)} characters.")
    logging.debug(f"Generated HTML Table Content:\n{html_table}")
    assemble_respec_spec(RESPEC_TEMPLATE_PATH, html_table, FINAL_SPEC_PATH, CORE_SCHEMA_PLACEHOLDER)


def run_generator(schema_view, generator, output_dir):
    if generator == 'jsonschema':
        logging.info(f"Proceeding with LinkML to JSON Schema convertion")
        json_schema_generator = JsonSchemaGenerator(schema_view.schema, mergeimports=True)
        processed_content = json_schema_generator.serialize()
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
            # Rerun Respec generation with custom table logic
            generate_respec_spec(input_path, GENS_PATH)

    except yaml.YAMLError as e:
        logging.error(f"LinkML schema validation failed: {e}")


if __name__ == "__main__":
    main()

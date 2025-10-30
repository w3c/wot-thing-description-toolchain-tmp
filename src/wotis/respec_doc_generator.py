import logging
import yaml

from jinja2 import Environment, FileSystemLoader, exceptions
from linkml_runtime.utils.schemaview import SchemaView
from pathlib import Path

from src.wotis import JINJA_TEMPLATE_DIR


def get_assignment(slot_name: str, class_def: object, slot_def: object) -> str:
    """
    Determines the assignment (mandatory/optional) for a slot based on LinkML properties
    and slot_usage overrides within the class.

    :param slot_name: The name of the slot.
    :param class_def: The LinkML ClassDefinition object.
    :param slot_def: The LinkML SlotDefinition object.
    :return: 'mandatory' or 'optional'.
    """

    slot_usage = class_def.slot_usage.get(slot_name) if class_def.slot_usage else None

    # Check 'required' property on slot or slot_usage
    if slot_def.required or (slot_usage and slot_usage.required):
        return 'mandatory'

    # Check for minimum_value requirement (cardinality 1..* etc.)
    min_value = slot_def.minimum_value
    if slot_usage and slot_usage.minimum_value is not None:
        min_value = slot_usage.minimum_value

    if min_value is not None and min_value > 0:
        return 'mandatory'

    # Default to optional for all others
    return 'optional'


def assemble_respec_spec(template_path: Path, fragment_content: str, final_path: Path, placeholder: str):
    """
    Reads the Respec template and injects the pre-formatted content into the final HTML spec.

    :param template_path: Path to the Respec HTML template.
    :param fragment_content: The HTML fragment (the table) to inject.
    :param final_path: Path to save the final Respec HTML file.
    :param placeholder: The placeholder string to replace in the template.
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


def generate_respec_spec(input_path: Path, respec_template_path: Path, final_spec_path: Path,
                         core_schema_placeholder: str):
    """
    Generates the custom HTML table for the 'Thing' class and assembles the
    final Respec specification using Jinja2 templates.

    :param input_path: Path to the input LinkML schema file.
    :param respec_template_path: Path to the Respec HTML template.
    :param final_spec_path: Path to save the final Respec HTML file.
    :param core_schema_placeholder: The placeholder string in the template.
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

    slot_data = []

    for slot_name in class_def.slots:
        slot_def = linkml_schema_view.get_slot(slot_name)

        description = slot_def.description or ""

        # Determine the Type text for the table, based on STTL
        if slot_name == '@context':
            range_text = 'anyURI or Array'
        elif slot_name == '@type':
            range_text = 'string or Array of string'
        else:
            range_name = slot_def.range
            is_multivalued = slot_def.multivalued
            if slot_def.inlined:
                range_text = f'Map of {range_name}'
            elif is_multivalued:
                range_text = f'{range_name} (Array)'
            else:
                range_text = range_name

        assignment = get_assignment(slot_name, class_def, slot_def)
        escaped_description = description.replace("'", "&#39;").replace('"', '&quot;')
        slot_data.append({
            'slot_name': slot_name,
            'description': escaped_description,
            'assignment': assignment,
            'range_text': range_text
        })

    try:
        if not JINJA_TEMPLATE_DIR.is_dir():
            raise exceptions.TemplateNotFound(
                f"Template directory not found: {JINJA_TEMPLATE_DIR}. Please ensure 'resources/jinja_templates' exists.")
        env = Environment(loader=FileSystemLoader(JINJA_TEMPLATE_DIR), autoescape=True)
        template = env.get_template('thing_table.jinja2')
        html_table = template.render(slots=slot_data)

    except exceptions.TemplateNotFound as e:
        logging.error(f"Jinja2 template rendering failed: {e}", exc_info=True)
        html_table = f"<!-- ERROR: Failed to render HTML table via Jinja2: {e} -->"
    except Exception as e:
        logging.error(f"Jinja2 environment setup failed: {e}", exc_info=True)
        html_table = f"<!-- ERROR: Failed to render HTML table via Jinja2: {e} -->"
    logging.info(f"Generated HTML table fragment via Jinja2. Length: {len(html_table)} characters.")

    assemble_respec_spec(respec_template_path, html_table, final_spec_path, core_schema_placeholder)

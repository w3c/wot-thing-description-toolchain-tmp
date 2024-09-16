import json
import logging

from linkml_runtime.linkml_model.meta import AnonymousSlotExpression
from linkml_runtime.utils.schemaview import SchemaView

XSD_NS = "http://www.w3.org/2001/XMLSchema#"


def process_langstring_conditions(slot, context_entry):
    """
    Handles 'langString' and 'exactly_one_of' language conditions for a slot.
    """
    is_langstring = slot.range == 'langString'
    is_exactly_one_language = (
            slot.range is None and
            any(
                expr.range == 'langString'
                for expr in slot.exactly_one_of if isinstance(expr, AnonymousSlotExpression)
            )
    )
    if is_langstring or (is_exactly_one_language and isinstance(context_entry, dict)):
        context_entry['@container'] = '@language'
        context_entry.pop('@type', None)
    return context_entry


def process_multivalued_slots(slot, context_entry):
    """
    Handles multivalued slots and applies the '@set' container.
    """
    if slot.multivalued and isinstance(context_entry, dict) and '@container' not in context_entry:
        context_entry['@container'] = '@set'
        context_entry.pop('@type', None)
    return context_entry


def process_inlined_slot(slot, context_entry):
    """
    Processes slots that are both inlined, multi-valued and have a instantiates fields.
    """
    if slot.inlined and slot.multivalued and not slot.inlined_as_list and isinstance(context_entry, dict):
        context_entry['@container'] = '@index'
        context_entry['@type'] = '@id'
        if slot.instantiates:
            context_entry['@index'] = slot.instantiates
    return context_entry


def process_exactly_one_of(slot, context_entry):
    """
    Handles the 'exactly_one_of' condition for a slot, determining its type.
    """
    if hasattr(slot, 'exactly_one_of') and slot.exactly_one_of:
        ranges = [opt['range'] for opt in slot.exactly_one_of if 'range' in opt]
        if len(set(ranges)) == 1:
            context_entry["@type"] = f"{XSD_NS}:{ranges[0]}"
        else:
            logging.warning(f"Warning: Slot {slot.name} has different ranges")
    return context_entry


def post_process_jsonld_context(schema_view: SchemaView, serialized_schema: str) -> str:
    """
    Post-processes a JSON-LD context generated from the default LinkML generators.
    """
    logging.info(f"Proceeding with JSON-LD Context postprocessor")
    serialized_schema_json = json.loads(serialized_schema)
    generated_context = serialized_schema_json.get('@context', {})
    default_range = schema_view.schema.default_range if schema_view.schema.default_range else "string"
    for slot in schema_view.all_slots().values():
        slot_name = slot.name
        context_entry = generated_context.get(slot_name, {})
        # Process language conditions
        context_entry = process_langstring_conditions(slot, context_entry)
        # Add @language for LinkML in_language slot
        if slot.in_language and isinstance(context_entry, dict):
            context_entry['@language'] = slot.in_language
        # Handle slots that are dict objects
        context_entry = process_inlined_slot(slot, context_entry)
        # Handle the @id for slots with exactly_one_of field
        context_entry = process_exactly_one_of(slot, context_entry)
        # Handles default range type
        if slot.range == default_range:
            context_entry["@type"] = f"{XSD_NS}:{default_range}"
        generated_context[slot_name] = context_entry

    # Intentionally handle multivalued slots separately after other processing
    for slot in schema_view.all_slots().values():
        context_entry = generated_context.get(slot.name, {})
        context_entry = process_multivalued_slots(slot, context_entry)
        generated_context[slot.name] = context_entry
    return json.dumps(serialized_schema_json, indent=3)

import json
import logging
from pyld import jsonld

from src.wotis import YAML_SCHEMA_PATH, GENS_PATH, MANUAL_PATH

logger = logging.getLogger(__name__)


def load_jsonld_context(file_path):
    """Loads and validates a JSON-LD context file using PyLD."""
    try:
        with open(file_path, 'r') as f:
            context_data = json.load(f)
        jsonld.expand(context_data)
        logger.info(f"{file_path} is a valid JSON-LD document.")
        return context_data
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Failed to load JSON-LD file {file_path}: {e}")
    except jsonld.JsonLdError as e:
        logger.error(f"Validation failed for {file_path}: {e}")
    return None


def deep_compare_dicts(manual_context_data, generated_context_data):
    """Recursively compares two dictionaries."""
    same = {}
    missing = {}
    extra = {}

    for key in manual_context_data:
        if key in generated_context_data:
            if isinstance(manual_context_data[key], dict) and isinstance(generated_context_data[key], dict):
                # Recursively compare nested dictionaries
                same_nested, missing_nested, extra_nested = deep_compare_dicts(manual_context_data[key], generated_context_data[key])
                if same_nested:
                    same[key] = same_nested
                if missing_nested:
                    missing[key] = missing_nested
                if extra_nested:
                    extra[key] = extra_nested
            elif manual_context_data[key] == generated_context_data[key]:
                same[key] = manual_context_data[key]
            else:
                missing[key] = manual_context_data[key]
                extra[key] = generated_context_data[key]
        else:
            missing[key] = manual_context_data[key]

    for key in generated_context_data:
        if key not in manual_context_data:
            extra[key] = generated_context_data[key]

    return same, missing, extra


def compare_contexts(manual_context, generated_context):
    """Compares two JSON-LD contexts and returns deep differences."""
    manual_context_data = manual_context.get('@context', {})
    generated_context_data = generated_context.get('@context', {})
    return deep_compare_dicts(manual_context_data, generated_context_data)


def test_context(manual_file, generated_file):
    """Loads and compares two JSON-LD contexts."""
    manual_context = load_jsonld_context(manual_file)
    generated_context = load_jsonld_context(generated_file)
    if manual_context is None or generated_context is None:
        logger.error("One of the JSON-LD contexts is invalid, comparison aborted.")
        return
    same_nodes, missing_in_generated, extra_in_generated = compare_contexts(manual_context, generated_context)
    logger.info("Nodes that are exactly the same and correct:")
    for node, value in same_nodes.items():
        logger.info(f"{node}: {value}")
    logger.info("Nodes missing from the generated context:")
    for node, value in missing_in_generated.items():
        logger.info(f"{node}: {value}")
    logger.info("Extra nodes in the generated context:")
    for node, value in extra_in_generated.items():
        logger.info(f"{node}: {value}")


if __name__ == "__main__":
    manual_file = f"{MANUAL_PATH}/context.jsonld"
    generated_file = f"{GENS_PATH}/jsonldcontext/context.jsonld"
    test_context(manual_file, generated_file)

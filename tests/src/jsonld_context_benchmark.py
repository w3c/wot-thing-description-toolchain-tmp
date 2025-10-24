import json
import logging

from typing import Any, Dict, Tuple
from pyld import jsonld

from src.wotis import GENS_PATH, MANUAL_PATH


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def load_jsonld_context(file_path: str) -> Dict[str, Any] | None:
    """Loads and validates a JSON-LD context file using PyLD."""
    try:
        with open(file_path, 'r') as f:
            context_data = json.load(f)
        # Attempt to expand to ensure it is valid JSON-LD
        jsonld.expand(context_data)
        logger.info(f"File {file_path} is a valid JSON-LD document.")
        return context_data
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Failed to load JSON-LD file {file_path}: {e}")
    except jsonld.JsonLdError as e:
        logger.error(f"Validation failed for {file_path}: {e}")
    return None


def deep_compare_dicts(
        manual_context_data: Dict[str, Any],
        generated_context_data: Dict[str, Any]
) -> Tuple[Dict, Dict, Dict, Dict]:
    """
    Recursively compares two dictionaries for exact matches, mismatches,
    missing keys (in generated), and extra keys (in generated).
    """
    same = {}
    missing = {}  # Keys in manual, but NOT in generated
    extra = {}  # Keys in generated, but NOT in manual
    mismatched = {}  # Keys in both, but values are different

    all_keys = set(manual_context_data.keys()) | set(generated_context_data.keys())

    for key in all_keys:
        in_manual = key in manual_context_data
        in_generated = key in generated_context_data

        # Case 1: Key only in manual (Missing in generated)
        if in_manual and not in_generated:
            missing[key] = manual_context_data[key]
            continue

        # Case 2: Key only in generated (Extra in generated)
        if in_generated and not in_manual:
            extra[key] = generated_context_data[key]
            continue

        # Case 3: Key in both (Check for same, nested, or mismatch)
        manual_val = manual_context_data[key]
        generated_val = generated_context_data[key]

        if isinstance(manual_val, dict) and isinstance(generated_val, dict):
            same_nested, missing_nested, extra_nested, mismatched_nested = deep_compare_dicts(manual_val, generated_val)

            # Only record the key if there are differences or if it's perfectly the same (for full report)
            if same_nested or missing_nested or extra_nested or mismatched_nested:
                if missing_nested or extra_nested or mismatched_nested:
                    mismatched[key] = {
                        "manual": manual_val,
                        "generated": generated_val,
                        "details": {
                            "missing": missing_nested,
                            "extra": extra_nested,
                            "mismatched": mismatched_nested
                        }
                    }
                else:
                    same[key] = manual_val

        elif manual_val == generated_val:
            same[key] = manual_val

        else:
            # Case 4: Key in both, but values are different (the core collision issue)
            mismatched[key] = {
                "manual": manual_val,
                "generated": generated_val
            }

    # Note: For nested dictionary keys that are perfectly equal, they are reported in 'same' by the recursion
    return same, missing, extra, mismatched


def compare_contexts(manual_context: Dict[str, Any], generated_context: Dict[str, Any]) -> Tuple[
    Dict, Dict, Dict, Dict]:
    """Compares the @context block of two JSON-LD documents."""
    manual_context_data = manual_context.get('@context', {})
    generated_context_data = generated_context.get('@context', {})
    return deep_compare_dicts(manual_context_data, generated_context_data)


def generate_report(manual_file: str, generated_file: str):
    """Loads, compares, and prints a structured report of context differences."""
    manual_context = load_jsonld_context(manual_file)
    generated_context = load_jsonld_context(generated_file)

    if manual_context is None or generated_context is None:
        return

    same, missing, extra, mismatched = compare_contexts(manual_context, generated_context)

    print("\n" + "=" * 80)
    print(f"JSON-LD Context Comparison Report: {manual_file} vs {generated_file}")
    print("=" * 80)

    def print_section(title, data):
        """Prints a section of the comparison report."""
        if data:
            print(f"\n--- {title} ({len(data)} items) ---")
            for key, value in data.items():
                if key != "@context":
                    print(f"[{key}]")
                    if isinstance(value, dict) and "generated" in value:
                        print("  MANUAL:    ", json.dumps(value['manual'], indent=None, sort_keys=True))
                        print("  GENERATED: ", json.dumps(value['generated'], indent=None, sort_keys=True))
                    else:
                        print("  VALUE:     ", json.dumps(value, indent=None, sort_keys=True))

    print_section("EXACT MATCHES", same)
    print_section("MISMATCHED DEFINITIONS (Key in both, values differ)", mismatched)
    print_section("MISSING IN GENERATED (In Manual only)", missing)
    print_section("EXTRA IN GENERATED (In LinkML only)", extra)
    print("-" * 80)
    print(f"Comparison complete. Total Keys Compared: {len(same) + len(mismatched) + len(missing) + len(extra)}.")


if __name__ == "__main__":
    try:
        manual_file = str(MANUAL_PATH / "context.jsonld")
        generated_file = str(GENS_PATH / "jsonldcontext" / "context.jsonld")
        generate_report(manual_file, generated_file)
    except ImportError as e:
        logger.error(
            f"Critical Error: Could not import paths from src.wotis. Ensure your Python path is set correctly: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during report generation: {e}")
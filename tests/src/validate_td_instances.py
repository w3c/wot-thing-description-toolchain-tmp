import json
from pathlib import Path
from typing import Dict, List, Tuple
import jsonschema
import click

def load_schema(schema_path: Path) -> dict:
    """Load the JSON Schema from the specified path."""
    return json.loads(schema_path.read_text())

def find_td_files(test_data_dir: Path) -> List[Tuple[Path, bool]]:
    """
    Find all TD instance files in the test data directory.
    Returns a list of tuples (file_path, expected_valid) where expected_valid
    is determined from the filename.
    """
    td_files = []
    for json_file in test_data_dir.rglob('*.jsonld'):
        if json_file.name == 'README.txt':
            continue
        # Determine if the file should be valid based on its name
        expected_valid = 'invalid' not in json_file.name.lower()
        td_files.append((json_file, expected_valid))
    return td_files

def validate_td(schema: dict, benchmark_schema: dict, td_path: Path) -> Tuple[bool, bool, str]:
    """
    Validate a TD instance against both schemas.
    Returns (is_valid_generated, is_valid_benchmark, error_message).
    """
    try:
        td_instance = json.loads(td_path.read_text())
        
        # Validate against generated schema
        try:
            jsonschema.validate(instance=td_instance, schema=schema)
            is_valid_generated = True
        except jsonschema.exceptions.ValidationError as e:
            is_valid_generated = False
            error_generated = str(e)
            
        # Validate against benchmark schema
        try:
            jsonschema.validate(instance=td_instance, schema=benchmark_schema)
            is_valid_benchmark = True
            error = "" if is_valid_generated else f"Generated schema rejected but benchmark accepted: {error_generated}"
        except jsonschema.exceptions.ValidationError as e:
            is_valid_benchmark = False
            if is_valid_generated:
                error = f"Generated schema accepted but benchmark rejected: {str(e)}"
            else:
                error = ""  # Both rejected, which is expected for invalid files
                
        return is_valid_generated, is_valid_benchmark, error
        
    except json.JSONDecodeError as e:
        return False, False, f"Invalid JSON: {str(e)}"
    except Exception as e:
        return False, False, f"Unexpected error: {str(e)}"

def print_results(results: Dict[str, List[Tuple[Path, bool, bool, bool, str]]]) -> None:
    """Print validation results in a structured format."""
    total_files = sum(len(files) for files in results.values())
    total_matches = sum(
        sum(1 for _, _, gen_valid, bench_valid, _ in files if gen_valid == bench_valid)
        for files in results.values()
    )
    
    print("\nValidation Results:")
    print("=" * 80)
    
    for category, files in sorted(results.items()):
        print(f"\n{category}:")
        print("-" * 80)
        for file_path, expected, gen_valid, bench_valid, error in sorted(files, key=lambda x: x[0].name):
            status = "✓" if gen_valid == bench_valid else "✗"
            gen_result = "valid" if gen_valid else "invalid"
            bench_result = "valid" if bench_valid else "invalid"
            expected_str = "valid" if expected else "invalid"
            
            print(f"{status} {file_path.name}")
            print(f"  Expected: {expected_str}")
            print(f"  Generated Schema: {gen_result}")
            print(f"  Benchmark Schema: {bench_result}")
            if error:
                print(f"  Error: {error}")
        print("-" * 80)
    
    accuracy = (total_matches / total_files) * 100 if total_files > 0 else 0
    print(f"\nSchema Comparison Statistics:")
    print(f"Total files tested: {total_files}")
    print(f"Matching validation results: {total_matches}")
    print(f"Validation consistency: {accuracy:.2f}%")

@click.command()
@click.option(
    '--schema',
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help='Path to the generated JSON Schema file'
)
@click.option(
    '--benchmark-schema',
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help='Path to the benchmark JSON Schema file'
)
@click.option(
    '--test-data',
    required=True,
    type=click.Path(exists=True, dir_okay=True, path_type=Path),
    help='Path to the test data directory'
)
def main(schema: Path, benchmark_schema: Path, test_data: Path) -> None:
    """Validate TD instances against both the generated and benchmark JSON Schemas."""
    # Load schemas
    try:
        json_schema = load_schema(schema)
        benchmark = load_schema(benchmark_schema)
        print(f"Loaded schemas from {schema} and {benchmark_schema}")
    except Exception as e:
        print(f"Error loading schemas: {e}")
        return

    td_files = find_td_files(test_data)
    if not td_files:
        print(f"No TD instances found in {test_data}")
        return
    
    print(f"Found {len(td_files)} TD instances to validate")
    results: Dict[str, List[Tuple[Path, bool, bool, bool, str]]] = {}
    
    for file_path, expected_valid in td_files:
        dir_name = file_path.parent.name
        if dir_name not in results:
            results[dir_name] = []
        gen_valid, bench_valid, error = validate_td(json_schema, benchmark, file_path)
        results[dir_name].append((file_path, expected_valid, gen_valid, bench_valid, error))
    
    print_results(results)

if __name__ == '__main__':
    main()
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, TypeAlias
import jsonschema
from jsonschema.validators import validator_for
import click
from rich.console import Console
from rich.table import Table

# Type aliases
ValidationResult: TypeAlias = Tuple[bool, bool, str]
FileResults: TypeAlias = List[Tuple[Path, bool, bool, bool, str]]
ResultsDict: TypeAlias = Dict[str, FileResults]

@dataclass
class ValidationStats:
    """Statistics from validation results."""
    total_files: int = 0
    matching_results: int = 0
    
    @property
    def consistency(self) -> float:
        """Calculate the consistency percentage between schemas."""
        return (self.matching_results / self.total_files * 100) if self.total_files > 0 else 0.0

class SchemaValidator:
    """Handles JSON Schema validation for TD instances."""
    
    def __init__(self, schema: dict, benchmark: dict) -> None:
        """Initialize with both schemas and create validators."""
        # Create validators with format checking
        schema_cls = validator_for(schema)
        schema_cls.check_schema(schema)
        benchmark_cls = validator_for(benchmark)
        benchmark_cls.check_schema(benchmark)
        
        self.schema_validator = schema_cls(schema)
        self.benchmark_validator = benchmark_cls(benchmark)
        self.console = Console()

    def validate_td(self, td_path: Path) -> ValidationResult:
        """Validate a TD instance against both schemas."""
        try:
            td_instance = json.loads(td_path.read_text(encoding='utf-8'))
            
            # Validate against generated schema
            try:
                self.schema_validator.validate(td_instance)
                is_valid_generated = True
                error_generated = ""
            except jsonschema.exceptions.ValidationError as e:
                is_valid_generated = False
                error_generated = str(e)
            
            # Validate against benchmark schema
            try:
                self.benchmark_validator.validate(td_instance)
                is_valid_benchmark = True
                error = "" if is_valid_generated else f"Generated schema rejected but benchmark accepted: {error_generated}"
            except jsonschema.exceptions.ValidationError as e:
                is_valid_benchmark = False
                error = f"Generated schema accepted but benchmark rejected: {str(e)}" if is_valid_generated else ""
            
            return is_valid_generated, is_valid_benchmark, error
            
        except json.JSONDecodeError as e:
            return False, False, f"Invalid JSON: {str(e)}"
        except Exception as e:
            return False, False, f"Unexpected error: {str(e)}"

    def find_td_files(self, test_data_dir: Path) -> List[Tuple[Path, bool]]:
        """Find all TD instance files in the test data directory."""
        td_files = []
        for json_file in test_data_dir.rglob('*.jsonld'):
            if json_file.name == 'README.txt':
                continue
            expected_valid = 'invalid' not in json_file.name.lower()
            td_files.append((json_file, expected_valid))
        return td_files

    def print_results(self, results: ResultsDict) -> None:
        """Print validation results using rich tables."""
        stats = ValidationStats()
        stats.total_files = sum(len(files) for files in results.values())
        stats.matching_results = sum(
            sum(1 for _, _, gen_valid, bench_valid, _ in files if gen_valid == bench_valid)
            for files in results.values()
        )
        
        # Create and style the results table
        table = Table(title="Validation Results")
        table.add_column("File", style="cyan")
        table.add_column("Expected", style="blue")
        table.add_column("Generated Schema", style="green")
        table.add_column("Benchmark Schema", style="yellow")
        table.add_column("Status", style="bold")
        table.add_column("Error", style="red")
        
        for category, files in sorted(results.items()):
            table.add_section()
            table.add_row(f"[bold]{category}[/bold]", "", "", "", "", "")
            
            for file_path, expected, gen_valid, bench_valid, error in sorted(files, key=lambda x: x[0].name):
                status = "✓" if gen_valid == bench_valid else "✗"
                table.add_row(
                    file_path.name,
                    "valid" if expected else "invalid",
                    "valid" if gen_valid else "invalid",
                    "valid" if bench_valid else "invalid",
                    status,
                    error or ""
                )
        
        self.console.print(table)
        
        # Print statistics
        stats_table = Table(title="Schema Comparison Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Total files tested", str(stats.total_files))
        stats_table.add_row("Matching validation results", str(stats.matching_results))
        stats_table.add_row("Validation consistency", f"{stats.consistency:.2f}%")
        
        self.console.print(stats_table)

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
    console = Console()
    
    try:
        # Load schemas
        with schema.open(encoding='utf-8') as f:
            json_schema = json.load(f)
        with benchmark_schema.open(encoding='utf-8') as f:
            benchmark = json.load(f)
            
        console.print(f"[green]Loaded schemas from {schema} and {benchmark_schema}[/green]")
        
        validator = SchemaValidator(json_schema, benchmark)
        td_files = validator.find_td_files(test_data)
        
        if not td_files:
            console.print(f"[yellow]No TD instances found in {test_data}[/yellow]")
            return
        
        console.print(f"[green]Found {len(td_files)} TD instances to validate[/green]")
        
        # Process validation results
        results: ResultsDict = {}
        for file_path, expected_valid in td_files:
            dir_name = file_path.parent.name
            if dir_name not in results:
                results[dir_name] = []
            
            gen_valid, bench_valid, error = validator.validate_td(file_path)
            results[dir_name].append((file_path, expected_valid, gen_valid, bench_valid, error))
        
        validator.print_results(results)
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise click.Abort()

if __name__ == '__main__':
    main()
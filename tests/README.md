# WoTIS Testing

This directory contains test files and validation tools for the WoT Thing Description toolchain.

## TD Instance Validation

The `validate_td_instances.py` script provides functionality to validate TD instances against both the generated JSON Schema and a benchmark schema. This helps ensure that our generated schema maintains compatibility with the WoT TD specification.

### Usage

```bash
python src/validate_td_instances.py --schema <path-to-generated-schema> --benchmark-schema <path-to-benchmark-schema> --test-data <path-to-test-data-dir>
```

#### Arguments

- `--schema`: Path to the generated JSON Schema file (default: resources/gens/jsonschema/jsonschema.json)
- `--benchmark-schema`: Path to the benchmark JSON Schema file (default: resources/benchmark_schemas/td-json-schema-validation.json)
- `--test-data`: Path to the directory containing TD instance files to validate

### Features

- **Dual Schema Validation**: Validates TD instances against both the generated schema and a benchmark schema
- **CLI Output**: Provide validation results
- **Validation Statistics**: Shows statistics about schema compatibility and validation consistency
- **Detailed Error Reporting**: Provides detailed error messages when validation fails

### Example Output

The script provides a detailed table showing:
- File paths and their validation status
- Expected validity of each file
- Validation results from both schemas
- Detailed error messages when validation fails
- Overall statistics including total files tested and validation consistency

### Test Data Organization

The `data` directory contains TD instance files organized in subdirectories based on their test categories:
- `6-security-schemas/`: TD instances testing security configurations
- `7-complex-data-schemas/`: TD instances with complex data schema structures
- `8-meta-interactions/`: TD instances testing meta-interactions
- `9-versioning/`: TD instances testing versioning features

### Adding New Tests

To add new test cases:
1. Create a TD instance file with `.jsonld` extension
2. Place it in an appropriate subdirectory under `tests/data/`
3. Name the file to indicate whether it should be valid or invalid:
   - Valid TD instances: `*-td-valid.jsonld`
   - Invalid TD instances: `*-td-invalid.jsonld` 
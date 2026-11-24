# Command-line interface

```bash
wot-toolchain [-v | -vv | -q] generate-wot-resources [OPTIONS]
wot-toolchain [-v | -vv | -q] diff-report GENERATED REFERENCE
```

In a checkout, prefix each command with `uv run`.

## Global options

| Option | Effect |
|---|---|
| `-v`, `--verbose` | Log `INFO` messages; `-vv` also logs `DEBUG` messages. |
| `-q`, `--quiet` | Log only errors. |

Without either option, warnings and errors are logged.

## `generate-wot-resources`

Runs the generators of the project that a [config file](config-file.md) describes.

| Option | Effect |
|---|---|
| `-c`, `--config FILE` | Config file, relative to the current directory. Default: `wot-toolchain.yaml`. |
| `-i`, `--input_schema FILE` | LinkML schema to use instead of the config file's `root_schema`. |
| `--output-dir DIRECTORY` | Directory for the generated artifacts instead of the config file's `output_dir`, relative to the current directory. |
| `--only GENERATOR` | Run only this generator; repeat the option for several. The generator must be listed under `generators` in the config file. |

Each generator writes into `<output_dir>/<generator>/`, for example `resources/gens/jsonschema/`.
The `spec` generator is the exception: it writes the specification HTML and the assertion CSV to the paths in `generators.spec.output` and `generators.spec.assertions_csv`, and `--output-dir` does not move them.
`spec` runs after the other generators. It needs Bikeshed, which is installed with the toolchain; `visualization` needs Graphviz `dot` on `PATH`. A missing program is reported before anything is generated.

Exit status: 0 on success; 1 on an error of the toolchain (config file, schema, generation or missing program), logged as an `ERROR` line; 2 on a usage error, for example an `--only` generator that the config file does not list.

## `diff-report`

```bash
wot-toolchain diff-report resources/gens/jsonschema/jsonschema.json tests/snapshots/jsonschema.json
```

Prints a Markdown report of the JSON paths that were added, removed or changed in `GENERATED` relative to `REFERENCE`: first a table of counts, then the paths.
Differences do not fail the command, so its output can be appended to `$GITHUB_STEP_SUMMARY`. It exits with 1 only if a file cannot be read or is not valid JSON.

# Getting started

The toolchain has no knowledge of the Thing Description built into its code. A project brings its own LinkML schemas and a config file that says what to generate.
To change the Thing Description vocabulary, see [Editing schemas](editing-schemas/first-change.md). To work on the toolchain itself, see [Contribute to the tool](contributing/setup.md).

## Requirements

- Python 3.14 and [uv](https://docs.astral.sh/uv/).
- [Graphviz](https://graphviz.org/download/), for the class diagrams.

## Install

The toolchain is not published on PyPI. Install a tagged release:

```bash
uv tool install git+https://github.com/w3c/wot-thing-description-toolchain-tmp@<tag>
```

## Write a config file

A minimal project needs one schema and one config file, `wot-toolchain.yaml`. This one is in the toolchain repository as [`tests/fixtures/mini-project/`](https://github.com/w3c/wot-thing-description-toolchain-tmp/tree/main/tests/fixtures/mini-project):

```
mini-project/
  wot-toolchain.yaml
  schemas/
    sensor.yaml
```

```yaml
root_schema: schemas/sensor.yaml
output_dir: gens

vocabularies:
  - schema: schemas/sensor.yaml
    prefix: sen
    context: sensor-context.jsonld

generators:
  jsonschema:
    top_class: Sensor
    id: https://example.org/sensor
    description: A tiny vocabulary unrelated to the Thing Description, used to test the toolchain.
    dialect: "2019-09"
    output: jsonschema.json
  jsonldcontext:
```

- `root_schema` is the schema the generators read, together with the schemas it imports.
- `vocabularies` lists each schema with its prefix and the file names of what is generated from it.
- `generators` lists the generators to run. A generator without settings, like `jsonldcontext:`, only needs its key.

Paths are relative to the config file. Every key is described in the [Config file](reference/config-file.md) reference.

## Run

From the project directory:

```bash
wot-toolchain generate-wot-resources
```

Use `-c path/to/wot-toolchain.yaml` to run from elsewhere. The run writes:

```
gens/jsonschema/jsonschema.json
gens/jsonldcontext/context.jsonld
gens/jsonldcontext/sensor-context.jsonld
```

A `WARNING` line reports a problem worth looking at, but the run goes on; an `ERROR` line means the run failed, and the command exits with status 1. All commands and options are in the [CLI](reference/cli.md) reference.

## Next

- More generators: add `shacl:`, `owl:`, `visualization:` or `linkml:` under `generators`. An ontology or a diagram also needs an `ontology:` or `diagram:` file name on the vocabulary.
- A specification: add `spec:` with a template, sections and snippets. The repository's own [`wot-toolchain.yaml`](https://github.com/w3c/wot-thing-description-toolchain-tmp/blob/main/wot-toolchain.yaml) is a full example.
- In CI, `wot-toolchain diff-report` compares a generated JSON file with a committed one; see [`diff-report`](reference/cli.md#diff-report).

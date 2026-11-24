# Use from another repository

The toolchain holds no knowledge of the Thing Description in its Python code: a project brings its own LinkML schemas and a [config file](../reference/config-file.md) that says what to generate.
The first such project is meant to be `w3c/wot-thing-description`, with its schemas under `linkml/`.

## A minimal project

`tests/fixtures/mini-project/` is a complete project that is not the Thing Description. `tests/test_second_project.py` runs the toolchain on it.

```
mini-project/
  wot-toolchain.yaml
  schemas/
    sensor.yaml
```

`schemas/sensor.yaml` is an ordinary LinkML schema with two classes, `Sensor` and `Reading`, in the namespace `sen:`.
The config file names it as the root schema, declares it as one vocabulary, and lists two generators:

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

Paths in the file are relative to the file. `jsonldcontext:` has no settings; listing the key is enough to run the generator.

## Run it

Install a tagged release and run it from the project directory:

```bash
uv tool install git+https://github.com/w3c/wot-thing-description-toolchain-tmp@<tag>
cd mini-project
wot-toolchain generate-wot-resources
```

This writes:

```
gens/jsonschema/jsonschema.json
gens/jsonldcontext/context.jsonld
gens/jsonldcontext/sensor-context.jsonld
```

## Add more

- More generators: add `shacl:`, `owl:`, `visualization:` or `linkml:` under `generators`. For an ontology or a diagram, also give the vocabulary an `ontology:` or `diagram:` file name.
- A specification: add `spec:` with a template, sections and snippets. The repository's own [`wot-toolchain.yaml`](https://github.com/w3c/wot-thing-description-toolchain-tmp/blob/main/wot-toolchain.yaml) is a full example.
- In CI, `wot-toolchain diff-report` compares a generated JSON file with a committed one; see the [CLI reference](../reference/cli.md#diff-report).

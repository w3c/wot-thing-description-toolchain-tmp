# Install

## Requirements

- Python 3.14 and [uv](https://docs.astral.sh/uv/).
- [Graphviz](https://graphviz.org/), with `dot` on `PATH`, for the class diagrams.
- For some tests only: Node.js with the `jsonld` package (`npm install --no-save jsonld` at the repository root), and [ROBOT](https://robot.obolibrary.org/) on `PATH` or in `ROBOT_BIN`. See [Testing](../internals/testing.md).

Bikeshed, used by the `spec` generator, is installed with the toolchain.

## Work on a checkout

```bash
git clone https://github.com/w3c/wot-thing-description-toolchain-tmp.git
cd wot-thing-description-toolchain-tmp
uv sync --locked
uv run pre-commit install
```

`pre-commit install` activates the hooks in `.pre-commit-config.yaml`: ruff and ruff-format on Python files, and linkml-lint on `thing_description.yaml`, `hypermedia.yaml`, `wot_security.yaml` and `jsonschema.yaml` when a file under `resources/schemas/` changes.

## Get the reference files in `resources/upstream/`

`resources/upstream/` holds the artifacts published with TD 1.1: schemas, contexts, ontologies, shapes, the specification HTML and its assertion inventory.
The tests compare against them, and `wot-toolchain.yaml` names two of its schemas in `generators.spec.snippet_validation_schemas`.
The directory is not tracked by git. Without it the config file does not load, and every command fails with `ERROR: .../wot-toolchain.yaml: .../resources/upstream/schemas/td-next-json-schema-validation.json does not exist`.

Until the files get a new home, restore the last tracked copy from history:

```bash
git restore --source=b93bf44~1 -- resources/upstream
```

## Run the toolchain

```bash
uv run wot-toolchain generate-wot-resources
uv run pytest tests/
```

Each run prints `WARNING` lines about slots left out of the `hctl`, `wotsec` and `jsonschema` diagrams. They appear on an unchanged checkout too. An `ERROR` line means the run failed, and the command exits with status 1.

The outputs land under `resources/gens`: `index.html`, `assertions/assertions.csv`, `jsonschema/jsonschema.json`, `jsonldcontext/*.jsonld`, `owl/*.ttl`, `shacl/shapes.shacl.ttl`, `visualization/*.svg` and the merged schema `linkml/linkml.yaml`. Do not edit them. The options of every command are in the [CLI reference](../reference/cli.md).

## Install a release in another repository

The toolchain is not published on PyPI. A repository that owns LinkML schemas and a config file installs a tagged release:

```bash
uv tool install git+https://github.com/w3c/wot-thing-description-toolchain-tmp@<tag>
wot-toolchain generate-wot-resources -c path/to/wot-toolchain.yaml
```

[Use from another repository](using-from-another-repo.md) walks through a minimal project.

## Preview these pages

```bash
uv run --group docs python scripts/gen_config_docs.py
uv run --group docs zensical serve
```

The first command generates the [config file reference](../reference/config-file.md). The second serves the site at <http://127.0.0.1:8000/> and rebuilds on every change under `docs/`.

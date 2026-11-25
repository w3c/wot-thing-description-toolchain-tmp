# Set up a checkout

This section is for people who work on the toolchain itself: its Python code, its tests and these pages. To use the toolchain in your own repository, see [Getting started](../getting-started.md) instead.

## Install

You need the [requirements](../getting-started.md#requirements) from Getting started. Clone the repository and install the toolchain with its pre-commit hooks:

```bash
git clone https://github.com/w3c/wot-thing-description-toolchain-tmp.git
cd wot-thing-description-toolchain-tmp
uv sync --locked
uv run pre-commit install
```

The hooks run ruff on Python files, and linkml-lint on the vocabulary schemas when a file under `resources/schemas/` changes.

In a checkout, prefix each `wot-toolchain` command with `uv run`.

## Restore `resources/upstream/`

`resources/upstream/` holds the artifacts published with TD 1.1. The tests compare against them, and `wot-toolchain.yaml` needs two of them. The directory is not tracked by git; until it gets a new home, restore it from history:

```bash
git restore --source=b93bf44~1 -- resources/upstream
```

Without it, every command fails with `ERROR: .../wot-toolchain.yaml: .../resources/upstream/schemas/td-next-json-schema-validation.json does not exist`.

## Generate and test

```bash
uv run wot-toolchain generate-wot-resources
uv run pytest tests/
```

The outputs land under `resources/gens`; do not edit them. Each run prints `WARNING` lines about slots left out of the `hctl`, `wotsec` and `jsonschema` diagrams; they are expected. How the tests are organised, and what to do when one fails, is in [Testing](testing.md).

## Tools for the tests

Some tests need more than the requirements above:

- Node.js with the `jsonld` package: run `npm install --no-save jsonld` at the repository root. Without it, the JSON-LD round-trip tests fail with `Cannot find module`.
- [ROBOT](https://robot.obolibrary.org/) on `PATH` or in `ROBOT_BIN`. Without it, the OWL profile test is skipped locally; it runs in CI.

## The Thing Description files in this repository

Until they move to [`w3c/wot-thing-description`](https://github.com/w3c/wot-thing-description), the Thing Description schemas, specification template and snippets live here: `resources/schemas/`, `resources/index.template.html` and `resources/snippets/`. The [Editing schemas](../editing-schemas/first-change.md) pages already describe the layout they will have there, with the schemas under `linkml/`.

## Preview these pages

```bash
uv run --group docs python scripts/gen_config_docs.py
uv run --group docs zensical serve
```

The first command generates the [config file reference](../reference/config-file.md). The second serves the site at <http://127.0.0.1:8000/> and rebuilds on every change under `docs/`. How the pages are organised is described in `CONTRIBUTING.md`.

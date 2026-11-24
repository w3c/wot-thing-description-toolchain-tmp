# Contributing to wot-toolchain

This repository is maintained by the
[W3C Web of Things (WoT) Working Group](https://www.w3.org/groups/wg/wot/).
It generates the JSON Schema, JSON-LD context, SHACL shapes, OWL ontologies,
specification HTML, assertion CSV files and diagrams of the WoT Thing
Description vocabulary from LinkML schemas.

## W3C contribution context

Contributions are made in the context of the W3C Web of Things Working Group
and are subject to the W3C Patent Policy and the IPR commitments that apply to
the group. See the [Working Group page](https://www.w3.org/groups/wg/wot/) for
participation and IPR information. Code in this repository is distributed under
the repository license.

## Development setup

Requirements:

- Python 3.14 or later
- [uv](https://docs.astral.sh/uv/)
- [Graphviz](https://graphviz.org/) (the `dot` program) for the diagram
  generator. When the config file enables the `visualization` generator,
  generation stops with an error before writing any output if `dot` is not on
  `PATH`; `--only` can exclude that generator.
- [Node.js](https://nodejs.org/) with the `jsonld` package installed in
  `node_modules/`, only for the JSON-LD round-trip tests.

`bikeshed`, used to build the specification HTML, is a Python dependency and
is installed by uv.

Install the locked environment:

```bash
uv sync --locked
```

Optionally install the pre-commit hooks (`ruff`, `ruff-format`, and
`linkml-lint` on the schema files):

```bash
pre-commit install
```

## Running the generator

```bash
uv run wot-toolchain generate-wot-resources
```

The command reads the project config file `wot-toolchain.yaml` and runs every
generator listed under `generators`, including `spec` (the specification HTML
and assertion CSV). The artifacts are written to `resources/gens/`. Options:

| Option | Meaning |
|---|---|
| `-c`, `--config FILE` | Project config file (default: `wot-toolchain.yaml`) |
| `-i`, `--input_schema FILE` | LinkML schema to use instead of the config file's `root_schema` |
| `--output-dir DIRECTORY` | Write the artifacts to this directory instead of the config file's `output_dir` |
| `--only GENERATOR` | Run only this generator of the config file's `generators`; repeat for several |

Global options `-v`/`--verbose` and `-q`/`--quiet` go before the command name.
Run `uv run wot-toolchain --help` for details. The command exits with a
non-zero status if generation fails.

Do not edit files under `resources/gens/`; they are overwritten on every run.

## Tests and lint

Integration tests read the generated artifacts, so run the generator first:

```bash
uv run wot-toolchain generate-wot-resources
uv run pytest
uv run ruff check .
```

See [tests/README.md](tests/README.md) for what each test module covers.
Failures are investigated, not skipped. Expected failures are listed in
`tests/known_failures/` and marked as strict expected failures, so an entry
must be removed once its test passes.

### Snapshots

`tests/snapshots/` holds committed copies of the generated output. They are
updated only deliberately, after a schema or generator change whose effect on
the artifacts you have reviewed:

```bash
uv run pytest tests/test_golden_diff.py --update-goldens
```

Commit the updated snapshots together with the change that caused them and
explain the diff in the pull request so reviewers can check it. Do not edit
snapshot files by hand, and do not update them to silence an unexplained
failure.

## Modeling changes

- The LinkML schemas in `resources/schemas/` are the single source of truth.
  Fix modeling problems (types, cardinalities, enumerations, descriptions)
  there, not in the code under `src/wot_toolchain/artifacts/`.
  That code only adjusts generator output that LinkML cannot express; see
  [Postprocessor Conventions](docs/internals/postprocessors.md).
- Schema changes must align with the
  [WoT Thing Description specification](https://www.w3.org/TR/wot-thing-description11/).
  A change that departs from the specification needs a reference to the
  corresponding Working Group issue or decision.
- Before editing a schema, read the
  [LinkML Naming Conventions](docs/reference/naming-conventions.md) and
  [WoT Custom Annotations](docs/reference/annotations.md).

## Documentation

The documents are published as a website built with [Zensical](https://zensical.org/).
Add a new document to `nav` in `zensical.toml`; a document missing from `nav` is still
built but does not appear in the navigation. Preview the site locally with:

```bash
uv run --group docs python scripts/gen_config_docs.py
uv run --group docs zensical serve
```

The first command generates `docs/reference/config-file.md` from the LinkML schema of the
config file, `src/wot_toolchain/schemas/config.yaml`. The page is not tracked: change the
schema's descriptions, or the template in `scripts/templates/config-docs/`, instead.
`uv run --group docs zensical build --strict` runs in CI after the same script and fails on
links to missing documents or anchors.

## Pull requests

- Keep each pull request focused on one issue and reference it
  (for example `fixes #123`).
- Make sure the generator and lint pass locally and that the change
  introduces no new test failures before requesting review.
- Describe any change to generated artifacts or snapshots in the pull request.
- Use the [issue tracker](https://github.com/w3c/wot-thing-description-toolchain-tmp/issues)
  to report problems or propose changes.

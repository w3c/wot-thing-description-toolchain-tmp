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

Install the toolchain, the pre-commit hooks, the reference files in
`resources/upstream/` and the test prerequisites as described in
[Set up a checkout](docs/contributing/setup.md). The commands and their options are
in the [CLI reference](docs/reference/cli.md). Do not edit files under
`resources/gens/`; they are overwritten on every run.

## Tests and lint

```bash
uv run wot-toolchain generate-wot-resources
uv run pytest
uv run ruff check .
```

Failures are investigated, not skipped. The expected-failure lists, the
snapshots in `tests/snapshots/` and when they may be updated are described in
[Testing](docs/contributing/testing.md). Before opening a pull request, go through
[Checking a change](docs/editing-schemas/checking-a-change.md).

## Modeling changes

- The LinkML schemas in `resources/schemas/` are the single source of truth.
  Fix modeling problems (types, cardinalities, enumerations, descriptions)
  there, not in the code under `src/wot_toolchain/artifacts/`.
  That code only adjusts generator output that LinkML cannot express; see
  [Postprocessor Conventions](docs/contributing/postprocessors.md).
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

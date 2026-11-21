# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `spec.snippet_validation_schemas` entries of the form `{generated: jsonschema}`
  validate snippets against the JSON Schema generated in the same run (honouring
  `--output-dir`); the run fails if `jsonschema` is not among its generators.
- Project manifest `wot-toolchain.yaml` describing the schemas, generators,
  modules and specification build. Select another manifest with
  `generate-wot-resources --config`.
- Typed errors in `wot_toolchain.errors` (`ManifestError`, `SchemaError`,
  `GenerationError`, `ExternalToolError`).
- `uv.lock` lockfile for reproducible environments (`uv sync --locked`).
- `generate-wot-resources --output-dir DIR` redirects the resource artifacts
  and `--only GENERATOR` runs a subset of the manifest's generators.
- The Jinja templates of the specification generator ship in the wheel, so
  the toolchain runs from an installed release without a checkout.
- `LICENSE.md`: W3C Software and Document License, as in
  `w3c/wot-thing-description`.

### Changed

- The snippet manifest picks each snippet's validation schema kind (per-snippet
  `schema`, else top-level `default_schema`) instead of the toolchain inspecting
  the snippet's `@type`; a validated snippet without a kind fails the build.
- Renamed the package to `wot-toolchain`: the import package is
  `wot_toolchain` and the command is `wot-toolchain`.
- `wot-toolchain generate-wot-resources` exits with a non-zero status when
  generation fails.
- The vocabulary version under development is named `td-next`; the reference
  schema `td20-json-schema-validation.json` is now
  `td-next-json-schema-validation.json`.
- Bikeshed is a declared dependency and runs as a module of the toolchain's
  own interpreter; it no longer has to be on `PATH`.
- The visualization generator writes SVG diagrams only; intermediate `.dot`
  files are no longer kept.

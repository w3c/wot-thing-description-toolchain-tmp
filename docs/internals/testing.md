# Testing

The tests live in `tests/`. How to check a schema change before opening a pull request is described in [Checking a change](../authoring/checking-a-change.md).

## Run the suite

Integration tests read generated artifacts. Generate them before running the
full suite:

```bash
uv run wot-toolchain generate-wot-resources
uv run pytest tests/ -v
```

`generate-wot-resources` also writes the specification HTML and assertion CSV
files used by the specification checks; `--only spec` runs that generator alone. Unit tests for the HTML rendering helpers use
their own fixtures and do not require generated output.

## Coverage

- `test_td_instance_gate.py` validates the generated JSON Schema against every
  valid and invalid TD sample in `tests/data/`.
- `test_td_crosscheck.py` compares the generated schema's validation verdicts
  with the W3C reference schemas in `resources/upstream/schemas/`.
- `test_golden_diff.py` detects changes to the generated JSON Schema, JSON-LD
  context, OWL modules, SHACL shapes, and generated specification sections.
- `test_golden_form_structure.py`, `test_spec_content_rendering.py`, and
  `test_default_assignments.py` check generated specification structure and
  HTML rendering behavior.
- `test_assertion_inventory.py` compares assertion counts, identifiers, and
  statuses with the upstream inventory, then checks each approved wording
  correction exactly.
- `test_spec_html_vs_golden.py` compares the four generated specification
  sections with `resources/upstream/html/index.html`. It also checks approved
  corrections, duplicate IDs, and in-page links.
- `test_snippet_schema.py`, `test_snippet_crossrefs.py`, and
  `test_snippet_vs_upstream.py` validate snippet metadata, references, and
  rendered examples. `test_snippet_rendering.py` checks the example markup
  rendered from snippet groups.
- `test_jsonld_context_composition.py`,
  `test_jsonld_context_upstream_comparison.py`, and `test_jsonld_roundtrip.py`
  check the generated JSON-LD contexts. The round-trip tests run `jsonld.js`
  and need Node.js with the `jsonld` package in `node_modules/`.
- `test_owl_structure.py` and `test_shacl_postprocessor.py` check the
  experimental OWL and SHACL outputs.
- `test_config.py`, `test_pipeline_project.py`, `test_spec_project.py`,
  `test_visualization_project.py`, `test_cli_options.py`, and
  `test_cli_exit_codes.py` check config file loading, CLI options, and error
  exits. `test_second_project.py` runs the toolchain on a LinkML project other
  than the Thing Description.
- `test_packaged_templates.py`, `test_declared_dependencies.py`,
  `test_wheel_layout.py`, and `test_installed_wheel.py` check the built
  package.
- `test_approved_divergences.py` validates the documents in
  `tests/approved_divergences/`, which record reviewed corrections to upstream text
  and generated snippets that were completed on purpose.

`baselines.py`, `rejections.py`, `conftest.py`, and `spec_html_compare.py` in `tests/`
are shared test helpers, not test modules.

## Reference Outputs

`resources/upstream/` contains the W3C reference artifacts used by comparison
tests: published schemas in `schemas/`, the assertion inventory in
`assertions.csv`, assertion source in `extra-asserts.html`, and the
hand-verified specification source in `html/index.html`.

### Snapshots

Snapshot tests catch accidental changes to what this toolchain produces. The
files in `tests/snapshots/` are committed copies of the toolchain's current
generated output — `jsonschema.json` (the JSON Schema), `context.jsonld` (the
JSON-LD context), `owl/*.ttl` (the OWL modules), `shapes.shacl.ttl` (the SHACL
shapes), and `spec-sections.html` (the specification HTML sections).

`test_golden_diff.py` regenerates each artifact and checks it is
character-for-character identical to the saved copy. Any difference — even a
single extra space — is a test failure.

**If a snapshot test fails and you did not change a schema or generator:** there
is a bug. Do not update the snapshots to silence it. Investigate the cause.

**If a snapshot test fails because you intentionally changed a schema or
generator:** review the diff to confirm the artifact change is correct, report
it in the pull request and get a maintainer's approval, then update the saved
copies:

```bash
uv run pytest tests/test_golden_diff.py --update-goldens
```

Commit the updated `tests/snapshots/` files in the same commit as the schema or
generator change. Do not edit files in `tests/snapshots/` by hand.

## Expected Failures

The only accepted failures are listed one per line in `tests/known_failures/`
(`td_gate.txt`, `td_crosscheck.txt`, `shacl_gate.txt`, `jsonld_roundtrip.txt`,
`spec_structure.txt`) and marked `xfail(strict=True)`. A listed case that starts
passing fails the suite until its entry is removed, so the lists can only
shrink. Reviewed divergences from upstream text and snippets are recorded in
`tests/approved_divergences/`.

Any other generated-schema rejection of a valid sample, mismatch between the
generated and the upstream schema, or HTML-structure regression fails its test
directly. Every failure needs a cause, even one that looks unrelated to the
change at hand.

## Update Policy

| Files | What they are | Updated |
|---|---|---|
| `resources/upstream/` | Artifacts published with TD 1.1, hand-verified | Never automatically; a change needs a maintainer's approval in the pull request |
| `tests/snapshots/` | Committed copies of the current generated output | With `--update-goldens`, after a maintainer approves the diff |
| `tests/known_failures/`, `tests/approved_divergences/` | Expected failures and reviewed divergences | Only with a maintainer's approval |

`--update-goldens` rewrites only `tests/snapshots/`.

## CI

`.github/workflows/main.yaml` runs three jobs in sequence:

| Job | What it does |
|---|---|
| `static-analysis` | Ruff lint and format check, mypy, LinkML schema lint (non-blocking), strict docs build |
| `build` | Installs Graphviz, runs `generate-wot-resources`, builds the package, and uploads the generated resources and the package |
| `tests` | Installs Graphviz, jsonld.js and ROBOT, downloads the generated resources and runs `uv run pytest` |

`tests/test_owl_profile.py` runs ROBOT from `ROBOT_BIN` or `PATH`; it is skipped locally when ROBOT is missing and fails on CI.

## Test Data

`tests/data/` contains TD instance files organized by the numbered TD specification
topic directories. Add a test case to the relevant directory and name it
`*-td-valid.jsonld` or `*-td-invalid.jsonld`; that suffix determines the
expected validation result.

## Migration Checks

`test_spec_html_vs_golden.py`, `test_assertion_inventory.py`,
`test_snippet_vs_upstream.py`, and `test_approved_divergences.py` compare
generated output with the published W3C Thing Description resources in
`resources/upstream/`. They support the migration to the W3C Thing Description
repository and are expected to move there with the schemas.

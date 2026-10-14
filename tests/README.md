# Testing

## Run the suite

Integration tests read generated artifacts. Generate them before running the
full suite:

```bash
uv run wotis generate-wot-resources -d
uv run pytest tests/ -v
```

The `-d` option generates the specification HTML and assertion CSV files used
by the specification checks. Unit tests for the HTML rendering helpers use
their own fixtures and do not require generated output.

## Coverage

- `test_td_instance_gate.py` validates the generated JSON Schema against every
  valid and invalid TD sample in `data/`.
- `test_td_crosscheck.py` compares the generated schema's validation verdicts
  with the W3C reference schemas in `resources/upstream/schemas/`.
- `test_golden_diff.py` detects changes to the generated JSON Schema, JSON-LD
  context, and generated specification sections.
- `test_golden_form_structure.py`, `test_spec_content_rendering.py`, and
  `tmp/test_default_assignments.py` check generated specification structure and
  HTML rendering behavior.
- `tmp/test_assertion_inventory.py` compares assertion counts, identifiers, and
  statuses with the upstream inventory, then checks each approved wording
  correction exactly.
- `tmp/test_spec_html_vs_golden.py` compares the four generated specification
  sections with `resources/upstream/html/index.html`. It also checks approved
  corrections, duplicate IDs, and in-page links.
- `test_snippet_schema.py`, `test_snippet_crossrefs.py`, and
  `tmp/test_snippet_vs_upstream.py` validate snippet metadata, references, and
  rendered examples.
- `tmp/test_approved_divergences.py` validates the documents in
  `approved_divergences/`, which record reviewed corrections to upstream text
  and deliberately complete generated snippets.

`baselines.py`, `rejections.py`, `conftest.py`, and `tmp/spec_html_compare.py`
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
JSON-LD context), and `spec-sections.html` (the specification HTML sections).
OWL modules and SHACL shapes will be added here as they are introduced.

`test_golden_diff.py` regenerates each artifact and checks it is
character-for-character identical to the saved copy. Any difference — even a
single extra space — is a test failure.

**If a snapshot test fails and you did not change a schema or generator:** there
is a bug. Do not update the snapshots to silence it. Investigate the cause.

**If a snapshot test fails because you intentionally changed a schema or
generator:** review the diff to confirm the artifact change is correct, then
update the saved copies:

```bash
uv run pytest tests/test_golden_diff.py --update-goldens
```

Commit the updated `tests/snapshots/` files in the same commit as the schema or
generator change. Do not edit files in `tests/snapshots/` by hand.

### Pre-commit checks

This repository uses [pre-commit](https://pre-commit.com/) hooks that run
automatically when you run `git commit`. Two hooks are active:

- **ruff** — checks and auto-fixes Python style in all `.py` files. If ruff
  modifies a file, stage the changes and commit again.
- **linkml-lint** — validates the four schema files under `resources/schemas/`
  whenever any of them change. If lint fails, fix the schema error it reports
  before committing.

These checks are separate from the snapshot tests but serve the same purpose:
prevent invalid or inconsistent changes from entering the repository unnoticed.

## Test Data

`data/` contains TD instance files organized by the numbered TD specification
topic directories. Add a test case to the relevant directory and name it
`*-td-valid.jsonld` or `*-td-invalid.jsonld`; that suffix determines the
expected validation result.

## Migration Checks

`tmp/` contains upstream-comparison tests and helpers that support the current
migration to the W3C Thing Description repository. They remain part of the
suite until their responsibilities move upstream. See `tmp/README.md`.

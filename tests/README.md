# Testing

## Run the suite

The tests in `conformance/` and `goldens/` read the files in `resources/gens/`
(except `goldens/test_approved_divergences.py`) and fail when a file is
missing. Generate the files before running the full suite:

```bash
uv run wot-toolchain generate-wot-resources
uv run pytest
```

The specification HTML is built when `spec` is listed under `generators` in
`wot-toolchain.yaml`.

## Layout

- `unit/` holds the tests that run without generated files: `cli/`,
  `artifacts/shacl/`, `snippets/`, `spec/`.
- `conformance/` validates the TD instances in `resources/td/` against the
  generated JSON Schema.
- `goldens/` compares generated output with the snapshots in
  `resources/snapshots/` and with the upstream files in `resources/upstream/`
  at the repository root.
- `resources/` holds test data only: `td/`, `snapshots/`,
  `approved_divergences/`.

## Coverage

- `conformance/test_valid_and_invalid_instances.py` validates the generated JSON Schema
  against every valid and invalid TD sample in `resources/td/`.
- `conformance/test_json_schema_vs_upstream.py` compares the generated schema's
  validation verdicts with the W3C td-next JSON Schema
  `resources/upstream/schemas/td20-json-schema-validation.json`.
- `goldens/test_snapshots.py` detects changes to the generated JSON Schema,
  JSON-LD context, and generated specification sections.
- `goldens/test_spec_form_sections.py` checks that the Form and
  ExpectedResponse sections of the generated specification contain the
  expected tables, operation types, and assertion ids.
- `unit/spec/test_spec_content_html.py` checks the HTML rendered from
  spec content blocks.
- `unit/spec/test_default_assignments.py` checks which table rows of the
  LinkML schemas are marked "with default".
- `goldens/test_assertion_inventory.py` compares assertion counts,
  identifiers, and statuses with the upstream inventory, then checks each
  approved wording correction exactly.
- `goldens/test_spec_html_vs_upstream.py` compares the four generated
  specification sections with `resources/upstream/html/index.html`. It also
  checks approved corrections, duplicate IDs, and in-page links.
- `unit/snippets/test_snippets_yaml.py`,
  `unit/snippets/test_snippet_ids.py`, and
  `goldens/test_snippet_vs_upstream.py` validate snippet metadata, references,
  and rendered examples.
- `goldens/test_approved_divergences.py` validates the documents in
  `resources/approved_divergences/`, which record reviewed corrections to
  upstream text and deliberately complete generated snippets.
- `unit/cli/test_cli.py` tests the command line interface and
  `unit/artifacts/shacl/test_shacl_postprocessor.py` tests the SHACL
  postprocessor.

`conftest.py`, `conformance/rejections.py`, and
`goldens/spec_html_compare.py` are shared test helpers, not test modules.

The upstream-comparison tests `test_spec_html_vs_upstream.py`,
`test_assertion_inventory.py`, `test_snippet_vs_upstream.py`, and
`test_approved_divergences.py` are removed when the toolchain merges into
w3c/wot-thing-description.

## Reference Outputs

`resources/upstream/` at the repository root contains the W3C reference
files that the comparison tests read: the td-next JSON Schema
`schemas/td20-json-schema-validation.json`, the assertion inventory `assertions.csv`, and the specification
`html/index.html`.

`resources/snapshots/` contains machine-updatable snapshots of this toolchain's
generated output. Update them only after reviewing an intentional change:

```bash
uv run pytest tests/goldens/test_snapshots.py --update-goldens
```

## Test Data

`resources/td/` contains the td-next TD instance files, one directory per topic
(`1-simple-default/` to `15-link-relation-type/`):

```
resources/td/<topic>/valid/<case>.jsonld     must be accepted
resources/td/<topic>/invalid/<case>.jsonld   must be rejected
```

`<case>` names what the instance shows, in lower-case words joined by `-`
(protocol and term names keep their spelling, e.g. `CoAP-hop-limit`,
`readOnly`). To add a test case, add one `*.jsonld` file to `valid/` or
`invalid/` of its topic; no Python change is needed.
`conformance/test_valid_and_invalid_instances.py` reads every `*.jsonld` file and fails
for a file outside a `valid/` or `invalid/` directory.

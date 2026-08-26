# WoTIS Testing

All tests run against the generated artifacts, so generate them first:

```bash
uv run wotis generate-wot-resources -d
uv run pytest tests/ -v
```

## What each test file checks

| File | Question it answers |
|---|---|
| `test_td_instance_gate.py` | Does the generated JSON Schema accept every valid sample in `data/` and reject every invalid one? |
| `test_td_crosscheck.py` | Does the generated JSON Schema give the same verdict as the W3C schemas in `resources/upstream/schemas/`? |
| `test_golden_diff.py` | Did the generated JSON Schema, JSON-LD context or the four generated spec sections change without us noticing? Compares with the snapshots in `snapshots/`. |
| `test_golden_form_structure.py` | Does the Form section of the generated HTML have the expected structure? |
| `test_spec_content_rendering.py` | Do the HTML rendering functions produce the expected markup? Uses fake input, does not read generated files. |
| `test_default_assignments.py` | Do the correct slots carry default-value assignments, and do enum value hints render as `<code>`-wrapped HTML? |
| `tmp/test_assertion_inventory.py` | Does our assertion id set match the upstream one in `resources/upstream/assertions.csv`? Reports only, never fails. |
| `tmp/test_spec_html_vs_golden.py` | Does the generated spec HTML match `resources/upstream/html/index.html` inside the four sections the pipeline generates? Fails today, so it is not run in CI. Also holds two integrity checks on the generated file alone (unique ids, resolvable in-page links). |

Helper modules, not test files: `baselines.py` (reads the known-failure lists,
derives TD 2.0 samples from TD 1.1 ones), `rejections.py` (groups schema
rejections for the CI report), `tmp/spec_html_compare.py` (DOM comparison used by
`tmp/test_spec_html_vs_golden.py` and `test_golden_diff.py`), `conftest.py` (shared options and the CI
summary).

## Upstream reference files

All W3C reference files live under `resources/upstream/`:

- `schemas/` — W3C published TD JSON Schemas (used by `test_td_crosscheck.py`)
- `assertions.csv` — upstream assertion inventory (used by `tmp/test_assertion_inventory.py`)
- `extra-asserts.html` — upstream assertion HTML source
- `html/index.html` — hand-verified upstream spec HTML (used by `tmp/test_spec_html_vs_golden.py`)

## Snapshots

`snapshots/` holds machine-updatable regression snapshots of our own generated output. Update with:

```bash
uv run pytest tests/test_golden_diff.py --update-goldens
```

Never update snapshots without understanding why the output changed.

## tmp/

Tests in `tmp/` are removed when the toolchain merges into `w3c/wot-thing-description`. See `tmp/README.md`.

## known_failures/

Lists of things that fail on purpose right now. A listed item is marked
`xfail(strict=True)`, so when it starts passing the test fails and the line has
to be removed. The lists can only shrink.

This directory is transitional. When all lists are empty, delete the directory.

## Test data

`data/` holds TD instance files, grouped by topic:

- `6-security-schemas/`: TD instances testing security configurations
- `7-complex-data-schemas/`: TD instances with complex data schema structures
- `8-meta-interactions/`: TD instances testing meta-interactions
- `9-versioning/`: TD instances testing versioning features

To add a test case, put a `.jsonld` file in the right subdirectory and name it
`*-td-valid.jsonld` or `*-td-invalid.jsonld`. The name decides what the test
expects, so it must be correct.

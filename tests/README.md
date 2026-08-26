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
| `test_td_crosscheck.py` | Does the generated JSON Schema give the same verdict as the W3C schemas in `resources/ground-truth-schemas/`? |
| `test_golden_diff.py` | Did the generated JSON Schema, JSON-LD context or the four generated spec sections change without us noticing? Compares with the snapshots in `goldens/`. |
| `test_spec_html_vs_golden.py` | Does the generated spec HTML match `manual_goldens/html/index.html` inside the four sections the pipeline generates? Fails today, so it is not run in CI. Also holds two integrity checks on the generated file alone (unique ids, resolvable in-page links). |
| `test_assertion_inventory.py` | Does our assertion id set match the upstream one in `resources/upstream/assertions.csv`? Reports only, never fails. |
| `test_golden_form_structure.py` | Does the Form section of the generated HTML have the expected structure? |
| `test_spec_content_rendering.py` | Do the HTML rendering functions produce the expected markup? Uses fake input, does not read generated files. |

Helper modules, not test files: `baselines.py` (reads the known-failure lists,
derives TD 2.0 samples from TD 1.1 ones), `rejections.py` (groups schema
rejections for the CI report), `spec_html_compare.py` (DOM comparison used by
`test_spec_html_vs_golden.py`), `conftest.py` (shared options and the CI
summary).

## Golden files

- `manual_goldens/` is hand-verified reference data. Never update it without
  maintainer approval.
- `goldens/` holds machine-updatable snapshots. Update with
  `uv run pytest tests/test_golden_diff.py --update-goldens` when a change is
  intended.

## known_failures/

Lists of things that fail on purpose right now. A listed item is marked
`xfail(strict=True)`, so when it starts passing the test fails and the line has
to be removed. The lists can only shrink.

This directory is transitional. When all lists are empty, delete the directory.

## Remove when the toolchain moves into wot-thing-description

The following exist only because the reference files live in another
repository. After a merge into `w3c/wot-thing-description` the repository is
its own reference, so they lose their meaning:

- `resources/upstream/`
- `test_assertion_inventory.py` — the upstream assertions.csv would then be the
  file we generate ourselves
- `test_spec_html_vs_golden.py` and `manual_goldens/` — the golden is a
  hand-adapted copy of the upstream index.html. `spec_html_compare.py` cannot
  go with them, `test_golden_diff.py` uses `generated_sections_html` from it
- `known_failures/` and the xfail wiring in `conftest.py`

## Test data

`data/` holds TD instance files, grouped by topic:

- `6-security-schemas/`: TD instances testing security configurations
- `7-complex-data-schemas/`: TD instances with complex data schema structures
- `8-meta-interactions/`: TD instances testing meta-interactions
- `9-versioning/`: TD instances testing versioning features

To add a test case, put a `.jsonld` file in the right subdirectory and name it
`*-td-valid.jsonld` or `*-td-invalid.jsonld`. The name decides what the test
expects, so it must be correct.

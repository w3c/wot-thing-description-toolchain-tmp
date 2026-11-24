# Checking a change

## Read the generation output

`uv run wot-toolchain generate-wot-resources` signals problems with `WARNING` and `ERROR` lines:

| Output | What to do |
|---|---|
| `WARNING: SCHEMA: slots not defined in this schema or its imports are left out of NAME.svg: ...` | Expected for `hypermedia.yaml`, `wot_security.yaml` and `jsonschema.yaml`: the diagram of that vocabulary leaves out the listed slots. Investigate it for any other schema. |
| Any other `WARNING:` line | Investigate. |
| `ERROR: N spec snippet(s) in DIR are invalid:`, followed by `FILE: PATH — MESSAGE [schema: ...]` or `FILE: invalid JSON` | Fix the snippet. It is not valid JSON, or fails the schema that `generators.spec.snippet_validation_schemas` names for it. |
| Any other `ERROR:` line | Fix it: generation failed. |

An `ERROR` makes the command exit with status 1.

## Compare with the snapshots and run the tests

Regenerate, then compare an output with its snapshot in `tests/snapshots`:

```sh
uv run wot-toolchain generate-wot-resources
uv run wot-toolchain diff-report resources/gens/jsonschema/jsonschema.json tests/snapshots/jsonschema.json
```

`diff-report` prints a Markdown table of added, removed and changed paths, then lists the paths. After the worked example and the new class, `/$defs/Firmware` and `/$defs/VersionInfo/properties/firmware` are listed as added. The command exits 0 even when it finds differences.

Run the tests with `uv run pytest tests/`. Some tests have prerequisites. `tests/test_owl_profile.py` reads `resources/gens/owl`, so generate first. `tests/test_jsonld_roundtrip.py` and `tests/test_jsonld_context_upstream_comparison.py` use the Node.js `jsonld` package and fail with `Cannot find module` when it is missing. The repository has no `package.json`. `npm install --no-save jsonld` at the repository root installs the package.

`tests/test_golden_diff.py` compares the generated outputs with the snapshots and reports each difference:

```
E       Failed: Generated jsonschema.json differs from the golden snapshot:
E       11 changes, 5 patterns
...
E           1  added    $.$defs.*   e.g. $.$defs.Firmware
E           1  added    $.$defs.*.properties.*   e.g. $.$defs.VersionInfo.properties.firmware
...
E       if the change is intended, update with --update-goldens.
```

Read the listed paths. If every change is one you intended, say so in the pull request: snapshots are updated only with a maintainer's approval. Then rewrite them with `uv run pytest tests/test_golden_diff.py --update-goldens` and commit them with the schema change. That run reports each test as skipped with `Golden updated: ...`. The next run passes. If a path changed that you did not expect, the change has a side effect: find it before updating anything.

Some tests are expected to fail. They are listed one per line in `tests/known_failures/` and marked `xfail(strict=True)`, so a listed case that starts passing fails the suite until its entry is removed. Reviewed divergences from upstream text and snippets are recorded in `tests/approved_divergences/`. Every other failure needs a cause, even when it looks unrelated to your change. See [Testing](../internals/testing.md).

## What counts as done

1. `uv run wot-toolchain generate-wot-resources` exits without an `ERROR`.
2. `uv run pytest tests/` passes, apart from the listed expected failures.
3. Every snippet linked to a changed class or slot validates. `validate: false` is only for examples that are not complete TDs or TMs.
4. The generated parts of `resources/gens/index.html` are right. Only the parts that replace `%` markers of the template, and changed `spec_content` or `spec_intro_content` blocks, need checking:
    - Every term in a vocabulary table matches the schema: name, description, type and whether it is mandatory or optional. A `required` slot must say mandatory.
    - The type column matches the range; check `spec_type_values` overrides with `mode: one_of` for completeness.
    - Class names match the LinkML class names exactly.
    - Each normative statement that should be an assertion has a `td-...` anchor that is unique in the document.
    - Normative references use ReSpec `[[RFC####]]` syntax, not bare URLs.

## Where to look next

The `spec_*` annotations that drive the specification tables: [annotations.md](../reference/annotations.md).

Where LinkML generators fall short of what the TD needs, and what the toolchain does about it: [linkml-gaps.md](../status/linkml-gaps.md).

How each generated artifact differs from the one published with TD 1.1, and the defects found in the published artifacts: [differences/](../status/differences/index.md).

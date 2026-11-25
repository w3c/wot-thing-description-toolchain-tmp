# Checking a change

## Read the generation output

`wot-toolchain generate-wot-resources` signals problems with `WARNING` and `ERROR` lines:

| Output | What to do |
|---|---|
| `WARNING: SCHEMA: slots not defined in this schema or its imports are left out of NAME.svg: ...` | Expected for `hypermedia.yaml`, `wot_security.yaml` and `jsonschema.yaml`: the diagram of that vocabulary leaves out the listed slots. Investigate it for any other schema. |
| Any other `WARNING:` line | Investigate. |
| `ERROR: N spec snippet(s) in DIR are invalid:`, followed by `FILE: PATH — MESSAGE [schema: ...]` or `FILE: invalid JSON` | Fix the snippet. It is not valid JSON, or fails the schema that `generators.spec.snippet_validation_schemas` names for it. |
| Any other `ERROR:` line | Fix it: generation failed. |

An `ERROR` makes the command exit with status 1.

## Compare with the previous output

Check that the change did what you meant and nothing else. Keep a copy of an artifact from before the change, regenerate, and compare the two with `diff-report`. Here `gens/` stands for the `output_dir` of `wot-toolchain.yaml`:

```bash
cp gens/jsonschema/jsonschema.json jsonschema-before.json
# change the schema, then:
wot-toolchain generate-wot-resources
wot-toolchain diff-report gens/jsonschema/jsonschema.json jsonschema-before.json
```

`diff-report` prints a Markdown table of added, removed and changed paths, then lists the paths. After the worked example and the new class, `/$defs/Firmware` and `/$defs/VersionInfo/properties/firmware` are listed as added. The command exits 0 even when it finds differences.

If a path changed that you did not expect, the change has a side effect: find it before you open a pull request.

## What counts as done

1. `wot-toolchain generate-wot-resources` exits without an `ERROR`.
2. The comparison with the previous output lists only the changes you intended.
3. Every snippet linked to a changed class or slot validates. `validate: false` is only for examples that are not complete TDs or TMs.
4. The generated parts of the specification HTML (`generators.spec.output`) are right. Only the parts that replace `%` markers of the template, and changed `spec_content` or `spec_intro_content` blocks, need checking:
    - Every term in a vocabulary table matches the schema: name, description, type and whether it is mandatory or optional. A `required` slot must say mandatory.
    - The type column matches the range; check `spec_type_values` overrides with `mode: one_of` for completeness.
    - Class names match the LinkML class names exactly.
    - Each normative statement that should be an assertion has a `td-...` anchor that is unique in the document.
    - Normative references use ReSpec `[[RFC####]]` syntax, not bare URLs.

## Where to look next

The `spec_*` annotations that drive the specification tables: [Specification annotations](../reference/annotations-spec.md).

How each generated artifact differs from the one published with TD 1.1, and the defects found in the published artifacts: [Differences from TD 1.1](../differences/index.md).

Where the LinkML generators fall short of what the TD needs, and what the toolchain does about it: [LinkML gaps](../contributing/linkml-gaps.md).

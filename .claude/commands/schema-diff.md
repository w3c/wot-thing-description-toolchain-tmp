Show schema-related changes in the working tree and summarize what kind of review is needed.

```bash
git diff resources/schemas/
```

After showing the diff, classify the change:
- **Slot added/removed** → JSON Schema, JSON-LD context, RDF ONTOLOGIES, SHACL all affected. Run `/validate-consistency`.
- **Annotation changed** (`spec_*`) → HTML spec output affected. Check annotation rules in AGENTS.md. Run `/generate`.
- **Range or cardinality changed** → JSON Schema and SHACL affected. Run `/validate-consistency` + TD instance gate.
- **Class added/removed** → All artifacts affected. Run `/validate-consistency` + full test suite.
- **Description changed only** → Low risk. Run `/generate` to confirm no rendering issues.

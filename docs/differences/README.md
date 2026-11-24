# Differences from the published TD 1.1 artifacts

This directory records, for each generated artifact, how it differs from the artifact published with TD 1.1 and kept in `resources/upstream/`, and the defects found in the published artifacts themselves.
It exists so that a reader can trace why generated output differs from the published output and see what was fixed here.

- [jsonld-context.md](jsonld-context.md): the JSON-LD context, against `resources/upstream/context/td-context-1.1.jsonld`.
- [json-schema.md](json-schema.md): the JSON Schema, against `resources/upstream/schemas/td11-json-schema-validation.json`.
- [shacl.md](shacl.md): the SHACL shapes, against `resources/upstream/validation/td-validation.ttl`, with data converted through `resources/upstream/context/td-context-1.1.jsonld`.
- [owl.md](owl.md): the OWL ontologies, against `td.ttl`, `hctl.ttl`, `wotsec.ttl`, `jsonschema.ttl` and `tm.ttl` in `resources/upstream/ontology/`.

Each file has a short introduction, then `## Method`, which names the published reference file or files, then `## Part 1: ...`, where the generated artifact differs from the published one, and `## Part 2: ...`, defects in the published artifact, including inconsistencies between published companion artifacts such as the context and the shapes.

Each entry is written in fixed paragraphs, in this order: Published, Generated, Effect, Cause and Status.
Cause is given only where it was established by experiment.

Two status words occur here. Undecided has the same meaning as at the top of [LinkML gaps](../linkml-gaps.md).

- Undecided: the generated artifact differs from the published one, and no decision has been taken. Every Part 1 entry has this status.
- Published defect: the published artifact is wrong against the TD 1.1 Recommendation or is inconsistent with a published companion artifact, for example the context with the shapes, and the generated artifact does not reproduce it. Every Part 2 entry has this status.

All comparisons are made on the output of `wot-toolchain generate-wot-resources` against the files in `resources/upstream/`.

How to change the schemas and regenerate the artifacts is described in the [authoring guide](../authoring-guide.md).

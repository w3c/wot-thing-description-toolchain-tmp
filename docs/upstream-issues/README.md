# Upstream LinkML issue drafts

Unfiled drafts. Each one is guarded by a canary in `tests/test_upstream_canaries.py` and was verified
against linkml 1.12.0 (linkml-runtime 1.12.0) on 2026-11-21. Bug vs. feature-gap labels are the
author's judgment, as stated in each draft.

- [01](01-jsonschema-designates-type-enum-crash.md): gen-json-schema crashes on a `designates_type` slot with an enum range.
- [02](02-rdfs-literal-type-emitted-as-datatype.md): context and SHACL emit `rdfs:Literal` as a concrete datatype.
- [03](03-context-enum-skos-scoped-context.md): gen-jsonld-context has no option to suppress the SKOS scoped context on enum slots.
- [04](04-context-any-range-coerced-to-id.md): gen-jsonld-context coerces `range: Any` (DatatypeProperty) slots to `@type: @id`.
- [05](05-context-inlined-class-coerced-to-id.md): gen-jsonld-context adds redundant `@type: @id` to inlined slots without an identifier.
- [06](06-owl-annotation-iri-values-as-literals.md): gen-owl emits IRI-valued annotations as string literals.
- [07](07-shacl-exactly-one-of-dropped.md): gen-shacl drops the `exactly_one_of` alternative ranges.

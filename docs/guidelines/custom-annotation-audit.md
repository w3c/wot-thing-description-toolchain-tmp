# Custom Annotation Audit

This audit treats a custom annotation as evidence that the base LinkML graph
does not yet express some required meaning. The preferred outcome is native
LinkML. When that is unavailable, a deterministic derivation is preferred over
an annotation. An annotation remains only when it expresses artifact policy or
a confirmed LinkML generator gap.

The inventory covers all annotations outside the `spec_*` family in the four
WoT schema modules.

## Native LinkML

No remaining annotation belongs in this category.

Native LinkML already provides the structural facts used by the generators:
`class_uri`, `slot_uri`, `is_a`, `mixins`, `range`, `inlined`,
`multivalued`, cardinality, `identifier`, and `slot_usage`. The context
generator also natively emits list and keyed-map containers when invoked with
`fix_multivalue_containers=True`.

## Derived From the Schema Graph

`jsonld_scoped_context` was removed in commit `6bc508d`.

Scoped vocabulary selection is now inferred from the range class, its
ancestors and mixins, class URI ownership, and the containing slot URI. The
algorithm and its expansion contract are documented in
[JSON-LD Context Composition](jsonld-context-composition.md).

There are no further annotations that can currently be removed by a proven
structural rule.

The literal JSON-LD keywords `@context` and `@type` are now handled as fixed
protocol terms rather than schema annotations. The security parameter uses the
native LinkML `alias: name`; its map-key identifier is identified from the
declared keyed map and kept out of public JSON Schema and root-context terms.

## Semantic Metadata

`dcterms:publisher` appears once in each schema module. It expresses the W3C
Working Group as a structured RDF organization in generated OWL. LinkML has
`contributors` but no native `publisher` metaslot, and a contributor is not a
publisher. Keep this annotation unless LinkML adds a publisher model capable
of representing the required organization name and URL.

`skos:note` appears on `jsonschema:allOf`, `wotsec:in`, and
`wotsec:oneOf`. These are vocabulary annotations, not generator controls.
They record distinctions between terms with the same JSON spelling or a
specification-status note. Keep them as RDF semantics.

## JSON-LD Generator Gaps

`jsonld_index` occurs on seven inlined keyed maps. It supplies the RDF
predicate represented by each JSON object key:

- `td:name` for affordance and URI-variable maps;
- `td:hasInstanceConfiguration` for security and Data Schema definition maps;
- `jsonschema:propertyName` for nested Object Schema properties.

This predicate cannot be inferred from `identifier`: the identifier describes
the key field of the value object, not the RDF predicate asserted for the map
key. `instantiates` is also not an alternative; it describes a metamodel
extension for a schema element, rather than an RDF mapping for serialized map
keys. Keep `jsonld_index` until LinkML supports an explicit keyed-map RDF
predicate in its JSON-LD context generator.

No `jsonld_keyword` annotations remain. The context composer handles the
fixed TD JSON-LD members `@context`, `@type`, and optional `id`; `id` maps to
`@id`. LinkML's native `identifier` would make the member required in generated
JSON Schema, which rejects valid TDs.

The internal LinkML names for `@context` and `@type` are `atContext` and
`atType`; their aliases preserve the JSON member names. RDF generators omit
all slots whose public alias is a JSON-LD keyword.

The relevant LinkML features are documented in the
[JSON-LD context generator](https://linkml.io/linkml/generators/jsonld-context.html)
and the [LinkML annotation model](https://linkml.io/linkml/schemas/annotations.html).

## JSON Schema Output Policy

`jsonschema_flatten_subclasses` on `DataSchema` produces the established TD
flat Data Schema definition. The class graph alone cannot decide that every
inheritance hierarchy should flatten: applying such a rule would also change
unrelated hierarchies, including security schemes. Keep it as an explicit
target-artifact choice.

`jsonschema_oneof_dispatch` on `SecurityScheme` creates a union of known
security-scheme subclasses plus the TD additional-security-scheme fallback.
Although LinkML has `designates_type`, it models a value that identifies a
LinkML class. TD `scheme` values such as `basic` and `apikey` are vocabulary
values, and the prefixed unknown-scheme fallback is a separate TD rule. Keep
this annotation. [LinkML type designators](https://linkml.io/linkml/schemas/type-designators.html)
do not generate this JSON Schema union.

`jsonschema_form_variants` on `Form` defines the TD operation sets for forms
at root, Property, Action, and Event locations. The current graph represents
these as one `Form` class, so the variant membership is not derivable from
inheritance or cardinality. Keep the annotation. A future model with explicit
Form subtypes and semantic operation-set relationships could replace it, but
that would be a deliberate model redesign affecting every generated artifact.

## Specification Rendering Policy

All `spec_*` annotations remain explicit. They encode ReSpec placement,
formatting, table visibility, assertion anchors, defaults, and allowed-value
presentation. These are editorial specification requirements, not facts about
the WoT information model.

## Decision Rule

Before introducing or retaining a non-`spec_*` annotation:

1. Check whether LinkML has a native metaslot and whether the target generator
   consumes it.
2. Check whether a deterministic rule over the resolved schema graph produces
   the required result for every current use.
3. Keep an annotation only when it expresses semantic metadata, a verified
   generator gap, or an intentional target-artifact policy.
4. Add a focused regression test before removing an annotation or replacing it
   with inference.

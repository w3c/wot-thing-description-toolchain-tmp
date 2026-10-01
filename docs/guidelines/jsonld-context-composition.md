# JSON-LD Context Composition

The generated JSON-LD context is a derived WoT artifact. The LinkML schema
modules remain the source of truth; this composition step must not contain a
list of TD paths, class names, or vocabulary-specific rules.

## Purpose

The context maps a TD JSON serialization to RDF without changing its JSON
surface. It must preserve:

- JSON-LD keywords such as `@context`, `@type`, and `id`;
- TD, HCTL, WoT Security, and Data Schema term URIs;
- keys of inlined maps as RDF statements; and
- the vocabulary used by members of nested objects.

The LinkML context generator supplies ordinary term mappings and JSON-LD
containers. The composition adapter adds only mappings that LinkML cannot yet
derive: JSON-LD keywords, keyed-map predicates, a public JSON key for an
internally escaped LinkML slot, and scoped vocabularies.

## Inputs

The algorithm reads only resolved LinkML model facts:

- `slot_uri` and `class_uri`;
- class inheritance and mixins;
- induced slots of each class;
- `range`, `inlined`, and `multivalued`; and
- the explicit `jsonld_index` annotations where LinkML has no native
  equivalent.

It uses `ContextGenerator(fix_multivalue_containers=True)` for native
`@set` and `@index` container generation.

## Scoped Vocabulary Algorithm

For each object-valued slot, resolve its range class, ancestors, and mixins.
For every class in that graph:

1. Read the prefix of the class's `class_uri`.
2. Keep the prefix only when at least one induced slot of that class has a
   `slot_uri` in the same vocabulary.
3. Remove the prefix of the containing slot's `slot_uri`.
4. If no prefix remains, emit no scoped context.
5. If exactly one prefix remains, use its declared namespace as the nested
   `@vocab` and populate it from slots in that namespace.
6. If more than one prefix remains, fail generation. The model is ambiguous
   and must be clarified before a context can be generated.

This is intentionally a structural inference rule. It recognizes
`PropertyAffordance` as a Data Schema through its `DataSchema` mixin, and it
does not scope `linkml:Any`, because that generic class owns no vocabulary
slots. No `jsonld_scoped_context` annotation is needed.

## Generated Context Contract

The generated context must provide the following behavior:

- A root `id` expands as JSON-LD `@id` and root `@type` expands as RDF type.
- TD affordance maps preserve their keys with `td:name`.
- `securityDefinitions` and `schemaDefinitions` preserve their keys with
  `td:hasInstanceConfiguration`.
- Nested Object Schema `properties` preserves keys with
  `jsonschema:propertyName`.
- Objects reached through `properties`, `schemaDefinitions`, `uriVariables`,
  Action/Event schema slots use the Data Schema vocabulary.
- Objects reached through `securityDefinitions` use the WoT Security
  vocabulary.
- Objects reached through `forms` and `links` use the HCTL vocabulary.
- `security` remains a string or array of strings. Its values are literals,
  not IRIs and not objects requiring a scoped context.

The TD Data Schema member `type` is deliberately outside this contract. It
must remain distinct from semantic JSON-LD `@type`; its RDF representation is
tracked in [Upstream Compatibility Findings](../upstream-compatibility-findings.md).

## Snippet Expectations

Specification snippets are authored as TD/TM JSONC and validate against the
generated JSON Schema when `validate: true`. Their rendering may hide
boilerplate, but hiding does not change the underlying JSON semantics.

Context regression examples must cover a complete TD serialization containing
at least a root `@type`, `id`, a security definition, `security`, a Property
Affordance, a Data Schema, and a Form. Expansion of such a serialization must
show the behavior in the generated-context contract above. In particular, a
snippet may use both:

```json
{
  "@type": "saref:OnOffState",
  "type": "string"
}
```

The first is semantic RDF typing. The second is the Data Schema JSON member;
tests must not treat them as interchangeable while its RDF mapping remains
under review.

Rendered snippet comparison tests check specification content. JSON-LD context
tests check RDF expansion separately, using compact representative TD inputs.
This keeps presentation differences from masking semantic regressions.

## Annotation Reduction Status

- `jsonld_scoped_context` was removed: vocabulary ownership is derived from the
  schema graph.
- `jsonld_index` remains: LinkML does not emit the required RDF predicate for
  a map key.
- `json_key` was removed: the public security member now uses native
  `alias: name`, while a structurally identified map key remains private.
- No `jsonld_keyword` annotations remain. The fixed TD JSON-LD members
  `@context`, `@type`, and `id` are handled by the context composer; `id`
  maps to `@id` without becoming a required LinkML identifier.
- LinkML names the JSON-LD keyword slots `atContext` and `atType`, with the
  public aliases `@context` and `@type`. JSON Schema and specification
  rendering use the aliases. RDF artifacts omit every slot whose public alias
  starts with `@`: JSON-LD keywords are serialization syntax, not TD
  vocabulary properties.
- `jsonschema_flatten_subclasses` remains: selecting a flattened Data Schema
  representation is JSON Schema output policy.
- `jsonschema_oneof_dispatch` remains: the discriminator and unknown-scheme
  fallback are TD JSON Schema policy.
- `jsonschema_form_variants` remains: operation-to-Form variant membership is
  specification policy, not derivable from class inheritance alone.

Revisit a retained annotation only after a native LinkML metaslot or a new
schema relationship can express the same meaning without reducing clarity.

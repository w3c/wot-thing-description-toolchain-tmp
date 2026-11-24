# JSON-LD context

The generated JSON-LD context is a derived WoT artifact. The LinkML schema
modules remain the source of truth; this composition step must not contain a
list of TD paths, class names, or vocabulary-specific rules.

How the generated context differs from the published TD 1.1 context is recorded only in
[JSON-LD context differences](../status/differences/jsonld-context.md).

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
- the explicit `jsonld_index` and `jsonld_container` annotations where LinkML
  has no native equivalent.

`WotContextGenerator` sets `fix_multivalue_containers=True` for native
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

This is a structural inference rule. It recognizes
`PropertyAffordance` as a Data Schema through its `DataSchema` mixin, and it
does not scope `linkml:Any`, because that generic class owns no vocabulary
slots.

## Bare `@id` Expansion

LinkML's `ContextGenerator` emits bare names (e.g., `"@id": "schemaDefinitions"`)
for slots and classes whose `slot_uri` or `class_uri` prefix matches the root
`@vocab`. These bare names resolve correctly at root level through `@vocab`
expansion, but break when re-declared inside scoped contexts where `@vocab`
points to a different namespace.

When a root term is re-declared inside a scoped context, its bare `@id` is
expanded with the root `@vocab` value. A term ID is considered bare when it
contains no colon, no slash, and does not start with `@`. The root context
keeps the bare names.

## Scoped Context Suppression

The scoped vocabulary algorithm (above) auto-infers a nested `@context` from
the range class's vocabulary ownership. This works correctly for most slots but
must be suppressed for definition containers like `schemaDefinitions`.

The upstream context `td-context-1.1.jsonld` assigns scoped contexts to these slots:

| Slot | Scoped vocabulary |
|------|-------------------|
| `properties`, `input`, `output`, `data`, `dataResponse`, `subscription`, `cancellation` | JSON Schema (`jsonschema`) |
| `security`, `securityDefinitions` | WoT Security (`wotsec`) |
| `forms`, `links` | Hypermedia Controls (`hctl`) |

`schemaDefinitions` is excluded despite having the same range
(`DataSchema`) as `properties`. Schema definitions are named, reusable data
schema containers — their content is opaque JSON that should not be
reinterpreted through a vocabulary-specific scoped context.

When a scoped context is injected into `schemaDefinitions`, terms like `href`
inside schema definitions expand to `hctl:hasTarget` — the JSON-LD processor
applies the vocabulary mapping even though the TD author intended `href` as a
plain JSON property name within a reusable schema.

To suppress auto-inference, annotate the slot with `jsonld_context: none` in
the LinkML schema. The `context_scope` function returns `None` for this value,
and no `@context` is emitted. See
[Custom Annotations — `jsonld_context`](../reference/annotations.md#jsonld_context)
for the annotation reference.

## Generated Context Contract

The generated context must provide the following behavior:

- A root `id` expands as JSON-LD `@id` and root `@type` expands as RDF type.
- TD affordance maps preserve their keys with `td:name`.
- `securityDefinitions` and `schemaDefinitions` are id maps
  (`@container: @id`): each key becomes the IRI of the defined node, resolved
  against the document base.
- Nested Object Schema `properties` preserves keys with
  `jsonschema:propertyName`.
- Objects reached through `properties`, `uriVariables`, Action/Event schema
  slots use the Data Schema vocabulary.
- `schemaDefinitions` has no scoped context — it is a definition container
  whose content stays opaque to JSON-LD vocabulary mapping.
- Objects reached through `securityDefinitions` use the WoT Security
  vocabulary.
- Objects reached through `forms` and `links` use the HCTL vocabulary.
- `security` remains a string or array of strings in JSON. Each value is
  coerced with `@type: @id` and resolves to the IRI of the scheme node that
  `securityDefinitions` defines under that name. The term has no scoped
  context. `schema` of an additional response refers to a `schemaDefinitions`
  entry in the same way.

The TD Data Schema member `type` is outside this contract. It
must remain distinct from semantic JSON-LD `@type`; its RDF representation is
tracked in [JSON-LD context differences](../status/differences/jsonld-context.md#data-schema-type-is-a-property-not-type).

## Type Coercion Rules

This section describes how the toolchain determines the `@type` coercion for
each term in the generated JSON-LD context.  Schema authors extending the TD
model must follow these rules so that new slots receive correct JSON-LD type
coercion without changes to the context passes registered in
`src/wot_toolchain/artifacts/jsonld_context/passes.py`.

### Background

In JSON-LD, a term's `@type` controls how values are interpreted:

| `@type` value  | Meaning                               | RDF result            |
|----------------|---------------------------------------|-----------------------|
| `@id`          | Value is an IRI reference             | IRI node (dereferenceable) |
| `@vocab`       | Value resolves against the active vocabulary | IRI from vocab base |
| `xsd:anyURI`   | Value is a URI-typed literal string   | `"http://..."^^xsd:anyURI` |
| *(omitted)*    | Value is a plain string               | `"value"^^xsd:string` |

The distinction between `@id` and `xsd:anyURI` is critical: `@id` produces an
RDF IRI node that JSON-LD processors can follow and dereference.  `xsd:anyURI`
produces a literal string that happens to contain a URI — processors treat it
as opaque text.

### Decision Rules

The context passes apply these rules.

#### Rule 1: Type Designator → `{"@id": "@type"}`

**Schema marker:** `designates_type: true` on the slot definition.

When a slot's value determines the RDF type of the enclosing node (i.e., the
value selects which class the instance belongs to), the JSON-LD context must
map it to `@type`.

No slot in the current schemas uses `designates_type`.

**LinkML limitation:** `WotJsonSchemaGenerator.before_generate_class_slot` in
`src/wot_toolchain/artifacts/jsonschema/generator.py` hands the upstream JSON
Schema generator a copy of the slot with the flag cleared.

#### Rule 2: A URI Value Is a Literal, a Name Reference Is a Node

A term whose JSON value is a URI string falls into one of two cases.  The case
is decided by what the value names, not by the JSON type.

**Case A — the URI names no node of the Thing Description.**  The value is an
`xsd:anyURI` literal.

**Schema marker:** `range: uri`, no `implements: [owl:ObjectProperty]`.

```yaml
slots:
  authorization:
    slot_uri: wotsec:authorization
    range: uri
```

This produces `"authorization": {"@type": "xsd:anyURI", "@id": "wotsec:authorization"}`
in the `wotsec` scoped context, an `owl:DatatypeProperty` with
`rdfs:range xsd:anyURI` in the ontology, and a property shape with
`sh:datatype xsd:anyURI` and `sh:nodeKind sh:Literal` in SHACL.  The slots
modelled this way are `href`, `base`, `support`, `profile`, `anchor`, `proxy`,
`authorization`, `token` and `refresh`.  `tests/test_uri_valued_terms.py` pins
the last five across the four artifacts.

**Case B — the value is the name of a node the Thing Description defines.**
The value is an IRI node, and the property is an object property that ranges
over the class of the defined node.

**Schema marker:** `range: <Class>` without `inlined`, where the class has a
key slot, and `jsonld_container: "@id"` on the definitions map that holds the
nodes.

```yaml
slots:
  security:
    slot_uri: td:hasSecurityConfiguration
    range: SecurityScheme
```

This produces `"security": {"@type": "@id", "@id": "hasSecurityConfiguration"}`.
Because `securityDefinitions` carries `@container: @id`, each map key becomes
the IRI of the scheme node, resolved against the document base, and a
`security` name resolves to the same IRI.  The slots modelled this way are
`security` (range `SecurityScheme`, defined by `securityDefinitions`) and
`schema` of `AdditionalExpectedResponse` (range `DataSchema`, defined by
`schemaDefinitions`).  `tests/test_definition_references.py` pins both across
the four artifacts.  JSON Schema keeps the values as strings in both cases.

**Not in use:** the context pass `fix_object_property_id_coercion` replaces `xsd:anyURI` with `@id` for a
`range: uri` slot that carries `implements: [owl:ObjectProperty]`.  No slot in
the schema uses this combination.  It yields an object property without a
range, which is the modelling this rule replaces.  The only URI-typed slot
with `implements: [owl:ObjectProperty]` is `unit` (`range: uriorcurie`), which
is coerced with `@vocab`.

#### Rule 3: OWL DatatypeProperty → Strip `@id`

**Schema marker:** `implements: [owl:DatatypeProperty]` on the slot definition.

LinkML sometimes adds `@type: @id` to slots that should produce literals.  When
a slot is explicitly declared as an `owl:DatatypeProperty`, the context pass
`strip_datatype_property_id_coercion` strips `@type: @id`, leaving the value as a plain literal.

#### Rule 4: `@vocab` Type Coercion

**Schema marker:** an enum range whose values have `meaning:` declarations, on
a slot without `designates_type`.

When a slot's range is an enum whose permissible values carry `meaning`
declarations (mapping string names to vocabulary IRIs), the context pass
`fix_enum_vocab_type_coercion` sets `@type: @vocab` on that slot's context entry. This activates the enum
value aliases added by `add_enum_value_aliases`, so bare string values
like `"readproperty"` expand to their vocabulary IRIs (e.g.
`td:readProperty`) during JSON-LD processing.

**Derivation rule:**

1. Resolve the slot's `range` to an enum definition.
2. Check whether any permissible value in that enum has a `meaning` CURIE.
3. If yes, and the slot is not `designates_type`, set `@type: @vocab`.

Slots with `designates_type` are excluded because they map to JSON-LD
`@type`, which already receives IRI expansion through a different mechanism.

**Two halves of one mechanism:**

- `add_enum_value_aliases` adds each permissible value's text as a context
  alias pointing to its `meaning` IRI. This makes the vocabulary terms
  available to the JSON-LD processor.
- `@type: @vocab` tells the processor to resolve bare string values through
  these aliases. Without it, enum values remain plain string literals and
  never expand to IRIs.

**Current slots affected:** `op` (range `OperationType`, 18 values with
meanings mapping operation names to `td:` IRIs), `scheme` (range
`SecuritySchemeList`) and `type` (range `DataSchemaType`). No slot in the
current schemas uses `designates_type`.

This rule is structural: it derives from `range`, `meaning`, and
`designates_type` — no custom annotations are required.

#### Rule 5: Default — LinkML Native Behavior

Slots that do not match any of the above rules keep whatever type coercion
LinkML's context generator produces:

- `range: uri` → `xsd:anyURI`
- `range: string` → no `@type` (plain string)
- Object-valued slots → no `@type` needed (value is a nested node)

### How to Extend the Schema

When adding a new URI-valued slot, ask:

1. **What does the URI value name?**
   - A node the Thing Description itself defines under a name (as `security`
     names an entry of `securityDefinitions`) → use `range: <Class>` without
     `inlined`, and `jsonld_container: "@id"` on the definitions map.  The
     context emits `@type: @id`.
   - Anything else (endpoint, URI template, contact URI, opaque identifier) →
     use `range: uri` without `implements: [owl:ObjectProperty]`.  The default `xsd:anyURI` is
     correct.

2. **Does the value determine the RDF type of the enclosing node?**
   - Yes → add `designates_type: true`.  The context passes emit
     `{"@id": "@type"}`.

3. **Is the value a vocabulary term from an enum?**
   - Yes, and the enum values have `meaning:` → the context passes handle
     `@vocab` coercion automatically from the enum's `meaning` declarations.

### Relationship to OWL

These rules are grounded in OWL semantics.  JSON-LD is also RDF, so OWL
property classifications are the correct discriminator:

- **`owl:ObjectProperty`** → the value is a node.  JSON-LD should use `@id`
  to produce an IRI node, and the property ranges over a class.
- **`owl:DatatypeProperty`** → the value is a literal.  JSON-LD should use
  a datatype IRI (e.g., `xsd:anyURI`) or no `@type` for plain strings.
- **`owl:AnnotationProperty`** → treated as a literal for JSON-LD purposes.

This alignment means the same `implements:` declaration serves both the OWL
ontology generator and the JSON-LD context passes — a single source of
truth in the schema.
## OWL-Only Slot Exclusion

Some slots exist in the LinkML schema solely for OWL ontology emission (e.g.
`hasInteractionAffordance`). They are never instantiated in TD JSON instances
and must not appear in the JSON-LD context.

The context pass `remove_uninduced_slots` identifies these slots structurally: a slot is excluded when
it is never induced by any class (via `SchemaView.class_induced_slots`) AND its
key is not referenced as a `@index` term by any slot's `jsonld_index`
annotation. This inference-based approach requires no extra annotations or
hardcoded lists.

For example, `propertyName` is never class-induced but is declared in the
scoped Data Schema contexts because it serves as the `@index` term for the
`properties` map of an Object Schema. `hasInteractionAffordance` and
`hasInstanceConfiguration` are neither class-induced nor an `@index` term, so
they are excluded.

## Title and Description Language

`title` and `description` have no `@language` and no `@type` in the generated
context, so a value takes the document's default `@language` when one is set
and is a plain string otherwise. The other artifacts are modelled to accept
both literal kinds this produces: the generated OWL gives `td:title` and
`td:description` `rdfs:range rdfs:Literal`, the SHACL shapes give them
`sh:nodeKind sh:Literal` without `sh:datatype`, and JSON Schema keeps
`"type": "string"`. `titles` and `descriptions` keep `@container: @language`
for explicit language maps.

How this differs from the published context, ontology and shapes is recorded in
[JSON-LD context differences](../status/differences/jsonld-context.md#forced-english-language),
[OWL differences](../status/differences/owl.md) and [SHACL differences](../status/differences/shacl.md#title-and-description-datatype).

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

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

This is intentionally a structural inference rule. It recognizes
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

`schemaDefinitions` is deliberately excluded despite having the same range
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
[Custom Annotations — `jsonld_context`](../reference/wot-custom-annotations.md#jsonld_context)
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

The TD Data Schema member `type` is deliberately outside this contract. It
must remain distinct from semantic JSON-LD `@type`; its RDF representation is
tracked in [JSON-LD context differences](../differences/jsonld-context.md#data-schema-type-is-a-property-not-type).

## Implicit `xsd:string` Type Coercion

The W3C upstream context annotates some string-valued terms with explicit
`"@type": "xsd:string"`. The generated context omits this annotation because
JSON-LD defines `xsd:string` as the default datatype for plain string values.

Verified behavior:

- **Expanded JSON-LD** differs structurally: without the annotation, expansion
  produces `{"@value": "basic_sc"}`; with it,
  `{"@type": "xsd:string", "@value": "basic_sc"}`. These are semantically
  equivalent per the JSON-LD specification.
- **RDF output** is identical: both produce the same N-Quads with a plain
  string literal (`"basic_sc"`). No datatype IRI appears in either case.
- **Roundtrip** is lossless: expand then compact recovers the original
  document regardless of the annotation.

The upstream annotation is a defensive belt-and-suspenders measure that makes
the string coercion explicit in expanded form. Omitting it does not change
RDF semantics or TD instance processing. This is not a bug in the generated
context.

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

## Enum Vocabulary Type Coercion

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

## Annotation Reduction Status

- `jsonld_index` remains: LinkML does not emit the required RDF predicate for
  a map key.
- `jsonld_container` remains: LinkML emits neither language maps nor id maps.
- The public security member uses native `alias: name`, while a structurally
  identified map key remains private.
- The fixed TD JSON-LD members
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
- `jsonschema_enum_subset_partition` and `jsonschema_form_subset` remain:
  operation-to-Form variant membership is specification policy, not derivable
  from class inheritance alone.

Revisit a retained annotation only after a native LinkML metaslot or a new
schema relationship can express the same meaning without reducing clarity.

## Upstream JSON-LD Issues Identified

### `@language: en` on `title`/`description` breaks multilanguage roundtrips

**Upstream context entries (td-context-1.1.jsonld):**

```json
"title":       { "@id": "td:title",       "@language": "en" },
"description": { "@id": "td:description", "@language": "en" }
```

The term-level `@language: en` forces every value of `title` and `description`
to produce an English-tagged RDF literal (`"value"@en`), regardless of the
document-level `@language` set by the TD instance. This is correct for the
common case — the W3C spec defines `title` and `description` as the default
English text, while `titles` and `descriptions` carry language maps — but it
causes a roundtrip failure when a TD instance sets a non-English document
language and places non-English text in `title`.

**Affected test instance:** `tests/data/11-multilanguage/string-direction-td-valid.jsonld`

```json
{
  "@context": [
    "https://www.w3.org/2022/wot/td/v1.1",
    { "@language": "ar-EG", "@direction": "rtl" }
  ],
  "title": "شيء يخصني يقيس درجة الحرارة",
  "description": "TD for a sensor that measures the temperature",
  ...
}
```

The instance sets `@language: ar-EG` at the document level and places Arabic
text in `title`. Since the upstream context defines `title` with
`@language: en`, the term-level setting wins during expansion.

**Expanded form (relevant fields):**

```json
"https://www.w3.org/2019/wot/td#title": [{
  "@value": "شيء يخصني يقيس درجة الحرارة",
  "@language": "en",
  "@direction": "rtl"
}],
"https://www.w3.org/2019/wot/td#description": [{
  "@value": "TD for a sensor that measures the temperature",
  "@language": "en",
  "@direction": "rtl"
}]
```

Arabic text is tagged as `@language: en`. This is semantically incorrect.

**Compacted form divergence:**

After expand→compact, the compactor cannot use the short-form key `title`
because its term-level `@language: en` does not match the document-level
`@language: ar-EG`. The processor falls back to the prefixed form:

| Field         | Original key    | After roundtrip   |
|---------------|-----------------|-------------------|
| `title`       | `title`         | `td:title`        |
| `description` | `description`   | `td:description`  |

The original `title` and `description` keys disappear from the compacted
output. Downstream consumers expecting the short-form keys will break.

**Root cause:** JSON-LD term-level `@language` overrides document-level
`@language` unconditionally (JSON-LD 1.1 §9.8). The upstream context assumes
`title` and `description` always carry English text, but the TD spec allows
instances to override the document language and use non-English text in these
fields.

**Impact:** This is an upstream spec issue. The test instance
`string-direction-td-valid.jsonld` is provided as a valid TD by the W3C test
suite, so the standard allows non-English text in `title`.

**Resolution:** The generated context omits `@language` from `title` and
`description` term definitions entirely. This is an intentional deviation from
upstream. Without term-level `@language`, these fields inherit the
document-level `@language` (if set), which correctly tags the value in the
language the TD instance declares. For TDs with no document-level `@language`,
the value becomes a plain string literal — which is the conservative default
since the language is genuinely unknown.

The `titles` and `descriptions` fields continue to use `@container: @language`
(language maps with BCP47 keys), which is the correct mechanism for explicit
multilanguage tagging. No `in_language` annotation is needed on those fields.

**RDF datatype implications:** The RDF literal type of `title` and
`description` values is determined by the TD instance, not the schema. When
a TD sets document-level `@language` (e.g. `"@language": "ar-EG"` in
`@context`), the value becomes an `rdf:langString` literal tagged with that
language. When no `@language` is in scope, the value is a plain `xsd:string`
literal. This is correct behavior — the instance author controls whether their
title is language-tagged. JSON Schema validates
the JSON surface form (always a plain string), while JSON-LD processing
determines the RDF datatype at expansion time based on the active `@language`.
These are independent concerns at different layers.

This deviation is tracked in `tests/test_jsonld_context_upstream_comparison.py`
under `INTENTIONAL_DEVIATION` xfail markers on `test_title_has_language_tag`
and `test_description_has_language_tag`.

### `rdfs:range xsd:string` contradicts `rdf:langString` literals from `@language`

The upstream ontology declares `td:title` and `td:description` with range
`xsd:string`, but the upstream JSON-LD context forces language-tagged
literals via `@language: en`. In RDF 1.1, `xsd:string` and `rdf:langString`
are **disjoint datatypes** — a literal is one or the other, never both.
Every TD instance processed with the upstream context produces triples that
violate the ontology's own range declarations.

**The contradiction across upstream files:**

| File | Predicate | Range value |
|------|-----------|-------------|
| `td.ttl` (hand-authored) | `schema:rangeIncludes` | `schema:Text` |
| `target/td.ttl` | `schema:rangeIncludes` | `xsd:string` |
| `gen-owl-td.ttl` | `rdfs:range` | `xsd:string` |
| `td-context-1.1.jsonld` | `@language: en` | produces `rdf:langString` |

The ontology says "values must be `xsd:string`". The context produces
`rdf:langString`. These types cannot overlap.

**Upstream SHACL shapes are also inconsistent.** In `td-validation.ttl`:

- `ThingShape` declares `td:title` inline with
  `sh:or ( [ sh:datatype xsd:string ] [ sh:datatype rdf:langString ] )` —
  accepts both.
- The reusable blank node `_:title` (used by other shapes) declares only
  `sh:datatype rdf:langString` — rejects plain strings.
- The reusable `_:description` declares only `sh:datatype rdf:langString`.

The same property has different datatype constraints depending on which
shape validates it.

**RDF 1.1 type rules
([RDF Concepts §3.3](https://www.w3.org/TR/rdf11-concepts/#section-Graph-Literal)):**

A literal in RDF 1.1 has exactly one datatype IRI. A language tag is
present *if and only if* the datatype IRI is `rdf:langString`. Without a
language tag, the datatype is `xsd:string`. The value spaces are
structurally different: `xsd:string` values are plain Unicode strings;
`rdf:langString` values are (string, language-tag) pairs with no overlap
([RDF Semantics](https://www.w3.org/TR/rdf11-mt/)).

Under RDFS entailment (rule rdfs3), if `p rdfs:range C` and `x p y`, then
`y rdf:type C`. A language-tagged literal cannot satisfy `rdfs:range
xsd:string`.

**Inheritance from Dublin Core:**

`td:title rdfs:subPropertyOf dcterms:title`. Dublin Core declares
`dcterms:title rdfs:range rdfs:Literal`
([DCMI Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/)).
`rdfs:Literal` is the superclass of all literal datatypes — it covers both
`xsd:string` and `rdf:langString`
([RDF Schema §2.3](https://www.w3.org/TR/rdf-schema/#ch_literal)). The
upstream TD ontology narrows this to `xsd:string`, which is more
restrictive than the parent property and excludes language-tagged values
that the context itself produces.

`td:description rdfs:subPropertyOf dcterms:description`. Dublin Core
declares no range constraint on `dcterms:description`, making the upstream
`xsd:string` restriction an independent addition that conflicts with the
context.

**How other W3C ontologies handle string-or-langString properties:**

| Ontology | Property | Range declaration | Accepts both? | Reference |
|----------|----------|-------------------|---------------|-----------|
| Dublin Core | `dcterms:title` | `rdfs:Literal` | Yes | [DCMI Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/) |
| SKOS | `skos:prefLabel` | "RDF plain literals" | Yes | [SKOS §S12](https://www.w3.org/TR/skos-reference/#labels) |
| FOAF | `foaf:name` | `rdfs:Literal` | Yes | [FOAF Spec](http://xmlns.com/foaf/spec/) |
| Schema.org | `schema:name` | `schema:Text` | Sidesteps issue | [schema.org](https://schema.org/) |
| WoT TD | `td:title` | `xsd:string` | **No** | Upstream bug |

**Fix alternatives and their layer compatibility:**

| Approach | OWL ontology | SHACL shapes | JSON-LD context | RDFS reasoning |
|----------|-------------|--------------|-----------------|----------------|
| `rdfs:range rdfs:Literal` | Valid, broad (accepts integers too) | Use `sh:nodeKind sh:Literal` | No change needed | Works |
| `rdfs:range rdf:PlainLiteral` | Precise, OWL 2 native ([OWL 2 §5.7](https://www.w3.org/TR/owl2-syntax/#Literals)) | Not expressible directly | Processors don't know OWL | Requires OWL 2 reasoner |
| `sh:or xsd:string rdf:langString` | Not an OWL range construct | Precise, matches ThingShape inline | No change needed | N/A (SHACL layer) |
| No `rdfs:range` | Permissive | Constrain in SHACL only | No change needed | No violation possible |

No single declaration works optimally at every layer. The practical
solution requires coordinated declarations:

1. **OWL ontology:** `rdfs:range rdfs:Literal`. Matches Dublin Core parent
   (`dcterms:title`), works with RDFS and OWL 2 reasoners, accepts both
   `xsd:string` and `rdf:langString`. Broader than ideal (admits integers)
   but consistent with established W3C precedent. `rdf:PlainLiteral` is
   more precise but only understood by OWL 2 reasoners — RDFS reasoners
   would still flag `rdf:langString` values against it.
2. **SHACL shapes:** `sh:or ( [ sh:datatype xsd:string ] [ sh:datatype
   rdf:langString ] )`. Precise validation that accepts exactly the two
   concrete literal types JSON-LD processors produce. This is what the
   upstream `ThingShape` already does for `td:title` inline — it should be
   applied consistently to all reusable shapes.
3. **JSON-LD context:** No `@type` coercion on `title`/`description`. The
   instance controls the RDF datatype via document-level `@language` (see
   previous section).
4. **JSON Schema:** `"type": "string"` (unchanged). JSON Schema validates
   the JSON surface form, not the RDF layer. A JSON string is a JSON
   string regardless of whether JSON-LD later tags it with a language.

This is an upstream issue requiring coordinated fixes across the ontology,
SHACL shapes, and context. Our generated artifacts follow the approach
above: the generated OWL declares `rdfs:range rdfs:Literal` on `td:title`;
the SHACL shapes use `sh:nodeKind sh:Literal` without `sh:datatype` (accepts
both types); the JSON-LD context omits `@language` (see previous section).

## Accepted IRI Differences

Some generated context entries intentionally use different IRIs than the
upstream W3C contexts. These are deliberate modeling choices, not bugs.

### `unit` — `qudt:unit` vs `schema:unitCode`

| Source | IRI |
|--------|-----|
| Generated context | `qudt:unit` (`http://qudt.org/schema/qudt/unit`) |
| Upstream `json-schema-context.jsonld` | `schema:unitCode` |

The upstream context maps `unit` to `schema:unitCode`, which is a string
code (e.g. `"CEL"`) from the UN/CEFACT recommendation. The LinkML schema
maps `unit` to `qudt:unit`, which points to a QUDT unit individual IRI
(e.g. `unit:DEG_C`). QUDT provides richer unit semantics — dimensional
analysis, conversion factors, and unit ontology membership — which aligns
with the machine-readable design goals of the Thing Description.

`test_unit_present` in `tests/test_jsonld_context_upstream_comparison.py`
asserts the generated mapping.
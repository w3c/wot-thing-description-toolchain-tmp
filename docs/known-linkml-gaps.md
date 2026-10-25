# Known LinkML Generator Gaps

Before writing a new postprocessor, run `/check-linkml <feature>` — a gap here may be fixed in a newer LinkML version.

Each entry: **what the gap is**, **which artifact(s) affected**, **current workaround**, **LinkML issue if known**.

---

## Accepted Differences from Upstream W3C Contexts

These are intentional deviations from upstream W3C TD/hctl/jsonschema/wotsec
contexts. They are correct LinkML default behavior, not bugs. **Do not "fix"
these — they should not be filed as issues.**

### A1. Explicit XSD primitive type coercion

**Upstream:** Omits `@type` for slots with XSD primitive ranges (`xsd:boolean`,
`xsd:string`, `xsd:integer`, `xsd:double`, `xsd:decimal`, `xsd:dateTime`,
`xsd:nonNegativeInteger`, `xsd:unsignedShort`, etc.) because JSON-LD processors
infer datatype from native JSON types (boolean, string, number).

**Generated:** LinkML emits explicit `@type: xsd:boolean`, `@type: xsd:integer`,
etc. for all typed slots.

**Why accepted:** This is LinkML's default JSON-LD context serialization. The
explicit coercion is redundant but semantically correct — it does not change
JSON-LD expansion or compaction behavior. Stripping all XSD primitives would
mean fighting the generator's native output for no functional benefit.

**Affected terms:** `success` (`xsd:boolean`), `idempotent` (`xsd:boolean`),
`observable` (`xsd:boolean`), `safe` (`xsd:boolean`), `synchronous`
(`xsd:boolean`), `readOnly` (`xsd:boolean`), `writeOnly` (`xsd:boolean`),
and all `xsd:integer`/`xsd:string`/`xsd:double`-ranged terms.

---

## JSON-LD Context Generator

### 1. No `@container: "@language"` support in JSON-LD context generator
**Symptom:** The context generator only emits `@container: "@index"` (inlined
dicts) or `@container: "@set"` (lists) via `fix_multivalue_containers`. It has
no mechanism to emit `@container: "@language"` for language maps.
**Artifact:** `context.jsonld`
**Checked:** v1.12.0 — `jsonldcontextgen.py` lines 423–427 only handle
`@index` and `@set`. The `in_language` metaslot (PR #3449, merged June 2026)
is for OWL/SHACL literal language tags, not JSON-LD container declarations.
**Workaround:** Schema annotation `jsonld_container: "@language"` on `titles`
and `descriptions` slots. The postprocessor reads this annotation and emits
`@container: "@language"` instead of the default `@container: "@index"`.
Tested with jsonld.js expand→compact roundtrip (64/64 instances pass).
**LinkML issue:** none filed — report as "support `@container: '@language'`
in JSON-LD context generator for language-keyed maps".

### 2. Multivalue containers are now natively supported
**Status:** Resolved in LinkML 1.11.0.post278.dev0+26ebff6d.
**Finding:** `ContextGenerator(fix_multivalue_containers=True)` emits
`@container: "@set"` for multivalued lists and `@container: "@index"` for
inlined dictionary-valued slots.
**Artifact:** `context.jsonld`
**Required action:** Keep the generator option enabled and maintain regression
tests for list and map serialization.
**LinkML reference:** [JSON-LD context generator options](https://linkml.io/linkml/cli/generate.html)

### 3. JSON-LD index predicates are not generated for keyed maps
**Symptom:** LinkML emits `@container: "@index"` for inlined keyed maps but
cannot emit the `@index` predicate that tells the JSON-LD processor which RDF
property carries the map key.
**Artifact:** `context.jsonld`
**WoT requirement:** TD JSON-LD expansion and compaction must preserve names
from `securityDefinitions`, `schemaDefinitions`, affordance maps, and nested
Data Schema `properties` maps as RDF statements.
**Current limitation:** The LinkML `instantiates` metaslot does not inform the
JSON-LD context generator's `@index` value.
**Workaround:** Postprocessor reads `jsonld_index_key` annotation from the
schema and emits `@index` with bare term names (e.g. `"name"`,
`"hasInstanceConfiguration"`), matching upstream W3C context convention. The
`@index` value is a JSON-LD term name resolved via the active context's
`@vocab` — not a prefixed CURIE. Verified with jsonld.js expand→compact
roundtrip (64/64 instances pass).
**LinkML issue:** unknown — report as "support an `@index` predicate for
inlined keyed maps, sourced from LinkML schema metadata".

### 3a. Scoped context mappings cannot express class-specific JSON terms
**Symptom:** LinkML supports a slot `alias`, and the JSON Schema and JSON-LD
context generators use it as an emitted JSON key. However, the context
generator only generates class-scoped context entries for range overrides. It
cannot scope a different alias or RDF predicate to a class.
An alias also cannot represent the WoT security member `name`: it collides
with the identifier slot that represents a security-definition map key.
**Artifact:** `context.jsonld`
**WoT requirement:** The JSON key `name` has different RDF mappings by
location: `td:name` for affordance-map keys, `wotsec:name` inside security
schemes, and `jsonschema:propertyName` for nested object-schema keys.
**Workaround:** Derive module contexts from the range class ancestry, using a
class URI prefix only when the class owns induced slots in that vocabulary.
Exclude the containing slot's vocabulary; require exactly one remaining
prefix. Use an explicit `jsonld_context` annotation only when a slot value is
an object and its range is insufficient to identify its vocabulary. No current
TD slot needs this override. The composition step is modeled on the upstream
context merger.
**LinkML issue:** unknown — report as "support class-scoped JSON-LD term
definitions for aliases and slot URIs, not only range coercion overrides".
See [JSON-LD Context Composition](guidelines/jsonld-context-composition.md)
for the complete inference algorithm and generated-context contract.

### 3b. `uriorcurie` range emits `xsd:anyURI` instead of `@vocab`
**Symptom:** Slots with `range: uriorcurie` get `@type: xsd:anyURI` in the
generated JSON-LD context. The upstream W3C context uses `@type: @vocab` so
that bare terms resolve against the active `@vocab` base.
**Artifact:** `context.jsonld`
**Example:** `unit` slot — upstream: `{"@id": "schema:unitCode", "@type": "@vocab"}`,
LinkML emits: `{"@id": "schema:unitCode", "@type": "xsd:anyURI"}`.
**Workaround:** Postprocessor `_fix_vocab_type_coercion()` replaces
`xsd:anyURI` → `@vocab` for all `uriorcurie`-ranged slots.
**LinkML issue:** none filed — report as "support `@type: @vocab` in JSON-LD
context for `uriorcurie` or `uri` ranged slots".

### 3d. URI `owl:ObjectProperty` slots emit `xsd:anyURI` instead of `@id`
**Symptom:** Slots with `range: uri` always get `@type: xsd:anyURI` in the
generated JSON-LD context, even when the slot represents a dereferenceable RDF
resource (an `owl:ObjectProperty`).  The upstream W3C context uses `@type: @id`
for these slots so that values produce IRI nodes, not literal strings.
**Artifact:** `context.jsonld`
**Example:** `authorization` slot — upstream: `{"@id": "wotsec:authorization", "@type": "@id"}`,
LinkML emits: `{"@id": "wotsec:authorization", "@type": "xsd:anyURI"}`.
**Workaround:** Postprocessor `_fix_object_property_id_coercion()` replaces
`xsd:anyURI` → `@id` for all slots that declare `implements: [owl:ObjectProperty]`
and have `range: uri`.  The `implements` metaslot is native LinkML — no custom
annotations needed.
**LinkML issue:** none filed — report as "support `@type: @id` in JSON-LD
context for `uri`-ranged slots annotated as `owl:ObjectProperty`".
See [JSON-LD Type Coercion Rules](guidelines/jsonld-type-coercion-rules.md)
for the full decision tree.

### 3e. `designates_type` slots not mapped to `@type` in JSON-LD context
**Symptom:** Slots with `designates_type: true` are not emitted as
`{"@id": "@type"}` in the generated JSON-LD context.  The upstream W3C context
maps `scheme` to `{"@id": "@type"}` so that the slot value determines the RDF
type of the enclosing node.
**Artifact:** `context.jsonld`
**Example:** `scheme` slot — upstream: `{"@id": "@type"}`,
LinkML emits: no entry (slot absent from generated context).
**Additional bug:** Setting `designates_type: true` on a slot whose range is
an enum causes the JSON Schema generator to crash (`ValueError: No such type`)
because `JsonSchemaGenerator.type_ancestors()` treats the range as a type name,
not an enum name.
**Workaround:** Postprocessor `_fix_type_designator_mapping()` injects
`{"@id": "@type"}` for all `designates_type` slots.  Pipeline guard in
`_gen_jsonschema()` temporarily clears `designates_type` before JSON Schema
generation and restores it after.
**LinkML issue:** none filed — report as "emit `{\"@id\": \"@type\"}` in
JSON-LD context for slots with `designates_type: true`" and separately "JSON
Schema generator crashes on `designates_type` when slot range is an enum".
See [JSON-LD Type Coercion Rules](guidelines/jsonld-type-coercion-rules.md)
for the full decision tree.

### 3f. Class-ranged slots always get `@type: @id` in JSON-LD context
**Symptom:** Slots whose range is a class always get `@type: @id` in the
generated JSON-LD context, even when the slot values are always inline objects
(never IRI references). `@type: @id` tells the JSON-LD processor to treat the
value as an IRI string, which is wrong for embedded objects.
**Artifact:** `context.jsonld`
**Example:** `response` slot (range: `ExpectedResponse`) — upstream:
`{"@id": "hctl:returns"}` (no `@type`), LinkML emits:
`{"@id": "hctl:returns", "@type": "@id"}`. Same for `additionalResponses`
(range: `AdditionalExpectedResponse`).
**Root cause:** `ContextGenerator.visit_slot()` adds `@type: @id` for every
class-ranged slot regardless of whether the value is an IRI reference or an
inline object. LinkML's `inlined` metaslot has no effect on context generation.
**Workaround:** Postprocessor strips `@type: @id` from slots where
`schema_view.is_inlined(slot)` returns `True` and the range class has no
`identifier` slot (i.e. values are always inline, never referenceable by IRI).
Uses `schema_view.is_inlined()` rather than checking `slot.inlined` directly,
because `inlined_as_list: true` sets `is_inlined()` to `True` but leaves
`slot.inlined` as `None`.
**LinkML issue:** none filed — report as "JSON-LD context generator should not
emit `@type: @id` for class-ranged slots when the range class has no identifier
slot (inlined-only values)".

### 3g. String-ranged `owl:ObjectProperty` slots need `@type: @id` coercion
**Symptom:** Slots with `range: string` and `implements: [owl:ObjectProperty]`
get no `@type` coercion in the generated JSON-LD context. The upstream W3C
context uses `@type: @id` for these slots so that plain string values (e.g.
schema definition names) are resolved to IRIs by the JSON-LD processor.
**Artifact:** `context.jsonld`
**Example:** `schema` slot (hctl:hasAdditionalOutputSchema) — upstream:
`{"@id": "hctl:hasAdditionalOutputSchema", "@type": "@id"}`, LinkML emits:
`{"@id": "hctl:hasAdditionalOutputSchema"}` (no `@type`).
**Distinction from gap 3d:** Gap 3d covers `range: uri` slots where LinkML
emits `xsd:anyURI` (wrong type, needs replacement). This gap covers
`range: string` slots where LinkML emits no type at all (missing, needs addition).
**Caveat:** Not all string-ranged ObjectProperties need `@type: @id`. When the
domain class has a `designates_type` slot, its scoped context provides `@vocab`
resolution, making `@type: @id` unnecessary. Example: `wotsec:allOf` and
`wotsec:oneOf` on `ComboSecurityScheme` (which has `designates_type: scheme`) —
values resolve via `@vocab: wotsec:` in the security scoped context.
**Workaround:** Postprocessor `_fix_object_property_id_coercion()` adds
`@type: @id` for string-ranged ObjectProperty slots whose domain class has no
`designates_type` slot. Same logic in `build_module_context` for per-module
contexts.
**LinkML issue:** none filed — report as "support `@type: @id` in JSON-LD
context for string-ranged slots annotated as `owl:ObjectProperty`".

### 3c. Enum value `meaning` not emitted as JSON-LD context term aliases
**Symptom:** Enum permissible values with a `meaning` CURIE are not emitted as
JSON-LD context term definitions. The upstream W3C context maps lowercase enum
values to class IRIs so that e.g. `"type": "object"` expands to
`jsonschema:ObjectSchema` and `"scheme": "nosec"` expands to
`wotsec:NoSecurityScheme`.
**Artifact:** `context.jsonld`
**Example:** `DataSchemaType.object` has `meaning: jsonschema:ObjectSchema` but
the generated context contains no `"object": "jsonschema:ObjectSchema"` entry.
Similarly for all 9 `SecuritySchemeList` values.
**Workaround:** Postprocessor `_add_enum_value_aliases()` iterates all enums
and adds `"value": "meaning:CURIE"` entries for permissible values that declare
a `meaning`.
**LinkML issue:** none filed — report as "emit JSON-LD context term aliases for
enum permissible values that declare a `meaning` CURIE".

### 4. Context coercion for default ranges requires review
**Symptom:** Slots whose range equals the schema `default_range` may not get a
JSON-LD `@type` coercion in the generated context.
**Artifact:** `context.jsonld`
**Status:** Open. No coercion is added outside LinkML output until the required
TD JSON-LD representation is confirmed with round-trip tests.
**LinkML issue:** unknown — report as "emit JSON-LD coercion for slots using a
schema default range".

### 5. JSON-LD coercion for `exactly_one_of` ranges requires review
**Symptom:** Slots with `exactly_one_of` ranges require a TD-specific decision
about whether a JSON-LD coercion is valid.
**Artifact:** `context.jsonld`
**Status:** Open. No synthetic coercion is added because mixed ranges cannot be
represented by one JSON-LD `@type` value.
**LinkML issue:** unknown — report as "support conditional JSON-LD context
coercion for LinkML unions where it is semantically valid".

---

## OWL Generator

### 10. `gen-owl` uses slot name (not `slot_uri`) as OWL property IRI

**Symptom:** `gen-owl` emits `td:forms`, `td:actions`, `td:input` etc. — the
slot name in the default namespace — instead of the correct OWL IRIs
`td:hasForm`, `td:hasActionAffordance`, `td:hasInputSchema` declared in the
WoT TD ontology.

**Root cause:** LinkML's built-in OWL generator derives each property IRI by
combining the schema default namespace with the slot name (or `alias`). The
`slot_uri` metaslot is a semantic mapping annotation ("this slot represents
this external concept") but `gen-owl` does not use it as the emitted IRI.

**Design rationale — 3-way split is intentional:**
- Slot name → JSON key (e.g. `forms` in JSON Schema, `forms` in JSON)
- `slot_uri` → OWL property IRI (e.g. `td:hasForm` in the OWL ontology)
- JSON-LD context bridges them: `"forms": {"@id": "td:hasForm"}`

The upstream `index.html` (spec table) and the published JSON-LD context both
follow this same pattern — JSON terms (`forms`, `actions`) map to OWL IRIs
(`td:hasForm`, `td:hasActionAffordance`) only via context, not by name equality.
Changing slot names to match OWL local names would break JSON output.

**Conclusion:** `gen-owl` cannot replace the custom `owl.py` generator for WoT
TD. The custom generator reads `slot_uri` and uses it as the OWL property IRI,
which is the correct behavior for this vocabulary.

**Artifact affected:** `*.ttl` (OWL ontology files for all modules)
**Workaround:** Custom `src/wotis/generators/owl.py` — reads `slot_uri`,
emits it as the property IRI for OWL output.
**LinkML issue:** By design — `gen-owl` intentionally uses slot name for
property IRI. WoT's split naming convention is outside the generator's scope.

### 11. No multi-domain support for OWL properties

**Symptom:** Properties used by multiple classes cannot express domain declarations natively. `rdfs:domain` with multiple classes creates OWL intersection semantics (subject must be ALL classes), which is wrong for multi-domain properties.

**Artifact:** OWL (`.ttl`)

**Root cause:** `SlotDefinition.domain` accepts a single class name only. `domain_of` exists on `ClassDefinition` but `gen-owl` ignores it. `AnonymousSlotExpression` has no `domain` field. No way to express `rdfs:domain [ owl:unionOf (...) ]` or `schema:domainIncludes` natively in LinkML.

**Workaround:** Postprocessor emits `schema:domainIncludes` derived from SchemaView class→slot membership. This matches upstream WoT ontology convention (20+ `schema:domainIncludes` occurrences, zero `rdfs:domain`). See [OWL/RDF Modeling Guide §6](guidelines/owl-rdf-modeling.md#6-domain-declarations--design-decision).

**LinkML issue:** none filed

---

## JSON Schema Generator

### 6. JSON Schema generator cannot express all W3C TD structural patterns
The JSON Schema postprocessor (`src/wotis/postprocessors/jsonschema_postprocessor.py`) contains active transforms that compensate for generator gaps — including subclass flattening, oneOf dispatch, form variants, type normalization, identifier slot removal, ref resolution, and metadata cleanup. Gaps #9, #10, and #11 below document specific transforms; additional undocumented transforms (`_normalize_types`, `_simplify_exclusive_minimum`, `_remove_identifier_slots`, `_remove_excluded_defs`, `_resolve_refs`, `_clean_metadata`) handle structural adjustments the generator cannot produce natively.

### 7. No oneOf dispatch on a discriminator slot
**Symptom:** W3C `securityScheme` is a oneOf over the known schemes plus `additionalSecurityScheme` with a prefixed `scheme`; the generator does not use `designates_type` for this.
**Artifact:** `jsonschema.json`
**Workaround:** `jsonschema_postprocessor.py` → `_build_oneof_dispatch()`, driven by the `jsonschema_oneof_dispatch` annotation
**LinkML issue:** none found (2026-09-09)

### 8. No form variants per affordance type
**Symptom:** W3C has one form definition per location (root, property, action, event) with its own `op` values; the generator emits a single Form.
**Artifact:** `jsonschema.json`
**Workaround:** `jsonschema_postprocessor.py` → `_build_form_variants()`, driven by the `jsonschema_form_variants` annotation; the base branch takes the forms without `op`
**LinkML issue:** none found (2026-09-09)

### 9. Inlined dict slots always allow the object form
**Symptom:** For `titles`/`descriptions` the generator emits `anyOf` of the object form and the SimpleDict string form; W3C allows only the string form.
**Artifact:** `jsonschema.json`
**Workaround:** `jsonschema_postprocessor.py` → `_fix_additional_props_anyof()`, keeps only the string form for a key + one string value class
**LinkML issue:** none found (2026-09-09)

---

## SHACL Generator

### 8. Known SHACL authoring issues
Known SHACL issues from `issues.txt`:

- `dcterms:created` and `dcterms:modified` appear in SHACL shapes but not in the ontology (missing from hand-authored OWL). Not a LinkML generator gap — an ontology authoring gap.
- Prefix inconsistency: SHACL uses `dcterms:` (`http://purl.org/dc/terms/`) but context uses `dct:` for the same namespace. Authoritative choice: `dcterms:` (correct per Dublin Core `/terms/` namespace).

### 12. Heterogeneous scalar `exactly_one_of` omits SHACL alternatives
**Symptom:** A slot with `exactly_one_of` ranges `string` and `langString` is emitted only as `sh:datatype xsd:string`, omitting `rdf:langString`.
**Artifact:** `shapes.shacl.ttl`
**Workaround:** `shacl_postprocessor.py` → `post_process_shacl()`, which emits `sh:or` branches for slots with a `langString` alternative.
**LinkML references:** [discussion #2199](https://github.com/orgs/linkml/discussions/2199), [discussion #2896](https://github.com/orgs/linkml/discussions/2896), and [linkml-model PR #276](https://github.com/linkml/linkml-model/pull/276)

---

## Cross-Artifact Naming Inconsistencies (not generator bugs — schema authoring issues)

From `issues.txt` — these need fixing in the schema, not in a postprocessor:

| Field in schema | Name in spec/docs | Action needed |
|---|---|---|
| `supportContact` | `support` | Align: rename slot or add alias |
| `baseURI` | `base` | Align: rename slot or add alias |

---

## Notes

- SHACL and OWL are lower-priority artifacts currently — do not block PRs on these gaps.
- For any gap marked "unknown LinkML issue", run `/check-linkml <feature>` before writing new code — the generator may already support it in a newer version.
- IDs (assertion anchors, `td-*` IDs) must never change once published — they are normative identifiers used by implementations.

## Reference Sources

| Source | URL | What it covers |
|---|---|---|
| LinkML metamodel docs | https://linkml.io/linkml-model/latest/docs/ | What is valid in LinkML YAML (meta-slots, annotations) |
| SlotDefinition | https://linkml.io/linkml-model/latest/docs/SlotDefinition/ | All valid slot meta-slots |
| ClassDefinition | https://linkml.io/linkml-model/latest/docs/ClassDefinition/ | All valid class meta-slots |
| linkml-model source | https://github.com/linkml/linkml-model/tree/main/linkml_model | Authoritative metamodel source |
| JSON Schema generator | https://linkml.io/linkml/generators/json-schema.html | Generator behavior and options |
| JSON-LD context generator | https://linkml.io/linkml/generators/jsonld-context.html | Generator behavior and options |
| SHACL generator | https://linkml.io/linkml/generators/shacl.html | Generator behavior and options |
| linkml/linkml issues | https://github.com/linkml/linkml/issues | Tooling bugs and feature requests |
| linkml/linkml-model issues | https://github.com/linkml/linkml-model/issues | Metamodel bugs and feature requests |

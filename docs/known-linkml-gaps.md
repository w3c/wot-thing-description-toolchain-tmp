# Known LinkML Generator Gaps

Before writing a new postprocessor, run `/check-linkml <feature>` — a gap here may be fixed in a newer LinkML version.

Each entry: **what the gap is**, **which artifact(s) affected**, **current workaround**, **LinkML issue if known**.

---

## JSON-LD Context Generator

### 1. Language maps are not derived from `langString` alternatives
**Symptom:** The context generator does not derive `@container: "@language"`
for WoT multilingual values from a `langString` alternative or the
`MultiLanguage` value model.
**Artifact:** `context.jsonld`
**Status:** Open. The current context retains LinkML's generated indexed-map
representation; it must not be changed until the TD language-map mapping is
specified and tested with expansion and compaction.
**LinkML issue:** unknown — report as "derive JSON-LD language containers from
language-keyed LinkML maps".

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
**Symptom:** LinkML now emits `@container: "@index"` for an inlined keyed
map, but it cannot emit the RDF predicate carried by the JSON map key, for
example `@index: "td:hasInstanceConfiguration"` or
`@index: "jsonschema:propertyName"`.
**Artifact:** `context.jsonld`
**WoT requirement:** TD JSON-LD expansion and compaction must preserve names
from `securityDefinitions`, `schemaDefinitions`, affordance maps, and nested
Data Schema `properties` maps as RDF statements.
**Current limitation:** The LinkML `instantiates` metaslot does not inform the
current JSON-LD context generator's `@index` value.
**Workaround:** A small WoT context-composition adapter reads an explicit
schema-declared index predicate until LinkML can generate it natively.
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

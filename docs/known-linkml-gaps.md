# Known LinkML Generator Gaps

Before writing a new postprocessor, check the current LinkML release — a gap here may be fixed in a newer version.

Each entry: **what the gap is**, **which artifact(s) affected**, **current workaround**, **LinkML issue if known**.

---

## JSON-LD Context Generator

`context.jsonld` is the unmodified output of the LinkML generator; the toolchain has no JSON-LD context postprocessor.

### 1. `@container: @language` not set for `langString` slots
**Symptom:** Slots with `range: langString` or `exactly_one_of` branches with `langString` range are emitted without `@container: @language`, making multilingual values serialize incorrectly.
**Artifact:** `context.jsonld`
**Workaround:** none
**LinkML issue:** unknown

### 2. `@container: @set` not set for multivalued slots
**Symptom:** Multivalued slots missing `@container: @set` in the context, causing JSON-LD framing to treat arrays as singletons.
**Artifact:** `context.jsonld`
**Workaround:** none
**LinkML issue:** unknown — run `/check-linkml multivalued @set container`

### 3. `@container: @index` + `@type: @id` not set for inlined dict-keyed slots
**Symptom:** Slots that are `inlined: true`, `multivalued: true`, and not `inlined_as_list` (i.e., keyed dicts like `securityDefinitions`) are not emitted with `@container: @index` and `@type: @id`.
**Artifact:** `context.jsonld`
**Workaround:** none
**LinkML issue:** unknown — run `/check-linkml inlined dict index container`

### 4. `@type` not set for default-range slots
**Symptom:** Slots whose range equals the schema `default_range` do not get `@type` set in the context entry.
**Artifact:** `context.jsonld`
**Workaround:** none
**LinkML issue:** unknown — run `/check-linkml default_range @type context`

### 5. `@type` handling for `exactly_one_of` with mixed ranges
**Symptom:** Slots with `exactly_one_of` branches with different ranges emit no `@type`; with a single uniform range, the XSD type must be constructed manually.
**Artifact:** `context.jsonld`
**Workaround:** none
**LinkML issue:** unknown — run `/check-linkml exactly_one_of range context type`

---

## JSON Schema Generator

### 6. JSON Schema generator cannot express all W3C TD structural patterns
The JSON Schema postprocessor (`src/wot_toolchain/artifacts/jsonschema/postprocess.py`) contains active transforms that compensate for generator gaps — including subclass flattening, oneOf dispatch, form variants, type normalization, identifier slot removal, ref resolution, and metadata cleanup. Gaps #9, #10, and #11 below document specific transforms; additional undocumented transforms (`_normalize_types`, `_simplify_exclusive_minimum`, `_remove_identifier_slots`, `_remove_excluded_defs`, `_resolve_refs`, `_clean_metadata`) handle structural adjustments the generator cannot produce natively.

### 7. No oneOf dispatch on a discriminator slot
**Symptom:** W3C `securityScheme` is a oneOf over the known schemes plus `additionalSecurityScheme` with a prefixed `scheme`; the generator does not use `designates_type` for this.
**Artifact:** `jsonschema.json`
**Workaround:** `artifacts/jsonschema/postprocess.py` → `_build_oneof_dispatch()`, driven by the `jsonschema_oneof_dispatch` annotation
**LinkML issue:** none found (2026-09-09)

### 8. No form variants per affordance type
**Symptom:** W3C has one form definition per location (root, property, action, event) with its own `op` values; the generator emits a single Form.
**Artifact:** `jsonschema.json`
**Workaround:** `artifacts/jsonschema/postprocess.py` → `_build_form_variants()`, driven by the `jsonschema_form_variants` annotation; the base branch takes the forms without `op`
**LinkML issue:** none found (2026-09-09)

### 9. Inlined dict slots always allow the object form
**Symptom:** For `titles`/`descriptions` the generator emits `anyOf` of the object form and the SimpleDict string form; W3C allows only the string form.
**Artifact:** `jsonschema.json`
**Workaround:** `artifacts/jsonschema/postprocess.py` → `_fix_additional_props_anyof()`, keeps only the string form for a key + one string value class
**LinkML issue:** none found (2026-09-09)

### 13. `list_elements_unique` emits no `uniqueItems`
**Symptom:** A multivalued slot with `list_elements_unique: true` is emitted as a plain array; W3C requires `uniqueItems: true` for `enum`.
**Artifact:** `jsonschema.json`
**Workaround:** `artifacts/jsonschema/generator.py` → `get_subschema_for_slot()` adds `uniqueItems: true` to every array slot with `list_elements_unique`
**LinkML issue:** unknown

### 14. A slot condition is named by the slot name, not its alias
**Symptom:** Class-level `slot_conditions` (in `rules`, `none_of`, `exactly_one_of`) on a slot with an `alias` emit the slot name as property name (`security_oneOf` instead of `oneOf`, `@name` instead of `name`), so the condition never matches.
**Artifact:** `jsonschema.json`
**Workaround:** `artifacts/jsonschema/generator.py` → `aliased_slot_name()` falls back to the alias of the slot the condition constrains
**LinkML issue:** unknown

### 15. "Not empty when present" becomes "mandatory" in SHACL and OWL
**Symptom:** `enum` is optional but must not be empty when present. Slot-level `minimum_cardinality: 1` emits the right `minItems: 1` in JSON Schema, but LinkML also emits `sh:minCount 1` (SHACL) and `owl:minCardinality 1` (OWL), which make the slot mandatory. An empty array has no triples in RDF, so the bound can not be violated there.
**Artifact:** `shapes.shacl.ttl`, `ontology.owl.ttl`
**Workaround:** `pipeline.py` → `_for_rdf()` gives the SHACL and OWL generators a schema copy without `minimum_cardinality: 1` on slots that are not required. The spec table reads "mandatory" from `required` only (`specgen/tables.py`).
**LinkML issue:** unknown

### 16. Keywords next to an inlined enum `$ref` were dropped
**Symptom:** `none_of` on a slot with an enum range emits `not` next to the `$ref`; inlining the enum kept only `description`.
**Artifact:** `jsonschema.json`
**Workaround:** `artifacts/jsonschema/refs.py` keeps every sibling keyword of the inlined `$ref`
**LinkML issue:** not a LinkML gap — toolchain transform

### 17. The partition dropped a subclass used as array item
**Symptom:** W3C root-level forms require `op`. The class `RootForm` in the JSON Schema profile states that, but the enum subset partition replaced the `items` of the root `forms` by its own variant and dropped the subclass.
**Artifact:** `jsonschema.json`
**Workaround:** `artifacts/jsonschema/partitions.py` → `_narrow_slot_items()` keeps a subclass of the partitioned class and adds the variant next to it (`allOf`)
**LinkML issue:** not a LinkML gap — toolchain transform

### 18. The catch-all branch of a oneOf dispatch was untyped
**Symptom:** The branch for values outside the known subclasses (gap #7) only constrained the discriminator; W3C `additionalSecurityScheme` also types the members of the base scheme.
**Artifact:** `jsonschema.json`
**Workaround:** `artifacts/jsonschema/subclasses.py` → `build_oneof_dispatch()` builds the catch-all from the dispatch class's own definition, without identifier slots
**LinkML issue:** not a LinkML gap — toolchain transform

---

## SHACL Generator

### 8. Known SHACL authoring issues
Known SHACL issues from `issues.txt`:

- `dcterms:created` and `dcterms:modified` appear in SHACL shapes but not in the ontology (missing from hand-authored OWL). Not a LinkML generator gap — an ontology authoring gap.
- Prefix inconsistency: SHACL uses `dcterms:` (`http://purl.org/dc/terms/`) but context uses `dct:` for the same namespace. Authoritative choice: `dcterms:` (correct per Dublin Core `/terms/` namespace).

### 12. Heterogeneous scalar `exactly_one_of` omits SHACL alternatives
**Symptom:** A slot with `exactly_one_of` ranges `string` and `langString` is emitted only as `sh:datatype xsd:string`, omitting `rdf:langString`.
**Artifact:** `shapes.shacl.ttl`
**Workaround:** `artifacts/shacl/postprocess.py` → `post_process_shacl()`, which emits `sh:or` branches for slots with a `langString` alternative.
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

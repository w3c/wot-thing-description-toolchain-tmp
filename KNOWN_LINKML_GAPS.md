# Known LinkML Generator Gaps

Gaps confirmed from postprocessors, `issues.txt`, and cross-artifact comparison.
Before writing a new postprocessor, run `/check-linkml <feature>` — a gap here may be fixed in a newer LinkML version.

Each entry: **what the gap is**, **which artifact(s) affected**, **current workaround**, **LinkML issue if known**.

---

## JSON-LD Context Generator

### 1. `@container: @language` not set for `langString` slots
**Symptom:** Slots with `range: langString` or `exactly_one_of` branches with `langString` range are emitted without `@container: @language`, making multilingual values serialize incorrectly.
**Artifact:** `context.jsonld`
**Workaround:** `jsonld_context_postprocessor.py` → `process_langstring_conditions()`
**LinkML issue:** unknown — run `/check-linkml langString @language container`

### 2. `@container: @set` not set for multivalued slots
**Symptom:** Multivalued slots missing `@container: @set` in the context, causing JSON-LD framing to treat arrays as singletons.
**Artifact:** `context.jsonld`
**Workaround:** `jsonld_context_postprocessor.py` → `process_multivalued_slots()`
**LinkML issue:** unknown — run `/check-linkml multivalued @set container`

### 3. `@container: @index` + `@type: @id` not set for inlined dict-keyed slots
**Symptom:** Slots that are `inlined: true`, `multivalued: true`, and not `inlined_as_list` (i.e., keyed dicts like `securityDefinitions`) are not emitted with `@container: @index` and `@type: @id`.
**Artifact:** `context.jsonld`
**Workaround:** `jsonld_context_postprocessor.py` → `process_inlined_slot()`
**LinkML issue:** unknown — run `/check-linkml inlined dict index container`

### 4. `@type` not set for default-range slots
**Symptom:** Slots whose range equals the schema `default_range` do not get `@type` set in the context entry.
**Artifact:** `context.jsonld`
**Workaround:** `jsonld_context_postprocessor.py` (default range block)
**LinkML issue:** unknown — run `/check-linkml default_range @type context`

### 5. `@type` handling for `exactly_one_of` with mixed ranges
**Symptom:** Slots with `exactly_one_of` branches with different ranges emit no `@type`; with a single uniform range, the XSD type must be constructed manually.
**Artifact:** `context.jsonld`
**Workaround:** `jsonld_context_postprocessor.py` → `process_exactly_one_of()`
**LinkML issue:** unknown — run `/check-linkml exactly_one_of range context type`

---

## JSON Schema Generator

### 6. JSON Schema postprocessor is currently empty
`src/wotis/postprocessors/json_schema_postprocessor.py` exists but is empty — no active fixes yet. All current JSON Schema correctness is handled entirely by the generator. If a new JSON Schema postprocessor fix is needed, it goes here.

### 7. Known schema-vs-instance gaps (from known-failures baselines)
The files `tests/td_gate_known_failures_td11.txt` and `tests/td_gate_known_failures_td20.txt` track valid TD instances that the generated JSON Schema wrongly rejects. These represent JSON Schema generator fidelity gaps. Each entry must link to a GitHub issue. Current status: files do not exist yet in `main` (added by PR #63).

---

## SHACL Generator

### 8. SHACL postprocessor is currently empty
`src/wotis/postprocessors/shacl_postprocessor.py` exists but is empty. Known SHACL issue from `issues.txt`:

- `dcterms:created` and `dcterms:modified` appear in SHACL shapes but not in the ontology (missing from hand-authored OWL). Not a LinkML generator gap — an ontology authoring gap.
- Prefix inconsistency: SHACL uses `dcterms:` (`http://purl.org/dc/terms/`) but context uses `dct:` for the same namespace. Authoritative choice: `dcterms:` (correct per Dublin Core `/terms/` namespace).

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

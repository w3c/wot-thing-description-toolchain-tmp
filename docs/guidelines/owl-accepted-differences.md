# OWL Generated vs Target: Known Differences

This document tracks ALL known differences between the generated OWL ontologies
(`resources/gens/owl/*.ttl`) and the upstream W3C targets
(`resources/upstream/ontology/target/*.ttl`).

Each difference is classified as:

- **ACCEPTED** — Intentional or inconsequential; do not re-investigate.
- **TODO** — Known gap that needs fixing; linked to the fix approach.
- **FIXED** — Was a gap, now resolved.

> **Rule:** Before reporting an OWL difference as new, check this table first.
> Before investigating a "bug" in generated OWL, check this table first.
> When a TODO is fixed, update the status here.

---

## Differences Table

### Serialization Format: LongTurtle

We use rdflib's **LongTurtle** serializer (with a thin custom subclass) instead of the
default compact Turtle serializer. LongTurtle is designed for machine-generated ontologies:

- **Diff-friendly.** One triple per line. Adding or removing any predicate is a 1-line diff.
  With inline dot (compact style), changing the last predicate produces a 2-line diff
  (`.` → `;` on previous line, new line with `.`). Same reasoning as trailing commas in
  Python/JSON.
- **Merge-friendly.** Single-predicate lines rarely cause git merge conflicts. Compact
  format where multiple triples share a line conflicts constantly.
- **Readable at scale.** Classes with 8+ predicates (common in OWL) are scannable with
  consistent indentation. Compact format wraps unpredictably.
- **Deterministic.** Sorted prefixes, sorted subjects, sorted predicates. Same graph →
  same bytes. Essential for CI diffing of generated output.
- **No special last line.** Every predicate line ends with `;`, terminator `.` on its own
  line. Reordering predicates = pure line swap, zero punctuation edits.

The trailing `;` before `.` and `.` on its own line differ from the hand-authored target
(which uses inline `.`). This is an intentional trade-off: the target is hand-edited
(inline dot is conventional for humans), our output is machine-generated (LongTurtle's
diff/merge properties matter more). See C5 below.

Our custom subclass (`WotTurtleSerializer`) overrides only:

| Override | Purpose |
|---|---|
| `predicateOrder` | W3C predicate ordering (type → label → subX → comment → domain → range) |
| `topClasses` + `orderSubjects()` | Subject grouping: Ontology → Classes → Individuals → Properties |
| `keywords = {}` | Emit explicit `rdf:type` instead of `a` shorthand |
| `startDocument()` | `@prefix` (Turtle) instead of `PREFIX` (SPARQL) syntax |

All other formatting — indentation, line breaks, trailing `;`, dot placement, blank node
layout — is inherited from LongTurtle unchanged.

### Ontology IRI Convention

Every schema's `id:` field **must not** end with `#`. The `id:` value becomes the
ontology subject IRI (e.g., `<https://www.w3.org/2019/wot/td>`). If it ends with `#`,
it matches the namespace prefix exactly, and rdflib serializes it as the prefix shorthand
(e.g., `td:` instead of `<https://www.w3.org/2019/wot/td>`). This breaks consistency
across modules and differs from upstream target style.

| Field | Purpose | Example |
|---|---|---|
| `id:` | Ontology IRI (no `#`) | `https://www.w3.org/2019/wot/td` |
| `prefixes: → td:` | Namespace (with `#`) | `https://www.w3.org/2019/wot/td#` |

When adding a new ontology module:

1. Set `id:` to the base IRI **without** trailing `#`.
2. Set the prefix in `prefixes:` to the base IRI **with** trailing `#`.
3. Verify after generation that the ontology block renders as
   `<https://...> rdf:type owl:Ontology`, not as a prefix shorthand.

### Serialization / Cosmetic

These are semantically equivalent. Remaining differences from the hand-authored target.

| # | Difference | Target | Generated | Status | Fix approach |
|---|-----------|--------|-----------|--------|-------------|
| C1 | `rdf:type` syntax | Explicit `rdf:type` predicate | Explicit `rdf:type` predicate | FIXED | Custom serializer: `self.keywords = {}` |
| C2 | `@prefix rdf:` declaration | Declared | Declared | FIXED | Fixed by C1 (explicit `rdf:type` → rdflib declares prefix) |
| C3 | Subject ordering | Ontology → Classes → Individuals → Properties | Ontology → Classes → Individuals → Properties | FIXED | Custom serializer: `topClasses` + `orderSubjects()` override |
| C4 | Predicate ordering | rdf:type → label → subX → comment → domain → range → isDefinedBy | Matching target order | FIXED | Custom serializer: `predicateOrder` attribute |
| C5 | Dot placement / trailing `;` | Inline `.` on last predicate | `.` on own line, trailing `;` | ACCEPTED | LongTurtle default — diff/merge-friendly (see rationale above) |

### Predicate Choices

| # | Difference | Target | Generated | Status | Notes |
|---|-----------|--------|-----------|--------|-------|
| P1 | Class/property descriptions | `rdfs:comment @en` | `skos:definition` | ACCEPTED | gen-owl default; semantically valid |
| P2 | Domain (single-class) | `schema:domainIncludes` | `rdfs:domain` | ACCEPTED | Stronger OWL semantics, acceptable |
| P3 | Domain (multi-class) | `schema:domainIncludes` | `schema:domainIncludes` | FIXED | Postprocessor `_add_domain_includes` |
| P4 | Range | `schema:rangeIncludes` | `rdfs:range` | ACCEPTED | Stronger OWL semantics, acceptable |
| P5 | Ontology author predicate | `dcterms:author` (non-standard) | `dcterms:creator` | ACCEPTED | Upstream uses `dcterms:author` which does not exist in Dublin Core Terms; `dcterms:creator` is the correct predicate |

### Lang Tags

| # | Difference | Target | Generated | Status | Notes |
|---|-----------|--------|-----------|--------|-------|
| L1 | `rdfs:comment` lang tag | `@en` on all | `@en` on all | FIXED | Postprocessor `_add_lang_tags` |
| L2 | `rdfs:label` lang tag | No `@en` in target | `@en` on all | ACCEPTED | Generated is stricter — acceptable |
| L3 | `skos:definition` lang tag | N/A (not used in target) | `@en` on all | FIXED | Postprocessor `_add_lang_tags` |

### Extra Triples in Generated

| # | Triple | Present in target? | Status | Notes |
|---|--------|-------------------|--------|-------|
| E1 | `skos:definition` on all classes/properties | No | ACCEPTED | Consequence of P1 (ACCEPTED predicate choice) |
| E2 | `rdfs:subPropertyOf dcterms:title` on title, titleInLanguage | No | ACCEPTED | Schema-declared semantic relationship |
| E3 | `rdfs:subPropertyOf dcterms:description` on description, descriptionInLanguage | No | ACCEPTED | Schema-declared semantic relationship |
| E4 | `skos:note` on OperationType individuals (8+ notes) | No | ACCEPTED | Extra metadata from schema |
| E5 | `skos:note` on OperationType class (3 notes) | No | ACCEPTED | Extra metadata from schema |
| E6 | `rdfs:seeAlso schema:version` on versionInfo property | No | ACCEPTED | Extra metadata from schema |
| E7 | `rdfs:label` on ontology IRI | No `rdfs:label` in target | ACCEPTED | Postprocessor replaces gen-owl snake_case with `schema.title`; best practice to have both `rdfs:label` + `dcterms:title` |
| E8 | `supportContact`: `rdfs:domain td:Thing` + `rdfs:range xsd:anyURI` | No domain/range in target | INVESTIGATE | See task #14 — need to determine if schema or gen-owl adds these |
| E9 | `name`: `rdfs:range xsd:string` + wrong domain predicate | No range; target uses `schema:domainIncludes` not `rdfs:domain` | INVESTIGATE | See task #14 — spurious range + wrong domain predicate form |
| E10 | Entire `td:versionInfo` property block | Not present as OWL property in target | ACCEPTED | gen-owl emits OWL property from schema slot |
| E11 | `wotsec:proxy`, `wotsec:authorization`: `owl:ObjectProperty` with `rdfs:range xsd:anyURI` | Target has `owl:DatatypeProperty` | DEFERRED | Follows the schema as written (`wot_security.yaml`: `implements: owl:ObjectProperty`, `range: uri`). Kept as is; modeling to be re-checked by the editor later |

### Missing Triples in Generated

| # | Triple | Present in generated? | Status | Fix approach |
|---|--------|----------------------|--------|-------------|
| M1 | `hasInstanceConfiguration` `schema:domainIncludes wotsec:SecurityScheme` | `rdfs:domain wotsec:SecurityScheme` | FIXED | Added `domain: SecurityScheme` to schema YAML (see F9) |
| M2 | `hasInteractionAffordance` `schema:domainIncludes td:Thing` | `rdfs:domain td:Thing` | FIXED | Added `domain: Thing` to schema YAML (see F8) |

### Fixed Issues

| # | Issue | Resolution | Date |
|---|-------|-----------|------|
| F1 | `schema1:` prefix collision | `g.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)` | 2026-10 |
| F2 | `rdfs:isDefinedBy` missing | Emitted by `WotOwlGenerator.add_metadata` | 2026-10 |
| F3 | `skos:inScheme` wrong IRI | Emitted by `WotOwlGenerator.add_metadata` | 2026-10 |
| F4 | Enum subclasses not converted to individuals | Emitted as instances by `WotOwlGenerator.add_enum` (see [OWL Enum Modeling](owl-enum-modeling.md)) | 2026-10 |
| F5 | Aliased labels wrong | Emitted by `WotOwlGenerator.add_metadata` | 2026-10 |
| F6 | Multi-domain `schema:domainIncludes` | Added `_add_domain_includes` | 2026-10 |
| F7 | Missing `@en` lang tags | Added `_add_lang_tags` postprocessor (resilient to upstream) | 2026-10 |
| F8 | `hasInteractionAffordance` missing domain | Added `domain: Thing` to schema YAML | 2026-10 |
| F9 | `hasInstanceConfiguration` missing domain | Added `domain: SecurityScheme` to schema YAML | 2026-10 |
| F10 | `a` shorthand instead of `rdf:type` | Custom serializer `self.keywords = {}` (C1) | 2026-10 |
| F11 | `@prefix rdf:` not declared | Fixed by F10 — explicit `rdf:type` triggers declaration (C2) | 2026-10 |
| F12 | Subject ordering wrong | Custom serializer `orderSubjects()` override (C3) | 2026-10 |
| F13 | Predicate ordering wrong | Custom serializer `predicateOrder` attribute (C4) | 2026-10 |
| F14 | Ontology IRI inconsistency (hctl/jsonschema/wotsec used prefix form) | Removed trailing `#` from schema `id:` fields | 2026-10 |
| F15 | Ontology `rdfs:label` was snake_case (`"thing_description"`) | Postprocessor replaces with `schema.title` (human-readable) | 2026-10 |

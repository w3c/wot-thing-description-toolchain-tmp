# OWL/RDF Modeling Guide

**Author:** Mahda Noura (mahda.noura@siemens.com)
**Date:** 14.10.2026

---

How to author LinkML schema YAML so the OWL generation pipeline (`preprocessor → gen-owl → postprocessor`) produces correct OWL ontologies. Cross-references: [LinkML Naming Conventions](linkml-naming-conventions.md), [Postprocessor Conventions](postprocessor-conventions.md), [Known LinkML Gaps](../known-linkml-gaps.md).

## 1. OWL Property Types and `implements`

**Rule: every slot with a `slot_uri` that should appear in OWL output must declare `implements` with the correct OWL property type.**

Rationale: gen-owl infers property type from range (object range → `owl:ObjectProperty`, datatype range → `owl:DatatypeProperty`). This inference is often wrong for WoT because LinkML ranges and OWL ranges do not always align. The `implements` metaslot overrides the inference.

Valid values:
- `owl:ObjectProperty` — range is another OWL class or resource
- `owl:DatatypeProperty` — range is a literal (string, integer, datetime, etc.)
- `owl:AnnotationProperty` — metadata properties outside the OWL logical model

```yaml
# ObjectProperty — range is a class (VersionInfo)
version:
  slot_uri: td:versionInfo
  implements:
    - owl:ObjectProperty
  range: VersionInfo

# DatatypeProperty — range is a literal
instance:
  slot_uri: td:instance
  implements:
    - owl:DatatypeProperty
  range: string
```

**Rule: do NOT use `implements` on slots referencing external vocabulary terms.**

Rationale: external terms (e.g., `dcterms:created`, `dcterms:modified`) are defined in their own ontologies. Adding `implements` causes gen-owl to re-declare them inside this module's OWL output — polluting the ontology with foreign property declarations.

```yaml
# wrong — re-declares Dublin Core property in td.ttl
created:
  slot_uri: dcterms:created
  implements:
    - owl:AnnotationProperty

# correct — slot exists for JSON Schema output, OWL skips it
created:
  slot_uri: dcterms:created
  range: datetime
```

## 2. The Three-Way Split: JSON Key, OWL IRI, JSON-LD Bridge

A single concept has three distinct identifiers:

| Aspect | Source | Example |
|--------|--------|---------|
| JSON key | slot name (or `alias`) | `version` |
| OWL property IRI | `slot_uri` | `td:versionInfo` |
| Bridge | JSON-LD context entry | `"version": {"@id": "td:versionInfo"}` |

**Rule: `slot_uri` determines OWL identity. Slot name determines JSON key. Never assume they match.**

Rationale: the upstream WoT specification uses short JSON keys (`forms`, `actions`, `version`) that map to longer OWL IRIs (`td:hasForm`, `td:hasActionAffordance`, `td:versionInfo`) via JSON-LD context. Changing slot names to match OWL local names would break JSON Schema output.

```yaml
# slot name "forms" → JSON key "forms"
# slot_uri td:hasForm → OWL property <https://www.w3.org/2019/wot/td#hasForm>
# JSON-LD context: "forms": {"@id": "td:hasForm", "@container": "@set"}
forms:
  slot_uri: td:hasForm
  implements:
    - owl:ObjectProperty
  range: Form
  multivalued: true
```

See [Known LinkML Gaps #10](../known-linkml-gaps.md#10-gen-owl-uses-slot-name-not-slot_uri-as-owl-property-iri) for why `gen-owl` cannot be used directly — it emits slot name as OWL IRI, ignoring `slot_uri`.

## 3. The `alias` Pattern

When multiple OWL properties must serialize to the same JSON key in different classes, use distinct LinkML slot names with `alias` to map each to the shared JSON key.

**Rule: use distinct slot names + `alias` when two OWL properties share a JSON key. Each slot gets its own `slot_uri`.**

Rationale: LinkML slot names are globally unique. Without `alias`, two properties needing the same JSON key `"in"` would require the same slot name — impossible if they map to different OWL IRIs.

```yaml
# Top-level slot for Basic/Digest/Bearer — OWL property wotsec:in
in:
  slot_uri: wotsec:in
  implements:
    - owl:DatatypeProperty
  range: string

# Class attribute for APIKeySecurityScheme — OWL property wotsec:apikeyIn
# alias maps it to same JSON key "in"
attributes:
  apikeyIn:
    alias: in
    slot_uri: wotsec:apikeyIn
    implements:
      - owl:DatatypeProperty
    range: SecurityLocationType
```

The same pattern applies when JSON Schema keywords collide with OWL property names:

```yaml
# wotsec:oneOf (not JSON Schema oneOf)
security_oneOf:
  alias: oneOf
  slot_uri: wotsec:oneOf
  range: string
  multivalued: true

# wotsec:name (not the TD affordance name)
"@name":
  alias: name
  slot_uri: wotsec:name
  range: string
```

## 4. Slot Placement: Attributes vs Top-Level Slots

**Rule: slots that need `rdfs:range` in OWL output must be top-level slots (under `slots:`), not class attributes.**

Rationale: gen-owl emits `rdfs:range` only on top-level slot definitions. Class-level attributes produce `rdfs:subClassOf` restrictions but no global range declaration. The preprocessor's `_promote_attributes` transform handles this automatically — it lifts class attributes with `slot_uri` to top-level slots before gen-owl runs.

```yaml
# correct — top-level slot, gen-owl emits rdfs:range
slots:
  title:
    slot_uri: td:title
    range: string

# also correct — class attribute with slot_uri
# preprocessor promotes this to top-level before gen-owl runs
classes:
  VersionInfo:
    attributes:
      instance:
        slot_uri: td:instance
        implements:
          - owl:DatatypeProperty
        range: string
```

**Rule: slots without `slot_uri` are implementation artifacts — they have no OWL counterpart and are stripped by the preprocessor.**

Examples: `atContext` (JSON-LD `@context`), `atType` (JSON-LD `@type`), identifier slots for JSON map keys.

## 5. Annotations as Workarounds for gen-owl Literal Bug

Several RDF predicates expect `URIRef` objects, but gen-owl emits annotation values as `Literal` strings. The postprocessor converts these automatically.

**Rule: use annotation syntax in schema YAML for these predicates. `WotOwlGenerator.add_metadata` (`src/wot_toolchain/artifacts/owl/generator.py`) emits these values as URIRefs instead of Literals.**

Affected predicates:

| Predicate | Purpose | Example value |
|-----------|---------|---------------|
| `rdfs:seeAlso` | Related resource | `http://schema.org/version` |
| `rdfs:subClassOf` | Class hierarchy | `http://schema.org/Enumeration` |
| `rdfs:subPropertyOf` | Property hierarchy | `dcterms:title` |

```yaml
# Sub-property annotation on a slot
title:
  slot_uri: td:title
  annotations:
    rdfs:subPropertyOf: dcterms:title
```

The postprocessor converts `"dcterms:title"` from `Literal` CURIE to expanded `URIRef` via SchemaView prefix expansion, and URI-valued `rdfs:seeAlso` / `rdfs:subClassOf` strings to `URIRef`.

**Note:** `rdfs:isDefinedBy` and `skos:inScheme` are NOT handled via annotations — see §5a below.

### 5a. Automatic `rdfs:isDefinedBy` and `skos:inScheme`

Both predicates are added automatically by the toolchain, not via schema annotations. This avoids cluttering every class and slot with repetitive per-element annotations.

| Predicate | Source | Mechanism |
|-----------|--------|-----------|
| `rdfs:isDefinedBy` | `WotOwlGenerator.add_metadata` | Adds `rdfs:isDefinedBy <ontology-iri>` to every local subject (class/property in module namespace) |
| `skos:inScheme` | gen-owl via `from_schema` | LinkML `from_schema` has `slot_uri: skos:inScheme`; gen-owl emits natively. `WotOwlGenerator.add_metadata` rewrites object to ontology IRI |

**Rule: do NOT add `rdfs:isDefinedBy` or `skos:inScheme` annotations in schema YAML. The toolchain handles them automatically.**

Rationale: these are mechanical metadata — every term in a module is defined by that module's ontology. Repeating `rdfs:isDefinedBy: https://www.w3.org/2019/wot/td` on every class and slot adds noise without information. The postprocessor derives the value from the module namespace, keeping schema files focused on modeling semantics.

See [Known LinkML Gaps #10](../known-linkml-gaps.md#10-gen-owl-uses-slot-name-not-slot_uri-as-owl-property-iri) for background on why the custom generator and postprocessor exist.

## 6. Domain Declarations — Hybrid Approach

### Problem

OWL properties need domain declarations. Two distinct cases:

1. **Single-domain** — property belongs to exactly one class (e.g., `td:isSafe` → `ActionAffordance`)
2. **Multi-domain** — property shared across classes (e.g., `td:description` → `Thing`, `InteractionAffordance`, `SecurityScheme`, `DataSchema`)

### OWL Semantics

Multiple `rdfs:domain` triples create an OWL **intersection** — the subject must be an instance of ALL listed classes simultaneously. This is wrong for shared properties. `schema:domainIncludes` is a soft hint with no OWL entailment.

### Decision: Hybrid Strategy

| Case | Mechanism | Source |
|------|-----------|--------|
| Single-domain slot | `rdfs:domain` | `domain:` field in schema YAML → gen-owl emits natively |
| Multi-domain slot | `schema:domainIncludes` | Postprocessor derives from class→slot membership |

### Single-Domain: Schema `domain:` Field

LinkML `SlotDefinition.domain` accepts a single class name. gen-owl emits `rdfs:domain <class-uri>`. Works on top-level slots; class attributes survive because the preprocessor's `_promote_attributes` does `copy.deepcopy`.

```yaml
# Top-level slot — domain: directly on the slot
slots:
  version:
    slot_uri: td:versionInfo
    domain: Thing
    implements:
      - owl:ObjectProperty
    range: VersionInfo

# Class attribute — domain: also works, survives promotion
classes:
  ActionAffordance:
    attributes:
      safe:
        slot_uri: td:isSafe
        domain: ActionAffordance
        implements:
          - owl:DatatypeProperty
        range: boolean
```

Produces:

```turtle
td:versionInfo rdfs:domain td:Thing .
td:isSafe rdfs:domain td:ActionAffordance .
```

**Rule: add `domain: ClassName` to every slot/attribute that belongs to exactly one class.**

### Multi-Domain: Postprocessor `schema:domainIncludes`

For properties used by 2+ classes, the postprocessor's `_add_domain_includes` function scans class→slot membership via SchemaView and emits `schema:domainIncludes` for each class. No hardcoded lookup tables.

```turtle
td:description schema:domainIncludes td:Thing ;
    schema:domainIncludes td:InteractionAffordance ;
    schema:domainIncludes wotsec:SecurityScheme ;
    schema:domainIncludes jsonschema:DataSchema .
```

The function handles `slot_usage` overrides (e.g., `ObjectSchema.properties` overrides `slot_uri` to `jsonschema:properties`) and class attributes.

**Rule: do NOT add `domain:` to multi-domain slots. The postprocessor handles them automatically.**

### Rationale

1. **Semantic correctness:** `rdfs:domain` is safe and informative for single-domain properties. Multi-domain properties use `schema:domainIncludes` to avoid intersection semantics.
2. **Upstream alignment:** WoT upstream ontologies use `schema:domainIncludes` for multi-domain properties across td.ttl, hctl.ttl, jsonschema.ttl, wotsec.ttl.
3. **LinkML limitation:** `SlotDefinition.domain` is `str | ClassDefinitionName | None` — single class only. No native way to express multi-domain (see [Known LinkML Gaps #11](../known-linkml-gaps.md#11-no-multi-domain-support-for-owl-properties)).
4. **No hardcoded tables:** both mechanisms derive from schema structure — `domain:` field for single, class membership for multi.

## 7. Enum-to-OWL Patterns

Enums with `enum_uri` produce OWL named classes with named individuals.

**Rule: set `enum_uri` on enums that represent OWL classes. Set `meaning` on permissible values for individual IRIs.**

```yaml
OperationType:
  enum_uri: td:OperationType
  annotations:
    rdfs:isDefinedBy:
      value: https://www.w3.org/2019/wot/td
    rdfs:subClassOf:
      value: http://schema.org/Enumeration
  permissible_values:
    readProperty:
      meaning: td:readProperty
      description: Identifies the read operation on Property Affordances.
    writeProperty:
      meaning: td:writeProperty
      description: Identifies the write operation on Property Affordances.
```

This produces:

```turtle
td:OperationType a owl:Class ;
    rdfs:subClassOf schema:Enumeration .

td:readProperty a td:OperationType ;
    rdfs:label "readProperty" .
```

The postprocessor handles two conversions:
- `rdfs:subClassOf` on permissible values → `rdf:type` (upstream WoT convention: individuals are typed, not subclasses)
- `rdfs:subClassOf` annotation on the enum itself → `URIRef` (Literal→URIRef conversion, same as §5)

**Rule: enums without `enum_uri` are JSON Schema validation enums only — the preprocessor strips them before OWL generation.**

## 8. Accepted Differences from Upstream Ontology

The generated OWL output intentionally differs from upstream WoT ontologies in specific, documented ways. See [OWL Fix Rules](../owl-fix-rules.md) for the full list.

Key accepted differences:

| Difference | Rationale |
|------------|-----------|
| `rdfs:label` uses JSON key, not URI local name | JSON key is the developer-facing identifier |
| `owl:Class` only (no `rdfs:Class` dual-typing) | Valid OWL; dual-typing is redundant |
| No `@en` language tag on `rdfs:comment` | LinkML gen-owl behavior; acceptable |
| `rdfs:domain` for single-domain (upstream uses `schema:domainIncludes`) | Stronger but semantically correct for single-domain; multi-domain uses `schema:domainIncludes` (§6) |
| `rdfs:range` instead of `schema:rangeIncludes` | Valid OWL; stronger but correct |
| `rdfs:isDefinedBy` on all local subjects | Postprocessor adds automatically (§5a); matches upstream coverage |
| `skos:definition` alongside `rdfs:comment` | Both present, content identical |

**Rule: do not "fix" accepted differences. If a diff appears during OWL generation review, check the accepted differences list before filing it as a bug.**

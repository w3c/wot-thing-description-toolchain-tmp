# OWL ontologies

How to author LinkML schema YAML so the OWL generation pipeline (`preprocess_for_gen_owl` → `WotOwlGenerator` → `postprocess_owl_graph`, under `src/wot_toolchain/artifacts/owl/`) produces correct OWL ontologies. Cross-references: [LinkML Naming Conventions](../reference/linkml-naming-conventions.md), [Postprocessor Conventions](../guidelines/postprocessor-conventions.md), [LinkML gaps](../linkml-gaps.md). How the generated ontologies differ from the published TD 1.1 ontologies is recorded only in [OWL differences](../differences/owl.md).

## 1. OWL Property Types and `implements`

**Rule: declare `implements` with the correct OWL property type on a slot whose property type does not follow from its range.**

Rationale: gen-owl infers property type from range (object range → `owl:ObjectProperty`, datatype range → `owl:DatatypeProperty`). LinkML ranges and OWL ranges do not always align. The `implements` metaslot overrides the inference.

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

**Rule: a URI value that names no node of the Thing Description is a datatype property; a name that refers to a node the Thing Description defines is an object property ranging over the class of that node.**

Rationale: an object property without a range says nothing about its values, and an object property with an `xsd` range is wrong. Neither slot kind declares `implements`; the range decides.

```yaml
# DatatypeProperty, rdfs:range xsd:anyURI — the value is an endpoint URI
authorization:
  slot_uri: wotsec:authorization
  range: uri

# ObjectProperty, rdfs:range wotsec:SecurityScheme — the value is the name
# of an entry of securityDefinitions
security:
  slot_uri: td:hasSecurityConfiguration
  range: SecurityScheme
```

Generated: `hctl:hasAnchor`, `wotsec:proxy`, `wotsec:authorization`, `wotsec:token` and `wotsec:refresh` are `owl:DatatypeProperty` with `rdfs:range xsd:anyURI`. `td:hasSecurityConfiguration` is an `owl:ObjectProperty` with `rdfs:range wotsec:SecurityScheme`, and `hctl:hasAdditionalOutputSchema` one with `rdfs:range jsonschema:DataSchema`. See [JSON-LD context, Rule 2](jsonld-context.md#rule-2-a-uri-value-is-a-literal-a-name-reference-is-a-node) for the JSON-LD and SHACL side.

## 2. The Three-Way Split: JSON Key, OWL IRI, JSON-LD Bridge

A single concept has three distinct identifiers:

| Aspect | Source | Example |
|--------|--------|---------|
| JSON key | slot name (or `alias`) | `version` |
| OWL property IRI | `slot_uri` | `td:versionInfo` |
| Bridge | JSON-LD context entry | `"version": {"@type": "@id", "@id": "versionInfo"}`, resolved against the `td` `@vocab` |

**Rule: `slot_uri` determines OWL identity. Slot name determines JSON key. Never assume they match.**

Rationale: the upstream WoT specification uses short JSON keys (`forms`, `actions`, `version`) that map to longer OWL IRIs (`td:hasForm`, `td:hasActionAffordance`, `td:versionInfo`) via JSON-LD context. Changing slot names to match OWL local names would break JSON Schema output.

```yaml
# slot name "forms" → JSON key "forms"
# slot_uri td:hasForm → OWL property <https://www.w3.org/2019/wot/td#hasForm>
# JSON-LD context: "forms": {"@id": "hasForm", "@container": "@set"}
forms:
  slot_uri: td:hasForm
  range: Form
  multivalued: true
```

## 3. The `alias` Pattern

When multiple OWL properties must serialize to the same JSON key in different classes, use distinct LinkML slot names with `alias` to map each to the shared JSON key.

**Rule: use distinct slot names + `alias` when two OWL properties share a JSON key. Each slot gets its own `slot_uri`.**

Rationale: LinkML slot names are globally unique. Without `alias`, two properties needing the same JSON key `"in"` would require the same slot name — impossible if they map to different OWL IRIs.

```yaml
# Top-level slot for Basic/Digest/Bearer — OWL property wotsec:in
in:
  slot_uri: wotsec:in
  range: SecurityLocationType

# Class attribute for APIKeySecurityScheme — OWL property wotsec:apikeyIn
# alias maps it to same JSON key "in"
attributes:
  apikeyIn:
    alias: in
    slot_uri: wotsec:apikeyIn
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

Rationale: gen-owl emits `rdfs:range` only on top-level slot definitions. Class-level attributes produce `rdfs:subClassOf` restrictions but no global range declaration. `_promote_attributes` in `src/wot_toolchain/artifacts/owl/pre_passes.py` handles this automatically — it lifts class attributes with `slot_uri` to top-level slots before gen-owl runs.

```yaml
# correct — top-level slot, gen-owl emits rdfs:range
slots:
  version:
    slot_uri: td:versionInfo
    range: VersionInfo

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

Several RDF predicates expect `URIRef` objects, but gen-owl emits annotation values as `Literal` strings.

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

The generator expands the CURIE `dcterms:title` to a `URIRef` via SchemaView prefix expansion, and emits URI-valued `rdfs:seeAlso` / `rdfs:subClassOf` strings as `URIRef`.

**Note:** `rdfs:isDefinedBy` and `skos:inScheme` are NOT handled via annotations — see §5a below.

### 5a. Automatic `rdfs:isDefinedBy` and `skos:inScheme`

Both predicates are added automatically by the toolchain, not via schema annotations. This avoids cluttering every class and slot with repetitive per-element annotations.

| Predicate | Source | Mechanism |
|-----------|--------|-----------|
| `rdfs:isDefinedBy` | `WotOwlGenerator.add_metadata` | Adds `rdfs:isDefinedBy <ontology-iri>` to every local subject (class/property in module namespace) |
| `skos:inScheme` | gen-owl via `from_schema` | LinkML `from_schema` has `slot_uri: skos:inScheme`; gen-owl emits natively. `WotOwlGenerator.add_metadata` rewrites object to ontology IRI |

**Rule: do NOT add `rdfs:isDefinedBy` or `skos:inScheme` annotations in schema YAML. The toolchain handles them automatically.**

Rationale: these are mechanical metadata — every term in a module is defined by that module's ontology. Repeating `rdfs:isDefinedBy: https://www.w3.org/2019/wot/td` on every class and slot adds noise without information. The generator uses the ontology IRI as the value, keeping schema files focused on modeling semantics.

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
| Multi-domain slot | `schema:domainIncludes` | `_add_domain_includes` derives from class→slot membership |

### Single-Domain: Schema `domain:` Field

LinkML `SlotDefinition.domain` accepts a single class name. gen-owl emits `rdfs:domain <class-uri>`. Works on top-level slots; class attributes survive because `_promote_attributes` does `copy.deepcopy`.

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
        range: boolean
```

Produces:

```turtle
td:versionInfo rdfs:domain td:Thing .
td:isSafe rdfs:domain td:ActionAffordance .
```

**Rule: add `domain: ClassName` to every slot/attribute that belongs to exactly one class.**

### Multi-Domain: `schema:domainIncludes`

For properties used by 2+ classes, `_add_domain_includes` in `src/wot_toolchain/artifacts/owl/passes.py` scans class→slot membership via SchemaView and emits `schema:domainIncludes` for each class. No hardcoded lookup tables.

```turtle
td:description schema:domainIncludes td:Thing ;
    schema:domainIncludes td:InteractionAffordance ;
    schema:domainIncludes wotsec:SecurityScheme ;
    schema:domainIncludes jsonschema:DataSchema .
```

The function handles `slot_usage` overrides (e.g., `ObjectSchema.properties` overrides `slot_uri` to `jsonschema:properties`) and class attributes.

**Rule: do NOT add `domain:` to multi-domain slots. `_add_domain_includes` handles them automatically.**

### Rationale

1. **Semantic correctness:** `rdfs:domain` is safe and informative for single-domain properties. Multi-domain properties use `schema:domainIncludes` to avoid intersection semantics.
2. **Upstream alignment:** WoT upstream ontologies use `schema:domainIncludes` for multi-domain properties across td.ttl, hctl.ttl, jsonschema.ttl, wotsec.ttl.
3. **LinkML limitation:** `SlotDefinition.domain` is `str | ClassDefinitionName | None` — single class only. No native way to express multi-domain (see [LinkML gaps, Multiple domains](../linkml-gaps.md#multiple-domains)).
4. **No hardcoded tables:** both mechanisms derive from schema structure — `domain:` field for single, class membership for multi.

## 7. Enum-to-OWL Patterns

Enums with `enum_uri` produce OWL classes whose permissible values are typed instances of the class.

**Rule: set `enum_uri` on enums that represent OWL classes. Set `meaning` on permissible values for individual IRIs.**

```yaml
OperationType:
  enum_uri: td:OperationType
  annotations:
    rdfs:subClassOf:
      value: http://schema.org/Enumeration
  permissible_values:
    readproperty:
      meaning: td:readProperty
      description: Identifies the read operation on Property Affordances.
    writeproperty:
      meaning: td:writeProperty
      description: Identifies the write operation on Property Affordances.
```

**Rule: enums without `enum_uri` are JSON Schema validation enums only — the preprocessor strips them before OWL generation.**

### 7.1 Generated shape

| Element | Emitted triples |
|---------|-----------------|
| Enum | `a owl:Class`, `rdfs:label`, `skos:definition`, `rdfs:isDefinedBy <ontology>`, `skos:inScheme <ontology>` |
| Enum with `rdfs:subClassOf` annotation | additionally `rdfs:subClassOf <IRI>`, e.g. `schema:Enumeration` |
| Permissible value with `meaning` | IRI = `meaning`; `a <Enum>`, `rdfs:label` (the value text), `skos:definition`, `rdfs:isDefinedBy <ontology>` (own namespace only) |
| Permissible value without `meaning` | nothing |

`rdfs:subClassOf schema:Enumeration` is not added by code. It comes from the schema annotation on `OperationType` (`resources/schemas/hypermedia.yaml`), which `WotOwlGenerator.add_metadata` emits as an IRI. Only `td:OperationType` carries it today.

Emitted by `WotOwlGenerator.add_enum` and `_add_enum_instance` in `src/wot_toolchain/artifacts/owl/generator.py`.

### 7.2 Not emitted

- `owl:NamedIndividual` declaration on values
- `owl:oneOf` covering axiom on the enum class
- `skos:Concept` typing
- `linkml:permissible_values`

### 7.3 Decision

**Rule: an enum is an open class whose values are typed instances, following the schema.org enumeration pattern, not the closed `owl:oneOf` enumeration of OWL textbooks.**

Consequence: the OWL enum class has no closure axiom, so the ontology does not state that the listed values are the only members. The closed value set is enforced by the validation artifacts instead:

- SHACL: `sh:in ( td:readProperty ... )` on `hctl:hasOperationType` (`resources/gens/shacl/shapes.shacl.ttl`)
- JSON Schema: `"enum": [ "readproperty", ... ]` in the array branch of `op` (`resources/gens/jsonschema/jsonschema.json`)

### 7.4 Option

Selected by `OwlOptions(permissible_values=PermissibleValueKind.INSTANCE)` (`src/wot_toolchain/artifacts/owl/options.py`), set by the pipeline in `src/wot_toolchain/pipeline.py`. The other kinds (`CLASS`, `INDIVIDUAL`) fall through to upstream `add_enum`.

### 7.5 Example (`resources/gens/owl/td.ttl`, abridged)

```turtle
td:OperationType
    rdf:type owl:Class ;
    rdfs:label "OperationType"@en ;
    rdfs:subClassOf schema:Enumeration ;
    rdfs:isDefinedBy <https://www.w3.org/2019/wot/td> ;
    skos:inScheme <https://www.w3.org/2019/wot/td> ;
.

td:readProperty
    rdf:type td:OperationType ;
    rdfs:label "readProperty"@en ;
    skos:definition "Identifies the read operation on Property Affordances to retrieve the corresponding data."@en ;
    rdfs:isDefinedBy <https://www.w3.org/2019/wot/td> ;
.
```

## 8. Differences from the published ontologies

The generated ontologies differ from the published TD 1.1 ontologies, for example in `owl:Class`-only typing, `rdfs:domain` and `rdfs:range` instead of single-class includes, and `rdfs:isDefinedBy` values. Every difference, with its status, is recorded in [OWL differences](../differences/owl.md); check there before treating an OWL diff as a bug.

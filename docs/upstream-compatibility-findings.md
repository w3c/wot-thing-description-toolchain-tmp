# Upstream Compatibility Findings

This document records differences between upstream W3C WoT resources that
affect how this toolchain can generate mutually consistent artifacts. These
findings are not resolved by this toolchain without Working Group agreement.

## API Key `in` predicate

**Status:** Open for Working Group discussion.

### Finding

The upstream security ontology declares `wotsec:apikeyIn` as a datatype
property whose domain includes `wotsec:APIKeySecurityScheme`. The JSON member
used in a TD serialization is nevertheless named `in`.

The published JSON-LD context scopes the security vocabulary beneath
`securityDefinitions` and maps that JSON member to `wotsec:in`, including for
API key security-scheme objects. The upstream context merger applies the same
security context to all values of both `security` and `securityDefinitions`;
it does not select a separate context according to the value of `scheme`.

Consequently, an API key scheme such as the following expands with
`wotsec:in`, not `wotsec:apikeyIn`:

```json
{
  "securityDefinitions": {
    "api_key": {
      "scheme": "apikey",
      "in": "header"
    }
  }
}
```

### Evidence

- [Security ontology: `wotsec:apikeyIn`](https://github.com/w3c/wot-thing-description/blob/main/ontology/wotsec.ttl)
- [Security context: `"in"` maps to `wotsec:in`](https://github.com/w3c/wot-thing-description/blob/main/context/wot-security-context.jsonld)
- [Context merger: security context scopes](https://github.com/w3c/wot-thing-description/blob/main/context/merge.js)
- [Published TD 2.0 context](https://www.w3.org/ns/wot-next/td)

### Effect on this toolchain

The LinkML model can represent the ontology-level API key predicate with a
class-specific `slot_uri: wotsec:apikeyIn`. However, a JSON-LD context scoped
only at `securityDefinitions` cannot apply that predicate only when
`"scheme": "apikey"`; JSON-LD context selection does not dispatch on that
member value.

Generating `wotsec:apikeyIn` for the API key slot while generating the
published JSON-LD context would therefore create an RDF mapping difference
between this toolchain's OWL or SHACL artifacts and JSON-LD expansion.

### Decision requested

The Working Group should decide which predicate is canonical for the API key
`in` member:

1. Preserve the published JSON-LD behavior and use `wotsec:in` for every
   security-scheme serialization.
2. Use `wotsec:apikeyIn` for API key schemes, which requires an upstream
   JSON-LD context design that can select that mapping and an assessment of
   compatibility with existing TD processors.
3. Define an explicit RDF relationship between `wotsec:apikeyIn` and
   `wotsec:in`, then specify which term JSON-LD expansion must emit.

Until that decision is made, the toolchain must not silently choose a new
JSON-LD mapping. Generated contexts should remain compatible with the
published TD context, and any ontology or SHACL distinction must be reported
as an intentional, tracked difference.

## TD `schemaDefinitions` ontology declaration

**Status:** Confirmed upstream ontology completeness gap.

### Finding

The TD 1.1 spec defines `schemaDefinitions` as a Thing-level member:

> **schemaDefinitions** — Set of named data schemas. To be used in a schema
> name-value pair inside an AdditionalExpectedResponse object. — optional —
> Map of DataSchema

The TD 1.1 JSON-LD context declares it with `@container: @index` (plain
key-based indexing, no semantic `@index` property):

```json
"schemaDefinitions": {
    "@id": "td:schemaDefinitions",
    "@type": "@id",
    "@container": "@index"
}
```

The TD ontology does not declare `td:schemaDefinitions` as a property,
despite it being referenced in the spec, context, and SHACL validation.
The upstream SHACL shapes (`validation/td-validation.ttl`) do reference
`td:schemaDefinitions` via `sh:path`:

```turtle
sh:property [
    sh:path td:schemaDefinitions ;
    sh:node :DataSchemaShape ;
    sh:order 18 ;
] ;
```

So the term is declared in spec, context, and SHACL — only the OWL ontology
omits it.

Note: unlike `securityDefinitions` which uses `"@index": "hasInstanceConfiguration"`
to give index keys a semantic property, `schemaDefinitions` uses plain
`@container: @index` — the JSON object keys are opaque string indices with no
RDF property mapping. The toolchain schema previously had an incorrect
`jsonld_index: td:hasInstanceConfiguration` annotation on the `schemaDefinitions`
slot, copied from `securityDefinitions`. This has been corrected.

### Evidence

- [TD 1.1 spec: Thing member table](https://www.w3.org/TR/wot-thing-description11/#thing) — `schemaDefinitions` listed as optional Map of DataSchema
- [TD 1.1 context: `schemaDefinitions`](https://github.com/w3c/wot-thing-description/blob/main/context/td-context-1.1.jsonld) — `@id: td:schemaDefinitions`, `@container: @index`, no `@index` key
- [TD ontology](https://github.com/w3c/wot-thing-description/blob/main/ontology/td.ttl) — no `td:schemaDefinitions` declaration
- [TD SHACL validation: `td:schemaDefinitions`](https://github.com/w3c/wot-thing-description/blob/main/validation/td-validation.ttl) — `sh:path td:schemaDefinitions` on ThingShape

### Effect on this toolchain

The toolchain generates `td:schemaDefinitions` as an ObjectProperty from the
LinkML source. This is correct — the term is spec-defined and context-mapped.
The upstream ontology omission should not cause the toolchain to suppress
generation. The JSON-LD context must use plain `@container: @index` without
an `@index` key, matching the upstream context.

## Data Schema `type` RDF representation

**Status:** Under investigation; no mapping change has been approved.

### Finding

TD JSON distinguishes the semantic JSON-LD keyword `@type` from the Data
Schema member `type`. For example, a Property Affordance can use
`"@type": "saref:OnOffState"` and `"type": "string"` at the same time.

The TD 1.1 JSON-LD context maps the Data Schema member `type` to the JSON-LD
keyword `@type`; its values expand to Data Schema classes such as
`jsonschema:StringSchema`. The context does not map the JSON member `type` to
the predicate `jsonschema:type`, and the upstream JSON Schema ontology does
not declare `jsonschema:type`.

The current LinkML schema declares a `type` slot with
`slot_uri: jsonschema:type`. That is therefore not sufficient evidence that
the slot URI is the correct RDF representation of the TD JSON member. The
semantic status of `jsonschema:type` must be resolved separately from the
unambiguous context and ontology gaps in this document.

### Evidence

- [TD 1.1 context: Data Schema `type`](https://github.com/w3c/wot-thing-description/blob/main/context/td-context-1.1.jsonld)
- [JSON Schema context: `type` and Data Schema classes](https://github.com/w3c/wot-thing-description/blob/main/context/json-schema-context.jsonld)
- [JSON Schema ontology](https://github.com/w3c/wot-thing-description/blob/main/ontology/jsonschema.ttl)

### Effect on this toolchain

Do not use `jsonschema:type` as the JSON-LD expansion of a TD Data Schema
`type` member. Before changing the LinkML mapping, add a round-trip test with
both `@type` and `type`, then determine whether `jsonschema:type` has an
independent ontology role that must be retained.

## TD `versionInfo` — AnnotationProperty vs ObjectProperty

**Status:** Upstream inconsistency between ontology and JSON-LD context.

### Finding

The upstream TD ontology declares `td:versionInfo` as an `owl:AnnotationProperty`:

```turtle
# upstream td.ttl
:versionInfo rdf:type owl:AnnotationProperty ;
    rdfs:label "versionInfo" ;
    rdfs:comment "Provides version information."@en ;
    rdfs:seeAlso schema:version ;
    rdfs:isDefinedBy <https://www.w3.org/2019/wot/td> .
```

However, the published JSON-LD context maps the `"version"` key with `@type: @id`:

```json
// td-context-1.1.jsonld
"version": {
    "@id": "td:versionInfo",
    "@type": "@id"
}
```

`@type: @id` means the value is a node reference — semantically an ObjectProperty,
not an AnnotationProperty. AnnotationProperties are metadata about the ontology
document itself (like `owl:versionInfo`), invisible to OWL reasoners. But
`td:versionInfo` links a Thing instance to a structured Version object with
`instance` and `model` fields — that is instance-level data, not ontology metadata.

### Evidence

- [TD ontology: `versionInfo` as AnnotationProperty](https://github.com/w3c/wot-thing-description/blob/main/ontology/td.ttl)
- [TD 1.1 context: `"version"` with `@type: @id`](https://github.com/w3c/wot-thing-description/blob/main/context/td-context-1.1.jsonld)
- [Spec Example 47](https://www.w3.org/TR/wot-thing-description11/#example-47): `"version": {"instance": "1.2.1"}` — structured object, not annotation metadata

### Toolchain decision

This toolchain declares `td:hasVersionInfo` as an `owl:ObjectProperty` with
`schema:rangeIncludes td:VersionInfo`. The rename from `versionInfo` to
`hasVersionInfo` follows the established WoT naming convention for object
properties (`hasForm`, `hasLink`, `hasInputSchema`, etc.) and avoids a
case-only collision between `td:versionInfo` (property) and `td:VersionInfo`
(class).

## TD `VersionInfo` — phantom class in context

**Status:** Upstream ontology completeness gap.

### Finding

The published JSON-LD context maps `"VersionInfo"` to `td:VersionInfo`:

```json
// td-context-1.1.jsonld
"VersionInfo": "td:VersionInfo"
```

The upstream TD ontology never defines `td:VersionInfo` as a class. The ontology
only has `td:versionInfo` (lowercase v, AnnotationProperty). Meanwhile, the
upstream TM ontology defines a separate `tm:Version` class:

```turtle
# upstream tm.ttl
:Version rdf:type owl:Class ;
    rdfs:comment "The Version is a container that provides versioning
                  information for the Thing Model definition."@en ;
    rdfs:isDefinedBy tm: ;
    rdfs:label "Version"@en .
```

The context maps to `td:VersionInfo`, the TM ontology defines `tm:Version` —
two different IRIs for what is semantically the same class. The `td:VersionInfo`
IRI is never defined in any upstream ontology file.

### Evidence

- [TD 1.1 context: `"VersionInfo"` → `td:VersionInfo`](https://github.com/w3c/wot-thing-description/blob/main/context/td-context-1.1.jsonld)
- [TD ontology: no `VersionInfo` class](https://github.com/w3c/wot-thing-description/blob/main/ontology/td.ttl)
- [TM ontology: `tm:Version` class](https://github.com/w3c/wot-thing-description/blob/main/ontology/tm.ttl)

### Toolchain decision

This toolchain defines `td:VersionInfo` as an `owl:Class` in the TD module,
matching what the published context expects. The Version container is used by
both TD and TM documents (TD uses `instance` and `model`; TM uses `model`),
so it belongs in the foundational TD vocabulary — not in the TM module that
depends on TD.

## TD `instance` / `model` — broken domain reference

**Status:** Upstream semantic error (confirmed via git history).

### Finding

The upstream TD ontology declares `td:instance` and `td:model` with
`schema:domainIncludes :versionInfo`:

```turtle
# upstream td.ttl
:instance rdf:type owl:DatatypeProperty ;
    rdfs:label "instance" ;
    rdfs:comment "Provides a version identicator of this TD instance."@en ;
    schema:domainIncludes :versionInfo ;
    rdfs:isDefinedBy <https://www.w3.org/2019/wot/td> .

:model rdf:type owl:DatatypeProperty ;
    rdfs:label "model" ;
    rdfs:comment "Provides a version indicator of the underlying TM."@en ;
    schema:domainIncludes :versionInfo ;
    rdfs:isDefinedBy <https://www.w3.org/2019/wot/td> .
```

`:versionInfo` is an AnnotationProperty, not a class. `schema:domainIncludes`
is meant to reference a class that instances of this property apply to. Pointing
it at a property IRI is semantically meaningless — no resource can be an instance
of an AnnotationProperty.

Git history shows this was originally `schema:domainIncludes :Thing`, which was
changed in a later commit. The intent was likely to express "these properties
belong to the Version container," but the wrong IRI was used (the property
`:versionInfo` instead of a class like `:VersionInfo`).

Both properties also lack a `schema:rangeIncludes` declaration in upstream,
though `instance` and `model` are clearly string-valued.

### Evidence

- [TD ontology: `instance` and `model`](https://github.com/w3c/wot-thing-description/blob/main/ontology/td.ttl)
- Git history: domain changed from `:Thing` to `:versionInfo` in upstream commit

### Toolchain decision

This toolchain sets `schema:domainIncludes td:VersionInfo` (the class, not the
property) and adds `schema:rangeIncludes schema:Text` to both properties.

## TM ontology — design issues and scope reduction

**Status:** Upstream design inconsistencies; toolchain generates corrected output.

### Finding: td: property re-declarations in tm.ttl

The upstream TM ontology re-declares several properties already fully defined
in td.ttl:

```turtle
# upstream tm.ttl — re-declarations
td:hasInteractionAffordance rdf:type owl:ObjectProperty ;
    rdfs:domain tm:ThingModel ;
    rdfs:label "hasInteractionAffordance" ;
    ...

td:hasLink rdf:type owl:ObjectProperty ;
    schema:domainIncludes tm:ThingModel ;
    ...

td:title rdf:type owl:DatatypeProperty ;
    schema:domainIncludes tm:ThingModel ;
    ...

td:description rdf:type owl:DatatypeProperty ;
    schema:domainIncludes tm:ThingModel ;
    ...
```

These re-declarations are redundant — OWL is open-world, so any property
defined in td.ttl can be used on any resource without redeclaration. Worse,
`td:hasInteractionAffordance` uses hard `rdfs:domain` instead of soft
`schema:domainIncludes`, which causes OWL reasoners to infer that every
resource with a `td:hasInteractionAffordance` triple is a `tm:ThingModel`.
This means every `td:Thing` with interaction affordances gets classified
as a ThingModel — semantic poison.

The other td: properties could legitimately add soft
`schema:domainIncludes tm:ThingModel` hints (additive, no inference
consequences), but even this is unnecessary documentation — TM reusing TD
properties is obvious from the spec and context.

### Finding: tm:Version, tm:instance, tm:model belong in td:

The upstream TM ontology defines `tm:Version` as a class and declares
`tm:hasVersion` as an ObjectProperty linking ThingModel to Version.

However, both TD and TM documents use the same `"version"` container with the
same `"instance"` and `"model"` fields. Spec Example 47 shows a TD with
`"version": {"instance": "1.2.1"}`. Example 74 shows both TM and TD using
`"version": {"model": "1.0.0"}`.

Placing the Version class in `tm:` namespace implies it is TM-specific, but it
is not — it is shared vocabulary. The published JSON-LD context maps
`"VersionInfo"` to `td:VersionInfo`, not `tm:Version`. The context is correct
about namespace ownership; the TM ontology is wrong.

Having `td → tm` dependency for a shared class would invert the module
hierarchy (TD is foundation, TM builds on top).

### Finding: tm:ref rdfs:seeAlso schema:contactPoint

The upstream tm.ttl declares:

```turtle
# upstream tm.ttl
tm:ref ...
    rdfs:seeAlso schema:contactPoint ;
    ...
```

`schema:contactPoint` has no semantic relationship to `tm:ref` (a JSON Pointer
reference mechanism). This is a copy-paste error from `td:supportContact`
which legitimately references `schema:contactPoint`.

### Finding: external annotation property boilerplate

The upstream tm.ttl includes declarations for 10 external annotation properties
(`dcterms:title`, `dcterms:description`, `rdfs:label`, `vann:preferredNamespacePrefix`,
etc.). No other WoT module ontology does this. These terms are defined by their
respective vocabularies and do not need re-declaration.

### Toolchain decision

The TM module (`tm.ttl`) in this toolchain contains only TM-specific terms:

| Term | Type | Purpose |
|------|------|---------|
| `tm:ThingModel` | Class | The Thing Model class |
| `tm:optional` | DatatypeProperty | JSON Pointer refs to optional interaction affordances |
| `tm:required` | DatatypeProperty | JSON Pointer refs to mandatory interaction affordances |
| `tm:ref` | DatatypeProperty | Reference to external/local definition (URI + JSON Pointer) |
| `tm:versionInfo` | AnnotationProperty | Ontology-level version metadata (like `owl:versionInfo`) |

**Removed from TM, placed in TD:**
- `tm:Version` → `td:VersionInfo` (class, shared by both TD and TM)
- `tm:hasVersion` → `td:hasVersionInfo` (ObjectProperty, links Thing → VersionInfo)
- `tm:instance` → `td:instance` (DatatypeProperty, already in upstream td.ttl)
- `tm:model` → `td:model` (DatatypeProperty, already in upstream td.ttl)

**Removed entirely (not generated):**
- td: property re-declarations (redundant, one uses harmful hard `rdfs:domain`)
- External annotation property boilerplate (no other WoT module does this)
- `tm:ref rdfs:seeAlso schema:contactPoint` (copy-paste error)

## TD `uriVariables` — phantom IRI in security scoped context

**Status:** Upstream context inconsistency.

### Finding

The top-level TD context correctly maps `"uriVariables"` to the ontology term
`td:hasUriTemplateSchema`:

```json
// td-context-1.1.jsonld (top-level)
"uriVariables": {
    "@id": "td:hasUriTemplateSchema",
    "@type": "@id",
    "@container": "@index",
    "@index": "name"
}
```

However, inside the scoped contexts for `securityDefinitions` and `security`,
the same JSON key maps to a different, non-existent IRI:

```json
// td-context-1.1.jsonld (security / securityDefinitions scope)
"uriVariables": "td:uriVariables"
```

`td:uriVariables` is never declared in `td.ttl`. The ontology only defines
`td:hasUriTemplateSchema`. This means the same JSON key `"uriVariables"`
expands to two different RDF predicates depending on its location in the
document — one real (`td:hasUriTemplateSchema`), one phantom
(`td:uriVariables`).

### Evidence

- [TD ontology: `hasUriTemplateSchema`](https://github.com/w3c/wot-thing-description/blob/main/ontology/td.ttl) — only this term exists
- [TD 1.1 context: top-level `uriVariables`](https://github.com/w3c/wot-thing-description/blob/main/context/td-context-1.1.jsonld) — maps to `td:hasUriTemplateSchema`
- [TD 1.1 context: security-scoped `uriVariables`](https://github.com/w3c/wot-thing-description/blob/main/context/td-context-1.1.jsonld) — maps to `td:uriVariables`

### Effect on this toolchain

The toolchain uses `td:hasUriTemplateSchema` consistently (matching the
ontology). If security-scoped `uriVariables` are ever needed, they should
use the same predicate IRI. The phantom `td:uriVariables` should not be
generated.

## TD `model` — missing `@type` annotation in context

**Status:** Upstream context inconsistency (asymmetric with `instance`).

### Finding

The TD context annotates `"instance"` with an explicit datatype but omits it
for `"model"`, despite both being string-valued DatatypeProperties in the
ontology:

```json
// td-context-1.1.jsonld
"instance": { "@id": "td:instance", "@type": "xsd:string" },
"model":    { "@id": "td:model" }
```

Without `@type: xsd:string`, `model` values expand to plain literals (no
datatype IRI) instead of `xsd:string`-typed literals. This is asymmetric —
two sibling properties of the same class, both string-valued, treated
differently in RDF expansion.

### Evidence

- [TD 1.1 context: `instance` vs `model`](https://github.com/w3c/wot-thing-description/blob/main/context/td-context-1.1.jsonld)
- [TD ontology: both are DatatypeProperties](https://github.com/w3c/wot-thing-description/blob/main/ontology/td.ttl) — neither has explicit `schema:rangeIncludes` but both are clearly string-valued

### Effect on this toolchain

The toolchain should match upstream context behavior for compatibility. Both
properties can be declared as string-ranged in the LinkML schema (and the OWL
output includes `schema:rangeIncludes schema:Text` for both), but the
generated context should replicate the upstream asymmetry until the Working
Group decides to fix it.

## TD `hasSecurityConfiguration` — self-contradictory type mapping across scopes

**Status:** Upstream context self-contradiction (extends prior finding).

### Finding

The context maps `td:hasSecurityConfiguration` with two different `@type`
values depending on scope:

```json
// td-context-1.1.jsonld — TOP-LEVEL (Thing.security)
"security": {
    "@id": "td:hasSecurityConfiguration",
    "@type": "xsd:string"
}

// td-context-1.1.jsonld — FORMS/LINKS SCOPE (Form.security)
"security": {
    "@id": "td:hasSecurityConfiguration",
    "@type": "@id"
}
```

The top-level mapping says values are strings. The forms-scoped mapping says
values are IRI references. The ontology declares an ObjectProperty (= IRI
reference semantics). All three disagree with each other:

- Ontology: ObjectProperty → values should be `@id`
- Forms scope: `@type: @id` → agrees with ontology
- Top-level: `@type: xsd:string` → contradicts both

This is not merely an ontology-vs-context mismatch — the context contradicts
itself. The same predicate gets different expansion behavior at different
nesting depths.

### Evidence

- [TD ontology: `hasSecurityConfiguration` as ObjectProperty](https://github.com/w3c/wot-thing-description/blob/main/ontology/td.ttl)
- [TD 1.1 context: top-level `security` with `xsd:string`](https://github.com/w3c/wot-thing-description/blob/main/context/td-context-1.1.jsonld)
- [TD 1.1 context: forms-scoped `security` with `@id`](https://github.com/w3c/wot-thing-description/blob/main/context/td-context-1.1.jsonld)

### Effect on this toolchain

The toolchain must replicate the upstream context behavior for TD compatibility
(top-level `xsd:string`, forms-scoped `@id`). The OWL generator correctly
emits ObjectProperty. This is a known upstream wart that the Working Group
should resolve, but the toolchain cannot unilaterally change the context
mapping.

## TD ontology minor upstream issues

**Status:** Trivial upstream bugs; no toolchain action needed.

### `rdfs:isDefinedBy` IRI inconsistency

Two properties use bare `:` (expanding to `https://www.w3.org/2019/wot/td#`)
instead of `<https://www.w3.org/2019/wot/td>` (without trailing `#`):

```turtle
# upstream td.ttl
:hasNotificationResponseSchema ...
    rdfs:isDefinedBy : .     # ← expands to td# (with #)

:isSynchronous ...
    rdfs:isDefinedBy : .     # ← same
```

All other terms use `rdfs:isDefinedBy <https://www.w3.org/2019/wot/td>`.
The trailing `#` makes these technically different IRIs.

### OperationType comment copy-paste errors

Four OperationType instances have incorrect `rdfs:comment` values copied from
`readProperty`:

| Instance | Comment says | Should say |
|----------|-------------|------------|
| `td:invokeAction` | "read a property value" | invoke an action |
| `td:subscribeEvent` | "read a property value" | subscribe to event |
| `td:unsubscribeEvent` | "read a property value" | unsubscribe from event |
| `td:writeAllProperties` | "read a property value" | write all property values |

These are documentation-only bugs with no semantic impact.

## Toolchain coverage follow-up

The following are LinkML or generator coverage gaps found during the ontology
audit. They are not upstream inconsistencies.

- `jsonschema:anyOf` exists in the upstream JSON Schema ontology but is not
  part of the TD 1.1 spec vocabulary tables, nor does it appear in any TD 1.1
  spec examples. Confirmed via discussion with Ege Korkan that this term can
  be removed from the toolchain scope. It is an upstream ontology artifact
  that was never adopted into the TD specification.
- `jsonschema:propertyName` exists in both the upstream JSON Schema ontology
  (as a DatatypeProperty with `schema:domainIncludes :DataSchema` and
  `rdfs:range xsd:string`) and the JSON-LD context (`"propertyName":
  {"@id": "jsonschema:propertyName"}`). It serves as the `@index` predicate
  for the ObjectSchema `properties` container — distinct from `td:name` which
  indexes Thing-level affordance containers (`properties`, `actions`,
  `events`). Added as a base slot with `slot_uri: jsonschema:propertyName`.
- `td:OperationType`, `td:hasInstanceConfiguration`, and
  `td:hasInteractionAffordance` are established TD 1.1 ontology terms. The
  LinkML model needs explicit ontology mappings for them. In particular,
  `OperationType` must retain its TD class and named operation values, and
  `hasInteractionAffordance` must remain the parent of the property, action,
  and event affordance predicates.

These items should be addressed after the scoped JSON-LD context mapping is
covered by tests. They must not be omitted merely because an existing
generator does not currently emit them.

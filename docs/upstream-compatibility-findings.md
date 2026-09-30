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

The published TD 2.0 JSON-LD context scopes the security vocabulary beneath
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

The TD 1.1 JSON-LD context declares `schemaDefinitions` as
`td:schemaDefinitions`, with an `@id` value and an `@index` container. The TD
ontology does not declare `td:schemaDefinitions`, although it is a TD term
needed to expand and compact named data-schema maps.

The absence of an ontology declaration does not make the term optional or
TD 2.0-specific. It is present in TD 1.1 context processing and must remain
in the LinkML model.

### Evidence

- [TD 1.1 context: `schemaDefinitions`](https://github.com/w3c/wot-thing-description/blob/main/context/td-context-1.1.jsonld)
- [TD ontology](https://github.com/w3c/wot-thing-description/blob/main/ontology/td.ttl)

### Effect on this toolchain

The toolchain should generate `td:schemaDefinitions` from the LinkML source
and should not remove it to match the incomplete ontology. The JSON-LD
context generator must preserve the indexed-map mapping. The Working Group
may decide whether the upstream ontology should be completed with a matching
declaration.

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

## Toolchain coverage follow-up

The following are LinkML or generator coverage gaps found during the ontology
audit. They are not upstream inconsistencies.

- `jsonschema:anyOf` and `jsonschema:propertyName` occur in both the upstream
  JSON-LD context and JSON Schema ontology but are not yet fully represented
  in the LinkML source.
- `td:OperationType`, `td:hasInstanceConfiguration`, and
  `td:hasInteractionAffordance` are established TD 1.1 ontology terms. The
  LinkML model needs explicit ontology mappings for them. In particular,
  `OperationType` must retain its TD class and named operation values, and
  `hasInteractionAffordance` must remain the parent of the property, action,
  and event affordance predicates.

These items should be addressed after the scoped JSON-LD context mapping is
covered by tests. They must not be omitted merely because an existing
generator does not currently emit them.

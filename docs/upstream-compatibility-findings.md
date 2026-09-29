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

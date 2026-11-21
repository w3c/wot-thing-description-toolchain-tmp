# JSON-LD Type Coercion Rules

This document describes how the toolchain determines the `@type` coercion for
each term in the generated JSON-LD context.  Schema authors extending the TD
model must follow these rules so that new slots receive correct JSON-LD type
coercion without postprocessor changes.

## Background

In JSON-LD, a term's `@type` controls how values are interpreted:

| `@type` value  | Meaning                               | RDF result            |
|----------------|---------------------------------------|-----------------------|
| `@id`          | Value is an IRI reference             | IRI node (dereferenceable) |
| `@vocab`       | Value resolves against the active vocabulary | IRI from vocab base |
| `xsd:anyURI`   | Value is a URI-typed literal string   | `"http://..."^^xsd:anyURI` |
| *(omitted)*    | Value is a plain string               | `"value"^^xsd:string` |

The distinction between `@id` and `xsd:anyURI` is critical: `@id` produces an
RDF IRI node that JSON-LD processors can follow and dereference.  `xsd:anyURI`
produces a literal string that happens to contain a URI — processors treat it
as opaque text.

## Decision Rules

The postprocessor applies these rules in order.  The first matching rule wins.

### Rule 1: Type Designator → `{"@id": "@type"}`

**Schema marker:** `designates_type: true` on the slot definition.

When a slot's value determines the RDF type of the enclosing node (i.e., the
value selects which class the instance belongs to), the JSON-LD context must
map it to `@type`.

**Example:** The `scheme` slot in WoT Security:

```yaml
slots:
  scheme:
    description: Identification of the security mechanism being configured.
    required: true
    designates_type: true
    range: SecuritySchemeList
```

This produces the context entry `"scheme": {"@id": "@type"}`, which means
`"scheme": "nosec"` expands to `rdf:type wotsec:NoSecurityScheme` (resolved
via the enum value's `meaning`).

**LinkML limitation:** The native `designates_type` metaslot triggers a bug in
LinkML's JSON Schema generator when the slot range is an enum.  The pipeline
guards against this by temporarily clearing the flag before JSON Schema
generation (see `pipeline.py::_gen_jsonschema`).

### Rule 2: OWL ObjectProperty + URI Range → `@id`

**Schema marker:** `implements: [owl:ObjectProperty]` on the slot definition,
combined with `range: uri`.

When a URI-valued slot represents a dereferenceable resource (an RDF IRI node),
mark it as an `owl:ObjectProperty`.  The postprocessor replaces the default
`xsd:anyURI` with `@id`.

**Example:** The `authorization` endpoint in OAuth2:

```yaml
slots:
  authorization:
    slot_uri: wotsec:authorization
    domain: OAuth2SecurityScheme
    implements:
      - owl:ObjectProperty
    range: uri
```

This produces `"authorization": {"@type": "@id", "@id": "wotsec:authorization"}`.

**When NOT to use:** Slots whose URI values are opaque strings (not meant to be
dereferenced as RDF resources) should NOT carry `owl:ObjectProperty`.  Examples:

- `href` — URI template, may contain template variables (`{id}`), not always a
  valid IRI.  Correctly uses `xsd:anyURI`.
- `support` — Contact URI (`mailto:`, `tel:`).  Not an RDF resource.  Correctly
  uses `xsd:anyURI`.

### Rule 3: OWL DatatypeProperty → Strip `@id`

**Schema marker:** `implements: [owl:DatatypeProperty]` on the slot definition.

LinkML sometimes adds `@type: @id` to slots that should produce literals.  When
a slot is explicitly declared as an `owl:DatatypeProperty`, the postprocessor
strips `@type: @id`, leaving the value as a plain literal.

### Rule 4: `@vocab` Type Coercion

**Schema marker:** `implements: [owl:ObjectProperty]` combined with an enum
range whose values have `meaning:` declarations.

When an enum-valued slot's values map to vocabulary terms (via `meaning:`), the
postprocessor applies `@type: @vocab` so that plain string values resolve
against the active JSON-LD vocabulary.

### Rule 5: Default — LinkML Native Behavior

Slots that do not match any of the above rules keep whatever type coercion
LinkML's context generator produces:

- `range: uri` → `xsd:anyURI`
- `range: string` → no `@type` (plain string)
- Object-valued slots → no `@type` needed (value is a nested node)

## How to Extend the Schema

When adding a new URI-valued slot, ask:

1. **Is the value a dereferenceable RDF resource?**
   - Yes → add `implements: [owl:ObjectProperty]` and `range: uri`.
     The postprocessor will emit `@type: @id`.
   - No (URI template, contact URI, opaque identifier) → use `range: uri`
     without `implements`.  The default `xsd:anyURI` is correct.

2. **Does the value determine the RDF type of the enclosing node?**
   - Yes → add `designates_type: true`.  The postprocessor will emit
     `{"@id": "@type"}`.

3. **Is the value a vocabulary term from an enum?**
   - Yes, and the enum values have `meaning:` → the postprocessor handles
     `@vocab` coercion automatically from the enum's `meaning` declarations.

## Relationship to OWL

These rules are grounded in OWL semantics.  JSON-LD is also RDF, so OWL
property classifications are the correct discriminator:

- **`owl:ObjectProperty`** → the value is an IRI (a resource).  JSON-LD
  should use `@id` to produce an IRI node.
- **`owl:DatatypeProperty`** → the value is a literal.  JSON-LD should use
  a datatype IRI (e.g., `xsd:anyURI`) or no `@type` for plain strings.
- **`owl:AnnotationProperty`** → treated as a literal for JSON-LD purposes.

This alignment means the same `implements:` declaration serves both the OWL
ontology generator and the JSON-LD context postprocessor — a single source of
truth in the schema.

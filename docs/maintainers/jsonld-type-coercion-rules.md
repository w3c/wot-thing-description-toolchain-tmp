# JSON-LD Type Coercion Rules

This document describes how the toolchain determines the `@type` coercion for
each term in the generated JSON-LD context.  Schema authors extending the TD
model must follow these rules so that new slots receive correct JSON-LD type
coercion without changes to the context passes registered in
`src/wot_toolchain/artifacts/jsonld_context/passes.py`.

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

The context passes apply these rules.

### Rule 1: Type Designator → `{"@id": "@type"}`

**Schema marker:** `designates_type: true` on the slot definition.

When a slot's value determines the RDF type of the enclosing node (i.e., the
value selects which class the instance belongs to), the JSON-LD context must
map it to `@type`.

No slot in the current schemas uses `designates_type`.

**LinkML limitation:** `WotJsonSchemaGenerator.before_generate_class_slot` in
`src/wot_toolchain/artifacts/jsonschema/generator.py` hands the upstream JSON
Schema generator a copy of the slot with the flag cleared.

### Rule 2: A URI Value Is a Literal, a Name Reference Is a Node

A term whose JSON value is a URI string falls into one of two cases.  The case
is decided by what the value names, not by the JSON type.

**Case A — the URI names no node of the Thing Description.**  The value is an
`xsd:anyURI` literal.

**Schema marker:** `range: uri`, no `implements: [owl:ObjectProperty]`.

```yaml
slots:
  authorization:
    slot_uri: wotsec:authorization
    range: uri
```

This produces `"authorization": {"@type": "xsd:anyURI", "@id": "wotsec:authorization"}`
in the `wotsec` scoped context, an `owl:DatatypeProperty` with
`rdfs:range xsd:anyURI` in the ontology, and a property shape with
`sh:datatype xsd:anyURI` and `sh:nodeKind sh:Literal` in SHACL.  The slots
modelled this way are `href`, `base`, `support`, `profile`, `anchor`, `proxy`,
`authorization`, `token` and `refresh`.  `tests/test_uri_valued_terms.py` pins
the last five across the four artifacts.

**Case B — the value is the name of a node the Thing Description defines.**
The value is an IRI node, and the property is an object property that ranges
over the class of the defined node.

**Schema marker:** `range: <Class>` without `inlined`, where the class has a
key slot, and `jsonld_container: "@id"` on the definitions map that holds the
nodes.

```yaml
slots:
  security:
    slot_uri: td:hasSecurityConfiguration
    range: SecurityScheme
```

This produces `"security": {"@type": "@id", "@id": "hasSecurityConfiguration"}`.
Because `securityDefinitions` carries `@container: @id`, each map key becomes
the IRI of the scheme node, resolved against the document base, and a
`security` name resolves to the same IRI.  The slots modelled this way are
`security` (range `SecurityScheme`, defined by `securityDefinitions`) and
`schema` of `AdditionalExpectedResponse` (range `DataSchema`, defined by
`schemaDefinitions`).  `tests/test_definition_references.py` pins both across
the four artifacts.  JSON Schema keeps the values as strings in both cases.

**Not in use:** the context pass `fix_object_property_id_coercion` replaces `xsd:anyURI` with `@id` for a
`range: uri` slot that carries `implements: [owl:ObjectProperty]`.  No slot in
the schema uses this combination.  It yields an object property without a
range, which is the modelling this rule replaces.  The only URI-typed slot
with `implements: [owl:ObjectProperty]` is `unit` (`range: uriorcurie`), which
is coerced with `@vocab`.

### Rule 3: OWL DatatypeProperty → Strip `@id`

**Schema marker:** `implements: [owl:DatatypeProperty]` on the slot definition.

LinkML sometimes adds `@type: @id` to slots that should produce literals.  When
a slot is explicitly declared as an `owl:DatatypeProperty`, the context pass
`strip_datatype_property_id_coercion` strips `@type: @id`, leaving the value as a plain literal.

### Rule 4: `@vocab` Type Coercion

**Schema marker:** an enum range whose values have `meaning:` declarations, on
a slot without `designates_type`.

When an enum-valued slot's values map to vocabulary terms (via `meaning:`), the
context pass `fix_enum_vocab_type_coercion` applies `@type: @vocab` so that plain string values resolve
against the active JSON-LD vocabulary.

### Rule 5: Default — LinkML Native Behavior

Slots that do not match any of the above rules keep whatever type coercion
LinkML's context generator produces:

- `range: uri` → `xsd:anyURI`
- `range: string` → no `@type` (plain string)
- Object-valued slots → no `@type` needed (value is a nested node)

## How to Extend the Schema

When adding a new URI-valued slot, ask:

1. **What does the URI value name?**
   - A node the Thing Description itself defines under a name (as `security`
     names an entry of `securityDefinitions`) → use `range: <Class>` without
     `inlined`, and `jsonld_container: "@id"` on the definitions map.  The
     context emits `@type: @id`.
   - Anything else (endpoint, URI template, contact URI, opaque identifier) →
     use `range: uri` without `implements: [owl:ObjectProperty]`.  The default `xsd:anyURI` is
     correct.

2. **Does the value determine the RDF type of the enclosing node?**
   - Yes → add `designates_type: true`.  The context passes emit
     `{"@id": "@type"}`.

3. **Is the value a vocabulary term from an enum?**
   - Yes, and the enum values have `meaning:` → the context passes handle
     `@vocab` coercion automatically from the enum's `meaning` declarations.

## Relationship to OWL

These rules are grounded in OWL semantics.  JSON-LD is also RDF, so OWL
property classifications are the correct discriminator:

- **`owl:ObjectProperty`** → the value is a node.  JSON-LD should use `@id`
  to produce an IRI node, and the property ranges over a class.
- **`owl:DatatypeProperty`** → the value is a literal.  JSON-LD should use
  a datatype IRI (e.g., `xsd:anyURI`) or no `@type` for plain strings.
- **`owl:AnnotationProperty`** → treated as a literal for JSON-LD purposes.

This alignment means the same `implements:` declaration serves both the OWL
ontology generator and the JSON-LD context passes — a single source of
truth in the schema.

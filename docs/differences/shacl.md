# Differences between the generated and the published SHACL shapes

The generated JSON Schema is release quality; the generated SHACL shapes are experimental.
This note compares the generated shapes `resources/gens/shacl/shapes.shacl.ttl` with the published W3C TD validation shapes `resources/upstream/validation/td-validation.ttl`, and lists defects of the published shapes.

The status words Undecided and Published defect are defined in the [README](index.md) of this directory.

## Method

Files:

- generated shapes `resources/gens/shacl/shapes.shacl.ttl`, generated context `resources/gens/jsonldcontext/context.jsonld`
- published shapes `resources/upstream/validation/td-validation.ttl`, published context `resources/upstream/context/td-context-1.1.jsonld`

Procedure:

1. Parse both shape graphs with rdflib 7.6.0. For every node shape, collect the targets, the node-level constraints and the property shapes grouped by path. Pair node shapes by target class and compare every constraint on every path. Each structural difference is covered by an entry below.
2. Convert each TD to N-Quads with jsonld.js 9.0.0 (processing mode `json-ld-1.1`, including property-valued `@index`), with base `http://example.org/td`. Each side gets its own context: data for the published shapes uses `https://www.w3.org/2022/wot/td/v1.1`, resolved to the published context; data for the generated shapes uses `https://www.w3.org/ns/wot-next/td`, resolved to the generated context. The document loader serves only these two files and raises an error for any other URL.
3. Validate each data graph against the shapes of its side with pyshacl 0.40.2, with `inference="none"` and `advanced=True`, and compare the result types (constraint components) and paths.

Two base TDs were used. B is the following, with `CTX` replaced by the context URL of the side:

```json
{"@context": "CTX", "title": "T",
 "securityDefinitions": {"nosec_sc": {"scheme": "nosec"}}, "security": "nosec_sc",
 "properties": {"p": {"type": "string", "forms": [{"href": "http://e.org/p"}]}}}
```

F is B with `"@type": "td:Thing"` on the Thing, `"@type": "wotsec:NoSecurityScheme"` on the scheme, `"@type": ["td:PropertyAffordance", "jsonschema:StringSchema"]` on `p` and `"@type": "hctl:Form"` on the form.
F conforms to the published shapes.
Against the generated shapes F fails Class on `td:definesSecurityScheme` and `td:hasSecurityConfiguration`; Closed on `td:hasForm`; Datatype, In and NodeKind on `wotsec:scheme`; and NodeKind on `td:hasPropertyAffordance`.
Each probe changes one member of F, and its Effect lists the violations the change adds or removes on each side.

To repeat an entry, build the TD of its Effect paragraph, convert it with the loader above and validate it with the same pyshacl options.

## Part 1: Where the generated shapes differ

Entries are ordered by constraint kind: targets, node kind and class, datatype, cardinality, closedness, then other constraint kinds.

### Untyped TDs reach no generated target

Published. The published context maps `type` and `scheme` to `rdf:type`, so data schemas and security schemes are focus nodes of their class targets.

Generated. Targets are the same classes, but the generated context maps `type` to `jsonschema:type` and `scheme` to `wotsec:scheme`. The data schema shapes constrain `jsonschema:type` with `sh:in` of the data schema classes, and `SecuritySchemeShape` constrains `wotsec:scheme` with `sh:in` of the scheme classes.

Effect. B conforms on both sides. On the published side the string schema and the scheme nodes are focus nodes; on the generated side B has no `rdf:type` triple and no focus node.
With only `"@type": "td:Thing"` added, the published side still conforms, and the generated side fails Class on `td:definesSecurityScheme`, `td:hasPropertyAffordance` and `td:hasSecurityConfiguration`, and NodeKind on `td:hasPropertyAffordance`.

Status. Undecided.

### Extra shape for `linkml:Any`

Published. No such shape.

Generated. `linkml:AnyShape` with `sh:targetClass linkml:Any`.

Effect. No TD produces `rdf:type linkml:Any`, so the shape has no focus node in any probe.

Status. Undecided.

### Affordances without a type

Published. `ThingShape` has a property shape with `sh:alternativePath (td:hasPropertyAffordance td:hasActionAffordance td:hasEventAffordance)` and `sh:node` of the interaction affordance shape, which requires a form.

Generated. No equivalent; affordance shapes are reached only through class targets.

Effect. B with `"@type": "td:Thing"` and no `forms` on `p` fails MinCount on `td:hasForm` and Node on the alternative path on the published side. The generated side reports Class on `td:definesSecurityScheme`, `td:hasPropertyAffordance` and `td:hasSecurityConfiguration` and NodeKind on `td:hasPropertyAffordance` only, and no missing form.

Status. Undecided.

### Nested objects use class and node kind

Published. Nested objects are checked with `sh:node` on the shape of the object.

Generated. Nested objects are checked with `sh:class` plus `sh:nodeKind sh:IRI` for `td:definesSecurityScheme`, the three affordance links, `td:hasUriTemplateSchema`, `td:schemaDefinitions`, the input, output, subscription, notification, notification response and cancellation schemas, `jsonschema:items`, `jsonschema:properties`, `jsonschema:oneOf` and `jsonschema:allOf`; and with `sh:class` plus `sh:nodeKind sh:BlankNodeOrIRI` for `td:hasForm`, `td:hasLink`, `td:versionInfo`, `hctl:returns` and `hctl:additionalReturns`.

Effect. In F, NodeKind fails on `td:hasPropertyAffordance`, because the affordance is a blank node. It does not fail on `td:definesSecurityScheme`: the generated context maps `securityDefinitions` and `schemaDefinitions` with `@container @id`, so their members are IRIs (`<http://example.org/nosec_sc>` in F). Typed actions and events add NodeKind on `td:hasActionAffordance` and `td:hasEventAffordance`; untyped ones add Class as well. Typed `items` and `properties` schemas add Class, NodeKind and Closed.
Untyped forms, `version` and `response` add Class on `td:hasForm`, `td:versionInfo` and `hctl:returns`; typed ones add nothing.
Class on `td:definesSecurityScheme` and on `td:hasSecurityConfiguration` stays in F, where the scheme is typed `wotsec:NoSecurityScheme`; both disappear only when the scheme is typed `wotsec:SecurityScheme`. Both also stay with `inference="rdfs"`.
The published side reports none of these.

Cause. A node typed with a subclass is not an `sh:class` instance of the superclass unless `rdf:type` / `rdfs:subClassOf*` reaches it in the data graph. Neither shape graph contains `rdfs:subClassOf` triples, and the data graph has none either.

Status. Undecided.

### Language maps

Published. `td:titleInLanguage` and `td:descriptionInLanguage` use `sh:node` on a multi-language shape with `sh:uniqueLang true`.

Generated. They use `sh:class td:MultiLanguage` plus `sh:nodeKind sh:IRI`, and no `sh:uniqueLang`. `td:MultiLanguageShape` constrains `td:language_tag` with `sh:pattern` and `td:language_value`, paths that no context term produces.

Effect. F with `"titles": {"en": "T", "de": "D"}` adds Class and NodeKind on `td:titleInLanguage` for the literals `"T"@en` and `"D"@de` on the generated side, and nothing on the published side. `descriptions` adds the same on `td:descriptionInLanguage` on the generated side, and nothing on the published side.

Status. Undecided.

### Security and schema references

Published. `td:hasSecurityConfiguration` has `sh:datatype xsd:string`, with `sh:minCount 1` on the Thing and `sh:nodeKind sh:Literal` on forms. `hctl:hasAdditionalOutputSchema` has `sh:datatype xsd:string`, `sh:nodeKind sh:Literal` and `sh:maxCount 1`.

Generated. `td:hasSecurityConfiguration` has `sh:class wotsec:SecurityScheme`, `sh:nodeKind sh:IRI` and `sh:maxCount 1`, with `sh:minCount 1` on the Thing. `hctl:hasAdditionalOutputSchema` has `sh:class jsonschema:DataSchema`, `sh:nodeKind sh:IRI` and `sh:maxCount 1`.

Effect. F fails Class on `td:hasSecurityConfiguration` on the generated side, because the scheme is typed `wotsec:NoSecurityScheme`; typed `wotsec:SecurityScheme`, it passes. A name without a definition, such as `"security": "zzz"`, fails Class as well. The published side passes F.
F with `"schemaDefinitions": {"s1": {"type": "string"}}` and a form with `"additionalResponses": [{"@type": "hctl:AdditionalExpectedResponse", "schema": "s1"}]` adds Class on `hctl:hasAdditionalOutputSchema` and on `td:schemaDefinitions` on the generated side. With `s1` typed `jsonschema:StringSchema` it adds Closed on `td:type` as well; with `s1` typed `jsonschema:DataSchema` it adds only Closed on `td:type`. On the published side the same probe adds Datatype and NodeKind on `hctl:hasAdditionalOutputSchema` and Node on `hctl:additionalReturns`, `td:hasForm` and the affordance alternative path.

Cause. The generated context maps `security` and `schema` with `@type @id`, and `securityDefinitions` and `schemaDefinitions` with `@container @id`, so a name and its definition are the same IRI (`<http://example.org/nosec_sc>` in F). The published context maps top-level `security` to an `xsd:string` literal and `schema` with `@type @id`. For `sh:class` on a node typed with a subclass, see Nested objects use class and node kind.

Status. Undecided.

### URI-valued members

Published. `hctl:hasTarget`, `td:baseURI`, `td:supportContact`, `td:followsProfile` and `hctl:hasAnchor` use `sh:datatype xsd:anyURI`; `hctl:hasTarget` also has `sh:nodeKind sh:Literal`. `wotsec:proxy`, `wotsec:authorization`, `wotsec:token` and `wotsec:refresh` combine `xsd:anyURI` with `sh:nodeKind sh:IRI` (see Part 2).

Generated. All of these use `sh:datatype xsd:anyURI` with `sh:nodeKind sh:Literal`.

Effect. F raises no violation on `hctl:hasTarget` on either side. `base`, `support`, `profile`, `anchor`, `proxy`, `authorization`, `token` and `refresh` add nothing on the generated side. For the published-side failures of `base`, `profile`, `anchor`, `proxy`, `authorization`, `token` and `refresh`, see Part 2.

Cause. The generated context produces `href`, `base`, `support`, `profile`, `anchor`, `proxy`, `authorization`, `token` and `refresh` as `xsd:anyURI` literals.

Status. Undecided.

### Security scheme value

Published. No shape constrains `scheme`; it becomes `rdf:type`. `SecuritySchemeShape` requires exactly one `rdf:type`.

Generated. `SecuritySchemeShape` puts `sh:in` of the scheme class IRIs on `wotsec:scheme`. Each subclass shape puts `sh:in` of one string (`"nosec"`, `"basic"` and so on), `sh:datatype xsd:string`, `sh:nodeKind sh:Literal` and `sh:minCount 1`, `sh:maxCount 1` on it.

Effect. F fails Datatype, In and NodeKind on `wotsec:scheme` on the generated side; the same three appear for every typed scheme probed (basic, digest, bearer, oauth2, apikey, combo). Removing the type from the scheme, or typing it `wotsec:SecurityScheme`, removes them.

Cause. The generated context produces `wotsec:scheme wotsec:NoSecurityScheme`, an IRI, which matches the parent shape and fails every subclass shape.

Status. Undecided.

### Title and description datatype

Published. `td:title` and `td:description` on affordances, data schemas and security schemes have `sh:datatype rdf:langString`. On the Thing, both sides use the same `sh:or` for `td:title`.

Generated. They have `sh:nodeKind sh:Literal` and `sh:maxCount 1`, and no datatype.

Effect. A `title` on `p`, or a `description` on the Thing, adds nothing on either side. A description on a scheme fails Datatype on the published side (see Part 2).
With the context `["CTX", {"@language": "en"}]`, the published side adds nothing; the generated side adds Datatype on `td:name` (`"p"@en`), which requires `xsd:string`.

Status. Undecided.

### Integer and number datatypes

Published. `minItems`, `maxItems`, `minLength` and `maxLength` use `xsd:unsignedInt`. `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum` and `multipleOf` on number schemas use `xsd:double`; integer schemas use `xsd:integer`.

Generated. Length and item counts use `xsd:nonNegativeInteger`. Number schemas use `xsd:decimal`, integer schemas `xsd:integer`, and `multipleOf` adds `sh:minInclusive 0`.

Effect. On the generated side, every probe here adds Closed, because the affordance shape does not allow the data schema term (see Closed shapes). Beyond that, `minLength 1`, `maxItems 3`, number `minimum 1` and `exclusiveMinimum` add nothing on the generated side. Integer `minimum 1` adds Datatype on the generated side for `"1"^^xsd:decimal` and nothing on the published side. Integer `multipleOf -1` adds Datatype and MinInclusive on the generated side and nothing on the published side.
Number `minimum 1.5` passes on both sides. For the published-side failures of `minLength`, `maxItems` and number `minimum 1`, see Part 2.

Cause. The generated context types these numbers `xsd:decimal`, also on integer schemas.

Status. Undecided.

### Literal node kind

Published. Most string members already have `sh:nodeKind sh:Literal`. The boolean members (`hctl:isSuccess`, `jsonschema:readOnly`, `jsonschema:writeOnly`, `td:isIdempotent`, `td:isObservable`, `td:isSafe`, `td:isSynchronous`), the dates `dct:created` and `dct:modified`, and the strings `hctl:hasHreflang`, `hctl:hasRelationType` and `hctl:hasSizes` have a datatype and no node kind.

Generated. All of these have `sh:nodeKind sh:Literal`.

Effect. `"readOnly": true` and `"observable": true` produce literals and add no NodeKind on either side.

Status. Undecided.

### Single-valued members

Published. `hctl:hasOperationType`, `td:hasSecurityConfiguration` on forms and on the Thing, `wotsec:scopes`, `hctl:hasHreflang`, `td:followsProfile` and `jsonschema:items` have no `sh:maxCount`.

Generated. They have `sh:maxCount 1`; `wotsec:scopes` is an `sh:or` of two identical string shapes.

Effect. Each of the following adds MaxCount on the generated side only: `"op": ["readproperty", "writeproperty"]`, form `"scopes": ["a", "b"]`, form `"security": ["a", "b"]`, Thing `"security": ["nosec_sc", "nosec_sc2"]`, a typed link with `"hreflang": ["en", "de"]`, two `profile` values, and an array schema with `"items": [{"type": "string"}, {"type": "number"}]`. The two `security` probes also add Class on `td:hasSecurityConfiguration` for each name without a definition.

Status. Undecided.

### Closed shapes

Published. All shapes are `sh:closed false`.

Generated. All shapes except `td:InteractionAffordanceShape` are `sh:closed true` with `sh:ignoredProperties (rdf:type)`. `jsonschema:DataSchemaShape` and `wotsec:SecuritySchemeShape` also ignore the properties of their subclasses.

Effect. An extension member such as `"ex:foo": "x"` on the Thing or on a form adds Closed on the generated side.
In F the node typed both `td:PropertyAffordance` and `jsonschema:StringSchema` fails Closed on `td:hasForm`. `observable`, `contentMediaType`, `contentEncoding` and `minLength` on that node add Closed on it too. Typed only `td:PropertyAffordance`, the node loses the `td:hasForm` violation, but `minLength 1` still adds Closed on `jsonschema:minLength`.
The published side reports no Closed violation.

Cause. `jsonschema:StringSchemaShape` has no property shape for `td:hasForm` or `td:isObservable`, and `td:PropertyAffordanceShape` has none for the string schema terms. A node that carries terms of both classes fails one closed shape or the other.

Status. Undecided.

### Security scheme key path

Published. The scheme key is not constrained.

Generated. `SecuritySchemeShape` declares `td:security_scheme_key` with `sh:datatype xsd:string` and `sh:maxCount 1` and no `sh:minCount`. No context term produces the path.

Effect. No probe produces `td:security_scheme_key`, and the path adds no violation on the generated side.

Cause. The generated context maps `securityDefinitions` with `@container @id`, so the key becomes the IRI of the scheme node (`<http://example.org/nosec_sc>` in F) and not a property value. The published context produces the key as `td:hasInstanceConfiguration`.

Status. Undecided.

### API key `in` path

Published. The API key shape constrains `wotsec:in`, which the context produces.

Generated. The API key shape constrains `wotsec:apikeyIn` with `sh:minCount 1`.

Effect. F with the scheme `{"@type": "wotsec:APIKeySecurityScheme", "scheme": "apikey", "in": "header"}` adds MinCount on `wotsec:apikeyIn` and Closed on `wotsec:in` on the generated side, and nothing on the published side.

Status. Undecided.

### Unit path

Published. Data schemas constrain `schema:unitCode`.

Generated. Data schemas constrain `qudt:unit` with `sh:nodeKind sh:IRI`.

Effect. `"unit": "ex:u"` on `p` adds nothing on either side, because the node typed `td:PropertyAffordance` and `jsonschema:StringSchema` is not a focus node of the published data schema shape. `"unitCode": "ex:u"` adds Closed on `jsonschema:unitCode` on the generated side. On array `items` `{"type": "string", "unit": "http://ex.org/u"}`, the generated side adds nothing for `unit`; for the published side, see Part 2.

Cause. The published context maps `unit` to `schema:unitCode` with `@type @vocab`, and the generated context maps it to `qudt:unit`; both produce an IRI.

Status. Undecided.

### Other generated-only paths

Published. No `td:name` or `td:id` constraint.

Generated. Affordance and data schema shapes constrain `td:name` (`xsd:string`, `sh:maxCount 1`); `ThingShape` constrains `td:id`.

Effect. `"id": "urn:x"` on the Thing adds nothing on either side. For `td:name`, see Title and description datatype.

Status. Undecided.

### String enumerations

Published. `contentEncoding`, `contentMediaType`, `alg`, `format` and `flow` are `xsd:string`. `in` of basic, digest and bearer is one of `header`, `query`, `body`, `cookie` and `auto`. `qop` and `op` have `sh:in`.

Generated. `contentEncoding` is one of `7bit`, `8bit`, `binary`, `quoted-printable`, `base16`, `base32` and `base64`; `contentMediaType` one of `image/png` and `audio/mpeg`; `alg` one of `ES256` and `ES512-256`; `format` one of `jwt`, `jws`, `cwt` and `jwe`; `flow` one of `code` and `client`. `in` of basic, digest and bearer also allows `uri`. These enumerations carry no datatype and no node kind. `qop` and `op` have the same lists as the published shapes.

Effect. `contentMediaType "text/plain"`, `contentEncoding "gzip"`, `alg "RS256"`, `format "jwk"` and `flow "implicit"` add In on the generated side only.
A basic scheme with `"in": "uri"` adds In on the published side only.
`"op": "foo"` and `"qop": "foo"` add In on both sides.

Status. Undecided.

### Icon sizes pattern

Published. `hctl:hasSizes` has no pattern.

Generated. `hctl:hasSizes` has `sh:pattern`.

Effect. A typed link with `"sizes": "big"` adds Pattern on the generated side and nothing on the published side.

Status. Undecided.

### Combo member count

Published. `wotsec:allOf` and `wotsec:oneOf` each have `sh:minCount 2`, `xsd:string` and `sh:Literal` (see Part 2).

Generated. Their property shapes have `sh:datatype xsd:string` and `sh:nodeKind sh:Literal` and no count. The count is stated on the node shape, as one `sh:or` per path of `sh:maxCount 0` and `sh:minCount 2`.

Effect. A typed combo scheme with `"allOf": ["a", "b"]` or `"oneOf": ["a", "b"]` adds nothing on the generated side and fails MinCount on the absent path on the published side. With `"allOf": ["a"]` it adds Or, with no result path, on the generated side and MinCount on both paths on the published side.

Cause. The generated shape requires two values on a path only when the path is present; the published shape requires two values on each path.

Status. Undecided.

### Default values

Published. Several boolean members and `alg`, `format`, `in` and `qop` carry `sh:defaultValue`.

Generated. No `sh:defaultValue`.

Effect. `sh:defaultValue` is not a validation constraint; F with `"readOnly": true` on `p` adds nothing on either side.

Status. Undecided.

## Part 2: Defects in the published shapes

The part lists defects of the published shapes and inconsistencies between the published shapes and the published context. Each entry is a case where data produced by the published context fails the published shapes, or where the shapes contradict TD 1.1. Generated paragraphs expand the same instance through the generated context and validate it against the generated shapes. Entries follow the constraint order of Part 1. All runs use the published context and no inference.

### Anchor is an IRI but the shape requires a literal

Published. `hctl:hasAnchor` has `sh:datatype xsd:anyURI` and `sh:node sh:IRI`. `sh:IRI` is a node kind, not a shape, so the `sh:node` constraint has no effect. The context maps `anchor` with `@type @id`.

Generated. The generated context maps `anchor` to an `xsd:anyURI` literal and the generated shape gives `hctl:hasAnchor` `sh:datatype xsd:anyURI` and `sh:nodeKind sh:Literal`, so the anchor passes. The typed link with the anchor adds no violation.

Effect. A typed link with `"anchor": "http://e.org/a"` fails Datatype on `hctl:hasAnchor` and Node on `td:hasLink`.

Cause. The value form is a context defect: the shape agrees with the TD 1.1 row td-vocab-anchor--Link, type `anyURI`, and with `resources/upstream/ontology/hctl.ttl`, where `hctl:hasAnchor` is an `owl:DatatypeProperty`, while the context maps `anchor` to an IRI. The ineffective `sh:node sh:IRI` is a shape defect.

Status. Published defect.

### URI members that no value satisfies

Published. The property shape for `wotsec:proxy` is

```turtle
sh:path wotsec:proxy ; sh:nodeKind sh:IRI ; sh:datatype xsd:anyURI ; sh:maxCount 1
```

and `wotsec:authorization`, `wotsec:token` and `wotsec:refresh` have the same combination. An IRI has no datatype and a literal is not an IRI, so no value conforms.

Generated. The generated context maps `proxy`, `authorization`, `token` and `refresh` to `xsd:anyURI` literals and the generated shapes give each `sh:datatype xsd:anyURI` and `sh:nodeKind sh:Literal`. A typed basic scheme with `proxy`, a typed bearer scheme with `authorization` and a typed OAuth2 scheme with `authorization`, `token` and `refresh` pass on these paths; each shows the same violations as F, raised on its own scheme. The same members given as IRIs (`{"@id": "http://e.org/x"}`) fail Datatype and NodeKind on their paths, so the shapes are applied.

Effect. With the Turtle data

```turtle
<t> a td:Thing ; td:definesSecurityScheme <s> .
<s> a wotsec:BasicSecurityScheme ; wotsec:proxy X .
```

`X = <http://e.org/x>` fails Datatype on `wotsec:proxy`, and `X = "http://e.org/x"^^xsd:anyURI` fails NodeKind on `wotsec:proxy`. From JSON, `"proxy": "http://e.org/x"` on a typed scheme and `"authorization": "http://e.org/a"` on a bearer scheme each fail Datatype, because the context produces IRIs.

Cause. The shape is unsatisfiable on its own. On value form, `resources/upstream/ontology/wotsec.ttl` declares `wotsec:proxy` an `owl:DatatypeProperty` with `schema:rangeIncludes xsd:anyURI`, so the context contradicts the ontology for `proxy`, and declares `wotsec:authorization`, `wotsec:token` and `wotsec:refresh` as `owl:ObjectProperty`, so the context agrees with the ontology for those and the shape's `sh:datatype xsd:anyURI` contradicts it.

Status. Published defect.

### Base and profile are plain literals

Published. `td:baseURI` and `td:followsProfile` have `sh:datatype xsd:anyURI`. The context defines `base` and `profile` without `@type`.

Generated. The generated context gives `base` and `profile` `xsd:anyURI` literals and the generated shapes give `td:baseURI` and `td:followsProfile` `sh:datatype xsd:anyURI` and `sh:nodeKind sh:Literal`. F with `base` and F with `profile` add no violation.

Effect. F with `"base": "http://e.org/"` fails Datatype on `td:baseURI`; F with `"profile": "http://e.org/prof"` fails Datatype on `td:followsProfile`.

Cause. For `profile`, `resources/upstream/ontology/td.ttl` gives `td:followsProfile` `schema:rangeIncludes xsd:anyURI`, so the context contradicts the ontology and the shape agrees with it. For `base`, the ontology gives `td:baseURI` `schema:rangeIncludes schema:URL` and the TD 1.1 row td-vocab-base--Thing gives type `anyURI` at the JSON level, so the sources do not decide between `xsd:anyURI` and a plain literal, and the context and the shape are only mutually inconsistent.

Status. Published defect.

### Form security is an IRI but the shape requires a string

Published. Form `td:hasSecurityConfiguration` has `sh:datatype xsd:string` and `sh:nodeKind sh:Literal`. The context maps `security` inside forms and links with `@type @id`, while top-level `security` is `xsd:string`.

Generated. The generated context maps form `security` with `@type @id` and the generated shape gives it `sh:class wotsec:SecurityScheme`, `sh:nodeKind sh:IRI` and `sh:maxCount 1`. Form `"security": "nosec_sc"` resolves to the scheme node `<http://example.org/nosec_sc>`; it adds Class on `td:hasSecurityConfiguration` in F, where the scheme is typed `wotsec:NoSecurityScheme`, and nothing when the scheme is typed `wotsec:SecurityScheme`. `"security": ["a", "b"]` adds Class on each undefined name and MaxCount on `td:hasSecurityConfiguration`, although the TD 1.1 row td-vocab-security--Form types it "string or Array of string".

Effect. Form `"security": ["a", "b"]` fails Datatype and NodeKind on each resolved IRI (`<http://example.org/a>`, `<http://example.org/b>`), Node on `td:hasForm` and Node on the affordance alternative path.

Cause. `resources/upstream/ontology/td.ttl` declares `td:hasSecurityConfiguration` an `owl:ObjectProperty`, so the shape contradicts the ontology and the context agrees with it. The TD 1.1 row td-vocab-security--Form, type "string or Array of string", is a JSON-level type and does not decide the RDF form.

Status. Published defect.

### Unit is an IRI but the shape requires a string

Published. `DataSchemaShape` gives `schema:unitCode` `sh:datatype xsd:string` and `sh:nodeKind sh:Literal`. The context maps `unit` with `@type @vocab`, so it becomes an IRI.

Generated. The generated context maps `unit` to `qudt:unit` with `@type @vocab` and the generated shape gives `qudt:unit` `sh:nodeKind sh:IRI`. On an array schema whose `items` is typed `jsonschema:StringSchema`, `"unit": "http://ex.org/u"` passes; the same item with the literal `{"@value": "x"}` fails NodeKind on `qudt:unit`, so the shape is applied.

Effect. An array schema with `"items": {"type": "string", "unit": "http://ex.org/u"}` fails Datatype and NodeKind on `schema:unitCode` and Node on `jsonschema:items`.

Cause. The TD 1.1 row td-vocab-unit--DataSchema gives type `string` and recommends that the value "points to a semantic definition", and `schema:unitCode` is not defined in any ontology in `resources/upstream/`. The sources do not decide, so the published context and the published shapes are only mutually inconsistent on the value form of `unit`.

Status. Published defect.

### Scheme description has no language tag

Published. `td:description` on security schemes has `sh:datatype rdf:langString`. The context sets `@language en` for `description` at top level and in data schema scopes, but not in the `securityDefinitions` scope.

Generated. The generated context gives the scheme `description` a plain literal and the generated shape gives `td:description` `sh:nodeKind sh:Literal` without a datatype. A scheme with `"description": "d"` passes.

Effect. A typed scheme with `"description": "d"` fails Datatype on `td:description` and Node on `td:definesSecurityScheme`. A Thing `description` passes.

Cause. The TD 1.1 rows td-vocab-description--SecurityScheme and td-vocab-description--Thing both give type `string`, and `resources/upstream/ontology/td.ttl` gives `td:description` `schema:rangeIncludes schema:Text`. The sources do not decide on a language tag. The shape follows the context's own treatment of `description` in the other scopes, so the published context and the published shapes are only mutually inconsistent.

Status. Published defect.

### Version `model` takes the default language

Published. `VersionInfoShape` gives `td:model` and `td:instance` `sh:datatype xsd:string` and `sh:nodeKind sh:Literal`. The context coerces `instance` to `xsd:string` but gives `model` no `@type`, so a default `@language` tags `model` only.

Generated. The generated context coerces neither, so both take the default language. An untyped `version` adds Class on `td:versionInfo`. Typed `td:VersionInfo` with the default language `de`, it adds Datatype on `td:instance` and `td:model`, besides the Datatype violation the default language raises on `td:name`; without a default language it adds nothing on these paths.

Effect. F with the default language `de` and `"version": {"instance": "1.0", "model": "M1"}` fails Datatype on `td:model` and Node on `td:versionInfo`. Without the default language, or with `instance` alone, it passes.

Cause. `resources/upstream/ontology/td.ttl` declares `td:model` and `td:instance` as `owl:DatatypeProperty` without a range, so it does not decide on a language tag, and the published context and the published shapes are only mutually inconsistent.

Status. Published defect.

### Integer values fail the count and number datatypes

Published. `minLength`, `maxLength`, `minItems` and `maxItems` require `xsd:unsignedInt`; number `minimum`, `maximum` and `multipleOf` require `xsd:double`. The context gives these terms no `@type`, so JSON-LD produces `xsd:integer` for integral JSON numbers.

Generated. The generated context coerces `minLength` and `maxItems` to `xsd:nonNegativeInteger` and `minimum` to `xsd:decimal`. The generated shapes give `jsonschema:minLength` and `jsonschema:maxItems` `sh:datatype xsd:nonNegativeInteger`, and `jsonschema:minimum` `xsd:decimal` on number schemas but `xsd:integer` on integer schemas. `"minLength": 1` on F, `"maxItems": 3` on an array schema, and `"minimum": 1` and `"minimum": 1.5` on a number schema add no Datatype violation. `"minimum": 1` on an integer schema adds Datatype on `jsonschema:minimum`, because the context makes it `xsd:decimal`. Each of these adds Closed on its own path on the property affordance node.

Effect. `"minLength": 1` and `"maxItems": 3` fail Datatype. On a number schema `"minimum": 1` fails Datatype, while `"minimum": 1.5` (`xsd:double`) passes.

Cause. The shape follows the TD 1.1 rows td-vocab-minLength--StringSchema and td-vocab-minimum--NumberSchema, types `unsignedInt` and `double`, but contradicts `resources/upstream/ontology/jsonschema.ttl`, which gives the count terms `rdfs:range xsd:nonNegativeInteger` and `minimum`, `maximum` and `multipleOf` `rdfs:range xsd:decimal`. The context gives no `@type`, so `xsd:integer` matches neither, and the published context and the published shapes are mutually inconsistent.

Status. Published defect.

### Typed schemes get two `rdf:type` values

Published. `SecuritySchemeShape` has `rdf:type` with `sh:minCount 1` and `sh:maxCount 1`. The context maps `scheme` to `@type`, so `scheme` and `@type` both produce `rdf:type`.

Generated. The generated context maps `scheme` to `wotsec:scheme`, so the same scheme has one `rdf:type` value and adds no violation on `rdf:type`. The generated shapes have no property shape on `rdf:type`.

Effect. A scheme with `"@type": "wotsec:SecurityScheme"` and `"scheme": "nosec"` has two `rdf:type` values and fails MaxCount on `rdf:type` and Node on `td:definesSecurityScheme`.

Cause. The TD 1.1 row td-vocab-at-type--SecurityScheme gives `@type` the type "string or Array of string" alongside the mandatory `scheme`, so the shape's `sh:maxCount 1` contradicts the Recommendation. The context is consistent with it.

Status. Published defect.

### Combo requires both `allOf` and `oneOf`

Published. `ComboSecuritySchemeShape` carries the comment `# FIXME should be exactly one of oneOf or allOf` and attaches both property shapes:

```turtle
sh:property _:oneOf ; sh:property _:allOf .
_:oneOf sh:path wotsec:oneOf ; sh:nodeKind sh:Literal ; sh:datatype xsd:string ; sh:minCount 2 .
```

`_:allOf` is the same for `wotsec:allOf`. TD 1.1 section ComboSecurityScheme, assertion td-security-combo-exclusive-oneof-or-allof, states: "Exactly one of either `oneOf` or `allOf` vocabulary terms MUST be included." The shape requires both.

Generated. The generated context maps the items to string literals, and the generated shape gives `wotsec:allOf` and `wotsec:oneOf` `sh:datatype xsd:string` and `sh:nodeKind sh:Literal`, with one `sh:or` per path of `sh:maxCount 0` and `sh:minCount 2` on the node shape. `"allOf": ["a", "b"]` and `"oneOf": ["a", "b"]` add no violation, and `"allOf": ["a"]` adds Or. A scheme with both paths, or with neither, adds no violation.

Effect. A typed combo scheme with `"allOf": ["a", "b"]` fails MinCount on `wotsec:oneOf`; with `"oneOf": ["a", "b"]` it fails MinCount on `wotsec:allOf`; with `"allOf": ["a"]` it fails MinCount on both. The items are string literals, so no Datatype or NodeKind violation appears.

Cause. The shape contradicts the TD 1.1 assertion td-security-combo-exclusive-oneof-or-allof. On value form, `resources/upstream/ontology/wotsec.ttl` declares `wotsec:allOf` and `wotsec:oneOf` as `owl:ObjectProperty`, while the context produces string literals and the shape requires them, so both contradict the ontology. The TD 1.1 rows td-vocab-allOf--ComboSecurityScheme and td-vocab-oneOf--ComboSecurityScheme, type "Array of string", are JSON-level types.

Status. Published defect.

### `schemaDefinitions` path is not in the ontology

Published. `ThingShape` constrains `td:schemaDefinitions` with `sh:node DataSchemaShape`, and the context maps `schemaDefinitions` to `td:schemaDefinitions` with `@container @index`. None of `td.ttl`, `hctl.ttl`, `wotsec.ttl`, `jsonschema.ttl` and `tm.ttl` in `resources/upstream/ontology/` has a triple with `td:schemaDefinitions`, while the TD 1.1 row td-vocab-schemaDefinitions--Thing defines the term as an optional Map of DataSchema.

Generated. The generated shapes give `td:schemaDefinitions` `sh:class jsonschema:DataSchema` and `sh:nodeKind sh:IRI`, and the generated TD ontology declares it an `owl:ObjectProperty` with domain `td:Thing` and range `jsonschema:DataSchema`. F with `"schemaDefinitions": {"s1": {"type": "string"}}` adds Class on `td:schemaDefinitions`; the member is the IRI `<http://example.org/s1>`, so NodeKind passes.

Effect. F with `"schemaDefinitions": {"s1": {"type": "string"}}` passes, also with the member typed `jsonschema:StringSchema`. A member with `"title": {"@value": "x"}` fails Datatype on `td:title` and Node on `td:schemaDefinitions`, so the shape is applied to a path the published ontology does not define.

Status. Published defect.

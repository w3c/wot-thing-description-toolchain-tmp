# Differences between the generated and the published JSON-LD context

This note compares the generated JSON-LD context `resources/gens/jsonldcontext/context.jsonld` with the published W3C TD 1.1 context `resources/upstream/context/td-context-1.1.jsonld`.
It lists every difference that changes how a TD is interpreted, and the defects of the published context that explain why the generated context departs from it.
To reproduce an entry, put either context in place of the TD 1.1 context URL in the fragment's `@context`, convert the fragment to RDF with a JSON-LD 1.1 processor whose document loader refuses remote loads, and compare the N-Quads.

The status words Undecided and Published defect are defined in the [README](README.md) of this directory.

## Method

The reference is the published context `resources/upstream/context/td-context-1.1.jsonld`; the generated context is `resources/gens/jsonldcontext/context.jsonld`.
Both contexts were processed into active contexts with pyld 3.3.0.
Starting at the top-level active context, every term definition that carries a scoped context was applied on top of the active context at its path, recursively, so that each scoped path (for example `/securityDefinitions` or `/forms/data`) has an effective active context.
At every path present in either context, the term definitions of the union of terms were compared on IRI mapping, type mapping, container mapping, language mapping, index mapping and presence of a scoped context, together with the default vocabulary and default language.
Each raw difference was then exercised by a TD fragment, and the TD fragments under `tests/data/*/*.jsonld` were converted to RDF under both contexts with jsonld.js 9.0.0, with the TD 1.0 context URL that some of them also list mapped to `resources/upstream/context/td-context.jsonld` in both runs; their triples were compared as multisets of predicate and object.
jsonld.js is used for all triples shown, because pyld does not emit the triple of a property-valued `@index`.
Relative IRIs are dropped when no base IRI is set; fragments that need one use the base `http://example.org/td`.
Under the generated context every fragment with `securityDefinitions` or `schemaDefinitions` needs the base, because each definition is a node named by its key and, without a base, that node is dropped together with all its triples; the triples shown for such fragments are those with the base.
Both contexts coerce `created` and `modified` to `xsd:dateTime`, and `support` and `href` to `xsd:anyURI`, at every path where the published context defines them.

Entries are ordered first by effect on triples (predicate IRI, then IRI versus literal object, then literal datatype or language, then container or structure), then by term presence without a triple difference, then by scoping, and both parts follow that order.
In outputs, `td:`, `jsonschema:`, `wotsec:`, `hctl:`, `rdf:` and `xsd:` abbreviate the WoT and W3C namespaces; an IRI written `<skos:note>` is an unexpanded compact IRI that the processor emitted as an absolute IRI with the scheme `skos`.

## Part 1: Where the generated context differs

### Data schema `type` is a property, not `@type`

Published. In every data-schema scope (`/properties`, `/input`, `/output`, `/data`, `/dataResponse`, `/subscription`, `/cancellation`) `type` is an alias of `@type`.

Generated. `type` maps to `jsonschema:type` with type coercion `@vocab`.

Effect. `{"properties":{"p":{"type":"string"}}}` gives `rdf:type jsonschema:StringSchema` under the published context and `jsonschema:type jsonschema:StringSchema` under the generated one.

Status. Undecided.

### Security `scheme` is a property, not `@type`

Published. In `/securityDefinitions`, `scheme` is an alias of `@type`.

Generated. `scheme` maps to `wotsec:scheme` with type coercion `@vocab`.

Effect. `{"securityDefinitions":{"basic_sc":{"scheme":"basic"}}}` gives `rdf:type wotsec:BasicSecurityScheme` under the published context and `wotsec:scheme wotsec:BasicSecurityScheme` under the generated one.
An unknown value such as `"invalidScheme"` gives `rdf:type wotsec:invalidScheme` and `wotsec:scheme wotsec:invalidScheme` respectively.

Status. Undecided.

### `unit` uses `qudt:unit`

Published. In data-schema scopes `unit` maps to `schema:unitCode` (`http://schema.org/unitCode`) with type coercion `@vocab`.

Generated. `unit` maps to `qudt:unit` (`http://qudt.org/schema/qudt/unit`) with type coercion `@vocab`.

Effect. `"unit":"qudt:DEG_C"` gives `schema:unitCode <qudt:DEG_C>` under the published context and `qudt:unit <http://qudt.org/schema/qudt/DEG_C>` under the generated one.
An absolute IRI value such as the om-2 `degree_Celsius` IRI is kept under both, with the two different predicates.

Status. Undecided.

### `license` is not a term

Published. The root term `license` maps to `dct:license`.

Generated. There is no `license` term; the key resolves through the default vocabulary.

Effect. `{"license":"http://x/l"}` gives `<http://purl.org/dc/terms/license> "http://x/l"` under the published context and `td:license "http://x/l"` under the generated one.

Status. Undecided.

### Security scheme aliases `cert`, `pop` and `public`

Published. `/securityDefinitions` defines `cert`, `pop` and `public` as aliases of `wotsec:CertSecurityScheme`, `wotsec:PoPSecurityScheme` and `wotsec:PublicSecurityScheme`.

Generated. These three terms are absent; the other nine scheme aliases are present.

Effect. `"scheme":"cert"` gives `rdf:type wotsec:CertSecurityScheme` under the published context and `wotsec:scheme wotsec:cert` under the generated one; `pop` and `public` behave alike.

Status. Undecided.

### `schema` in a security scheme is the schema.org prefix

Published. In `/securityDefinitions`, `schema` maps to `hctl:hasAdditionalOutputSchema` with type coercion `@id`.

Generated. In `/securityDefinitions`, `schema` is a prefix definition for `http://schema.org/`.

Effect. `"schema":"urn:x"` inside a security scheme gives `hctl:hasAdditionalOutputSchema <urn:x>` under the published context and the predicate `<http://schema.org/>` under the generated one.
Conversely, `schema:name` gives `<schema:name>` under the published context and `<http://schema.org/name>` under the generated one.
When the TD declares its own `schema` prefix, for example `https://schema.org/`, `schema:name` inside a security scheme follows that declaration under the published context and still gives `<http://schema.org/name>` under the generated one.

Status. Undecided.

### `uriVariables` in a security scheme keeps the root mapping

Published. In `/securityDefinitions`, `uriVariables` maps to `td:uriVariables` with no container and no scoped context.

Generated. `uriVariables` keeps the root definition `td:hasUriTemplateSchema` with `@container: @index`, `@index: name` and a data-schema scoped context.

Effect. `"uriVariables":{"u":{"type":"string"}}` inside a security scheme gives `td:uriVariables`, a member `wotsec:u` and `wotsec:type "string"` under the published context, and `td:hasUriTemplateSchema`, `wotsec:name "u"` and `jsonschema:type` under the generated one.

Status. Undecided.

### Prefix set

Published. Declares `dct` and no prefix for SKOS, RDF (at the root), QUDT or OWL.

Generated. Declares `dcterms` instead of `dct`, and adds `bcp47`, `foaf`, `owl`, `qudt`, `rdf`, `shex`, `skos`, `vann` and `xml` at the root.

Effect. `{"skos:note":"n","rdf:value":"v","qudt:x":"q"}` gives the predicates `<skos:note>`, `<rdf:value>` and `<qudt:x>` under the published context and the expanded SKOS, RDF and QUDT IRIs under the generated one.
`"dct:creator"` gives `<http://purl.org/dc/terms/creator>` under the published context and `<dct:creator>` under the generated one.

Status. Undecided.

### Operation-type terms at the root

Published. Defines no root term for operation types; it defines the same terms in the `/forms` and `/links` scopes, for example `"readproperty":"td:readProperty"`, where `op` maps to `hctl:hasOperationType` with type coercion `@vocab`.

Generated. Defines the 18 operation types (`readproperty`, `writeproperty`, `observeproperty`, `unobserveproperty`, `invokeaction`, `queryaction`, `cancelaction`, `subscribeevent`, `unsubscribeevent`, `readallproperties`, `writeallproperties`, `readmultipleproperties`, `writemultipleproperties`, `observeallproperties`, `unobserveallproperties`, `queryallactions`, `subscribeallevents`, `unsubscribeallevents`) as root terms mapped to their `td:` IRIs.

Effect. `op` values expand to the same IRIs under both contexts, for example `hctl:hasOperationType td:readProperty`.
Inside a form, a key `"readproperty":"y"` gives `td:readProperty "y"` under both contexts.
At the root, a key `"readproperty":"x"` gives `td:readproperty "x"` under the published context and `td:readProperty "x"` under the generated one.

Status. Undecided.

### A security scheme is a node named by its key

Published. `securityDefinitions` has `@container: @index` with `@index: hasInstanceConfiguration`, and the root term `hasInstanceConfiguration` has type coercion `@id`.

Generated. `securityDefinitions` has type coercion `@id` and `@container: @id`, with no `@index`; the context has no `hasInstanceConfiguration` term.

Effect. `{"securityDefinitions":{"basic_sc":{"scheme":"basic"}}}` gives a blank node for the scheme under the published context, with `td:hasInstanceConfiguration <http://example.org/basic_sc>` on it with a base and no such triple without a base.
The generated context gives `td:definesSecurityScheme <http://example.org/basic_sc>` and `<http://example.org/basic_sc> wotsec:scheme wotsec:BasicSecurityScheme` with a base and no triple at all without one.
The key is resolved like any `@id` value: `http://x.example/abs` and `urn:sec:b` are kept, `td:x` expands as a compact IRI to `https://www.w3.org/2019/wot/td#x`, `title` gives `<http://example.org/title>`, and a key with a space (`a b`) gives no triple, neither for the definition nor for a reference to it.
A security scheme and a schema definition with the same key `s1` become one node `<http://example.org/s1>` that carries `wotsec:scheme wotsec:BasicSecurityScheme` and `td:type "string"`.
A Thing with `"id":"http://example.org/basic_sc"` and the key `basic_sc` becomes one node with its scheme: `<http://example.org/basic_sc> td:definesSecurityScheme <http://example.org/basic_sc>`.
A property affordance named `basic_sc` stays a separate blank node with `td:name "basic_sc"`.

Cause. The `jsonld_container: "@id"` annotation on `securityDefinitions` in `resources/schemas/thing_description.yaml`.

Status. Undecided.

### Security references and combination members

Published. Root `security` has type coercion `xsd:string`; `security` in `/forms` and `/links` has type coercion `@id`; `allOf` and `oneOf` in `/securityDefinitions` have none.

Generated. `security` has type coercion `@id` at every path; `allOf` and `oneOf` in `/securityDefinitions` have none.

Effect. Under the generated context, Thing-level, form-level and link-level `"security":"basic_sc"` give `td:hasSecurityConfiguration <http://example.org/basic_sc>`, the node of the scheme, with a base and no triple without one; `"security":["a","b"]` gives two IRIs.
Under the published context, the Thing-level reference gives `"basic_sc"`, the form-level and link-level references give `<http://example.org/basic_sc>` (dropped without a base), and `"security":["a","b"]` at the Thing level gives two literals.
`"oneOf":["basic_sc"]` and `"allOf":["basic_sc"]` in a combo scheme give the literals `wotsec:oneOf "basic_sc"` and `wotsec:allOf "basic_sc"` under both contexts.

Cause. The range `SecurityScheme` of the `security` slot in `resources/schemas/thing_description.yaml` and `resources/schemas/hypermedia.yaml`.

Status. Undecided.

### Node-reference coercion on object-valued terms

Published. Root `forms` and `links` have type coercion `@id`; `allOf`, `oneOf` and `properties` in data-schema scopes have none.

Generated. Root `forms` and `links` have no type coercion; `allOf`, `oneOf` and `properties` in data-schema scopes have type coercion `@id`.

Effect. For object values the triples are the same under both contexts, as the test corpus and `oneOf` and `anyOf` fragments with object members show.
A string value differs: `"forms":"f1"` gives `td:hasForm <http://example.org/f1>` under the published context and `td:hasForm "f1"` under the generated one.

Status. Undecided.

### Link and form `type` is coerced to an IRI

Published. In `/forms` and `/links`, `type` maps to `hctl:hintsAtMediaType` with no type coercion.

Generated. The same mapping with type coercion `@vocab`.

Effect. `{"links":[{"href":"http://a","type":"application/pdf"}]}` gives `hctl:hintsAtMediaType "application/pdf"` under the published context and `hctl:hintsAtMediaType <https://www.w3.org/2019/wot/hypermedia#application/pdf>` under the generated one.
The value `" application/td+json"` (leading space) gives a literal under the published context and no triple under the generated one; the test corpus loses three triples this way.

Status. Undecided.

### `anchor`, `proxy`, `authorization`, `token` and `refresh` are `xsd:anyURI`

Published. `anchor` in `/forms` and `/links`, and `proxy`, `authorization`, `token` and `refresh` in `/securityDefinitions` and `/security`, have type coercion `@id`.

Generated. All five have type coercion `xsd:anyURI` in every scope where they occur.

Effect. `{"links":[{"href":"http://a","anchor":"http://a/anchor"}]}` gives `hctl:hasAnchor <http://a/anchor>` under the published context and `hctl:hasAnchor "http://a/anchor"^^xsd:anyURI` under the generated one; `"authorization":"https://as.example/auth"` in a security scheme gives `wotsec:authorization <https://as.example/auth>` and `wotsec:authorization "https://as.example/auth"^^xsd:anyURI`, and `proxy`, `token` and `refresh` behave alike.
A relative value such as `"anchor":"anchor"` gives `hctl:hasAnchor <http://example.org/anchor>` with a base and no triple without one under the published context, and `hctl:hasAnchor "anchor"^^xsd:anyURI` with and without a base under the generated one.

Cause. The five slots have `range: uri` and no `implements: owl:ObjectProperty` in `resources/schemas/hypermedia.yaml` and `resources/schemas/wot_security.yaml`.

Status. Undecided.

### `title` and `description` carry no language

Published. Root `title` and `description` have the language mapping `en`.

Generated. Neither has a language mapping.

Effect. `{"@context":{"@language":"de"},"title":"Lampe"}` gives `td:title "Lampe"@en` under the published context and `td:title "Lampe"@de` under the generated one; without a default language the generated context gives `"Lampe"`.

Status. Undecided.

### String literals without `xsd:string`

Published. `instance` has type coercion `xsd:string`.

Generated. `instance` has no type coercion.

Effect. With `"@language":"de"`, `"version":{"instance":"1.0"}` gives `"1.0"` under the published context and `"1.0"@de` under the generated one.
Combo `oneOf` members have no type coercion in either context, so `"oneOf":["basic_sc"]` gives `wotsec:oneOf "basic_sc"@de` under both.
`model`, the sibling of `instance` in `version`, has no type coercion in either context, so `"version":{"model":"M1"}` gives `td:model "M1"@de` under both; for the published shapes, see "Version `model` takes the default language" in Part 2 of the [SHACL note](shacl.md).

Status. Undecided.

### Numeric datatypes

Published. `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum`, `multipleOf`, `minItems`, `maxItems`, `minLength` and `maxLength` have no type coercion.

Generated. The first five have type coercion `xsd:decimal` and the last four `xsd:nonNegativeInteger`, in every data-schema scope.

Effect. `"minimum":0` gives `"0"^^xsd:integer` under the published context and `"0"^^xsd:decimal` under the generated one; `"maximum":55.2` gives `"5.52E1"^^xsd:double` and `"5.52E1"^^xsd:decimal`, whose lexical form is not valid for `xsd:decimal`; `"minItems":3` gives `"3"^^xsd:integer` and `"3"^^xsd:nonNegativeInteger`.

Cause. Upstream `gen-jsonld-context` emits a type coercion for each slot whose range is a non-string XSD type, such as `range: decimal` on `minimum` in `resources/schemas/jsonschema.yaml`, and the generated context keeps it.
Changing the range of `minimum` to `string` removed its type coercion, while `maximum` kept `xsd:decimal`.

Status. Undecided.

### Boolean datatypes

Published. `idempotent`, `safe`, `synchronous`, `observable`, `success`, `readOnly` and `writeOnly` have no type coercion.

Generated. All seven have type coercion `xsd:boolean`.

Effect. JSON `true` gives `"true"^^xsd:boolean` under both.
A string value is coerced only by the generated context: `"idempotent":"yes"` gives `"yes"` under the published context and the ill-typed `"yes"^^xsd:boolean` under the generated one; `"readOnly":"no"` gives `"no"^^xsd:boolean`.

Cause. Upstream `gen-jsonld-context` emits type coercion `xsd:boolean` for each slot with `range: boolean`, such as `readOnly` in `resources/schemas/jsonschema.yaml`, and the generated context keeps it.
Changing the range of `readOnly` to `string` removed its type coercion, while `writeOnly` kept `xsd:boolean`.

Status. Undecided.

### `base` and `profile` are `xsd:anyURI`

Published. `base` and `profile` have no type coercion.

Generated. Both have type coercion `xsd:anyURI`.

Effect. `"profile":"http://p/x"` gives `td:followsProfile "http://p/x"` under the published context and `td:followsProfile "http://p/x"^^xsd:anyURI` under the generated one; `base` behaves the same way with `td:baseURI`.

Status. Undecided.

### A schema definition is a node named by its key

Published. `schemaDefinitions` has `@container: @index` with no `@index` mapping.

Generated. `schemaDefinitions` has `@container: @id`.

Effect. `{"schemaDefinitions":{"s1":{"type":"string"}}}` gives a blank node with `td:type "string"` under the published context, with and without a base; the key gives no triple.
The generated context gives `td:schemaDefinitions <http://example.org/s1>` and `<http://example.org/s1> td:type "string"` with a base and no triple at all without one.
An additional response `"schema":"s1"` gives `hctl:hasAdditionalOutputSchema <http://example.org/s1>` with a base and no triple without one under both contexts; under the generated context that IRI is the node of the definition, under the published context no node carries it.
Key resolution and collisions are as in "A security scheme is a node named by its key".

Cause. The `jsonld_container: "@id"` annotation on `schemaDefinitions` in `resources/schemas/thing_description.yaml`.

Status. Undecided.

### `anyOf` in data-schema scopes

Published. Every data-schema scope defines `anyOf` as `jsonschema:anyOf` with `@container: @set`.

Generated. No `anyOf` term; the key resolves through the default vocabulary `jsonschema:`.

Effect. Both contexts give `jsonschema:anyOf` for object members.

Status. Undecided.

### Root terms from the `MultiLanguage` class

Published. No such terms.

Generated. Root terms `MultiLanguage` (`td:MultiLanguage`), `language_tag` (alias of `@id`) and `language_value` (`td:language_value`).

Effect. A node with both `@id` and `language_tag` fails under the generated context with the jsonld.js error "colliding keywords"; the published context gives `td:language_tag`.
A node with only `language_tag` takes its value as node identifier under the generated context.
`language_value` gives `td:language_value` under both.

Status. Undecided.

### Scoped context of `security`

Published. Root `security` carries a scoped context that redeclares the WoT prefixes, sets `@vocab` to `wotsec:` and repeats the security-scheme terms, including `name` mapped to `wotsec:name`.

Generated. `security` has no scoped context. Both contexts map `name` to `wotsec:name` in `/securityDefinitions`.

Effect. String and array-of-string values differ only as described in "Security references and combination members".
An object value `{"security":{"name":"x","scheme":"basic"}}` gives `rdf:type wotsec:BasicSecurityScheme` and `wotsec:name "x"` under the published context, and `td:name "x"` and `td:scheme "basic"` under the generated one.
Object values do not occur in a TD, because TD 1.1 types `security` as string or Array of string.

Status. Undecided.

### Scoped context of Thing-level `uriVariables`

Published. Root `uriVariables` has no scoped context.

Generated. Root `uriVariables` carries a data-schema scoped context.

Effect. `{"uriVariables":{"u":{"type":"string","enum":["a"]}}}` gives `td:type "string"` and `td:enum "a"` under the published context and `jsonschema:type` and `jsonschema:enum` under the generated one; both give `td:name "u"`.

Status. Undecided.

### Re-scoping of nested affordance members

Published. In `/forms`, `/links` and `/input`, the terms `cancellation`, `data`, `dataResponse`, `input`, `output` and `subscription` carry their own scoped context again; in `/output`, `/data`, `/dataResponse`, `/subscription` and `/cancellation` a subset of them does, and in `/properties` none does.

Generated. Where the published context re-scopes these terms, the generated terms have no scoped context, so their values are read in the enclosing scope.

Effect. Inside a form, `{"data":{"type":"string","properties":{"q":{"type":"string"}}}}` gives `hctl:hintsAtMediaType <https://www.w3.org/2019/wot/hypermedia#string>`, `jsonschema:type jsonschema:StringSchema`, `td:hasPropertyAffordance` and `td:name "q"` under the generated context, and `rdf:type jsonschema:StringSchema`, `jsonschema:properties` and `jsonschema:propertyName "q"` under the published one.
These members do not occur at these positions in a TD.

Status. Undecided.

### Terms redeclared in scoped contexts

Published. Data-schema, form, link and security scopes declare only their own vocabulary and otherwise fall back to the scope's `@vocab`.

Generated. These scopes also declare class terms (for example `StringSchema` in `/forms`) and terms of other modules (for example `href` in data-schema scopes).

Effect. `{"properties":{"p":{"href":"http://a/b"}}}` gives `jsonschema:href "http://a/b"` under the published context and `hctl:hasTarget "http://a/b"^^xsd:anyURI` under the generated one.
Forms, links and data schemas nested inside a security scheme add two more cases: `name` resolves to `wotsec:name` under the published context and `td:name` under the generated one, and `format` in a nested form or link to `wotsec:format` and `jsonschema:format`. These nestings do not occur in a TD.

Status. Undecided.

## Part 2: Defects in the published context

### `uriVariables` in a security scheme maps to an undefined term

Published. `/securityDefinitions` maps `uriVariables` to `td:uriVariables`, while the root maps it to `td:hasUriTemplateSchema`, and gives it no data-schema scope.
The TD ontology `resources/upstream/ontology/td.ttl` defines `td:hasUriTemplateSchema` but no `td:uriVariables`.

Generated. `uriVariables` in a security scheme keeps the root mapping and its data-schema scope, so `"uriVariables":{"u":{"type":"string"}}` inside a security scheme gives `td:hasUriTemplateSchema`, `wotsec:name "u"` and `jsonschema:type jsonschema:StringSchema`; see the Part 1 entry "`uriVariables` in a security scheme keeps the root mapping".

Effect. `"uriVariables":{"u":{"type":"string"}}` inside a security scheme gives `td:uriVariables`, a member predicate `wotsec:u` and `wotsec:type "string"`.

Status. Published defect.

### API key `in` maps to the term of the other schemes

Published. `/securityDefinitions` and `/security` map `in` to `wotsec:in` for every scheme and have no term for `wotsec:apikeyIn`.
The security ontology `resources/upstream/ontology/wotsec.ttl` declares `wotsec:in` with `schema:domainIncludes` the basic, digest and bearer schemes, and `wotsec:apikeyIn`, label "in", with `schema:domainIncludes wotsec:APIKeySecurityScheme`.
The published shapes constrain `wotsec:in` on the API key scheme as well, so they agree with the context and contradict the ontology.

Generated. The generated context also gives `wotsec:in "header"` for an API key scheme, while the generated shapes constrain `wotsec:apikeyIn`; see "API key `in` path" in Part 1 of the [SHACL note](shacl.md).

Effect. `{"securityDefinitions":{"k":{"scheme":"apikey","in":"header","name":"x"}}}` gives `rdf:type wotsec:APIKeySecurityScheme` and `wotsec:in "header"`.

Status. Published defect.

### Security scheme keys do not match their references

Published. `hasInstanceConfiguration`, the `@index` of `securityDefinitions`, has type coercion `@id`; root `security` has `xsd:string`, form `security` has `@id`, and combo `allOf` and `oneOf` have no coercion.
In `resources/upstream/ontology/td.ttl`, `td:hasSecurityConfiguration`, the IRI of `security`, is an `owl:ObjectProperty`, so the literal from the root coercion contradicts the ontology.

Generated. With the base `http://example.org/td`, the key `basic_sc` names the scheme node `<http://example.org/basic_sc>`, and the Thing-level, form-level and link-level references give that IRI.
Combo `oneOf` and `allOf` members give the literal `"basic_sc"`, so they do not match the key; see "Security references and combination members" in Part 1.
Without a base, neither the scheme nor a reference to it produces a triple.

Effect. Without a base IRI the key `basic_sc` produces no triple.
With the base `http://example.org/td`, the key gives `<http://example.org/basic_sc>`, the form-level reference matches it, but the Thing-level reference and combo members give the literal `"basic_sc"`, which does not.

Status. Published defect.

### Forced English language

Published. `title` and `description` have the language mapping `en`, which overrides the document default language.
The TD 1.1 specification `resources/upstream/html/index.html` states that the default language of a TD is defined by `@language` in the `@context`.

Generated. `title` and `description` have no language mapping; with `"@language":"de"`, `"title":"Lampe"` gives `td:title "Lampe"@de`.

Effect. With `"@language":"de"`, `"title":"Lampe"` gives `td:title "Lampe"@en`; the test corpus shows German and Arabic titles and a German description tagged `@en`.

Status. Published defect.

### No data-schema scope for `schemaDefinitions` and Thing-level `uriVariables`

Published. Neither term carries a scoped context, so their members are read with the root context and its `td:` vocabulary, which gives IRIs such as `td:type` and `td:enum` that `resources/upstream/ontology/td.ttl` does not define.

Generated. The generated context reproduces the `schemaDefinitions` case: with the base, `{"schemaDefinitions":{"s1":{"type":"string"}}}` gives `<http://example.org/s1> td:type "string"`.
Thing-level `uriVariables` carries a data-schema scope, so `"uriVariables":{"u":{"type":"string","enum":["a"]}}` gives `jsonschema:type jsonschema:StringSchema` and `jsonschema:enum "a"`.

Effect. `{"schemaDefinitions":{"s1":{"type":"string"}}}` gives `td:type "string"`, and Thing-level `"uriVariables":{"u":{"type":"string","enum":["a"]}}` gives `td:type` and `td:enum`.

Cause. In the generated context, the `jsonld_context: none` annotation on `schemaDefinitions` in `resources/schemas/thing_description.yaml`.

Status. Published defect.

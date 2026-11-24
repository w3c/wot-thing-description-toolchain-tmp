# Differences between the generated and the published OWL ontologies

This note records every lasting semantic difference between the OWL ontologies that wot-toolchain generates and the published WoT Thing Description 1.1 ontologies.
It also records defects of the published ontologies.
OWL output is of experimental quality in this project.

The generated ontologies are `resources/gens/owl/{td,hctl,wotsec,jsonschema,tm}.ttl`.
The published ontologies are the files with the same names in `resources/upstream/ontology/`, except `td.ttl` and `tm.ttl`, for which the files served by W3C are used; see Method.

Each entry in Part 1 has the status Undecided and each entry in Part 2 the status Published defect, both defined in the [README](index.md) of this directory.
Entries are ordered term presence, property type, class hierarchy, domain and range, restrictions and individuals, annotations, ontology header; within a group, modules follow the order td, hctl, wotsec, jsonschema, tm.

## Method

The reference is the files in `resources/upstream/`, with one exception.
The copies `resources/upstream/ontology/td.ttl` and `tm.ttl` differ from the files served at `https://www.w3.org/2019/wot/td` and `https://www.w3.org/2022/wot/tm`, which are identical to `ontology/td.ttl` and `ontology/tm.ttl` on the main branch of `w3c/wot-thing-description`.
In the local `td.ttl`, `td:versionInfo` is an `owl:ObjectProperty` with `schema:domainIncludes td:Thing` and `schema:rangeIncludes td:VersionInfo`, `td:VersionInfo` is declared as a class, and `td:instance` and `td:model` have `schema:domainIncludes td:VersionInfo`.
In the served `td.ttl`, `td:versionInfo` is an `owl:AnnotationProperty` without these statements, `td:VersionInfo` is not declared, and `td:instance` and `td:model` have `schema:domainIncludes td:versionInfo`.
The served `tm.ttl` declares `tm:versionInfo`, `tm:hasVersion`, `tm:model` and `tm:Version`; the local copy does not.
The local `hctl.ttl`, `wotsec.ttl` and `jsonschema.ttl` are identical to the files of the same names on that branch.
Statements about the published `td.ttl` and `tm.ttl` in this note describe the served files. On the merged published set, `robot validate-profile` reports the same kinds of violation with the served and the local files; the reports differ only in the annotation assertions on the terms above.
Parse each generated module and its published counterpart with rdflib and compare them term by term, where a term is every IRI subject other than the `owl:Ontology` node.
For each term compare presence and the object sets of these predicate groups: `rdf:type`; `rdfs:subClassOf`, `rdfs:subPropertyOf`, `owl:equivalentClass`, `owl:equivalentProperty`, `owl:inverseOf`, `owl:disjointWith`; `rdfs:domain` with `schema:domainIncludes`; `rdfs:range` with `schema:rangeIncludes`; `rdfs:label`; `rdfs:comment` with `skos:definition`; `skos:note`; `rdfs:isDefinedBy`; `rdfs:seeAlso`; `skos:inScheme`; and all remaining predicates, including blank node restrictions, as a further group.
Compare the `owl:Ontology` node of each pair separately.
To judge entailment, merge the modules of a set, add sample instance triples and compute the OWL 2 RL closure with owlrl.
To judge consistency, run the HermiT reasoner through ROBOT on a module plus sample instance triples.
To judge profile conformance, merge all generated modules into one file, do the same for the published modules, and run `robot validate-profile --profile DL` on each merged file; no file in either set has `owl:imports`.
To judge how instance data lands on these terms, expand a sample TD with `resources/gens/jsonldcontext/context.jsonld` and with `resources/upstream/context/td-context-1.1.jsonld`.

## Part 1: Where the generated ontology differs

### td:schemaDefinitions exists only in the generated ontology

Published. `td.ttl` does not declare `td:schemaDefinitions`, although the published context maps `schemaDefinitions` to `td:schemaDefinitions` with `@type: @id`.

Generated. `td:schemaDefinitions a owl:ObjectProperty ; rdfs:domain td:Thing ; rdfs:range jsonschema:DataSchema .`

Effect. A TD using `schemaDefinitions` produces triples on a term that only the generated ontology defines; under RL any subject of it is entailed to be a `td:Thing`.

Status. Undecided.

### td:VersionInfo exists only in the generated ontology, and td:versionInfo is an object property

Published. `td.ttl` declares `td:versionInfo` as `owl:AnnotationProperty` with no domain, range or includes, and does not declare `td:VersionInfo`. `td:instance` and `td:model` are `owl:DatatypeProperty` with `schema:domainIncludes td:versionInfo` and no range.

Generated. `td:versionInfo a owl:ObjectProperty ; rdfs:domain td:Thing ; rdfs:range td:VersionInfo .` and `td:VersionInfo a owl:Class .` `td:instance` and `td:model` are datatype properties with `rdfs:domain td:VersionInfo` and `rdfs:range xsd:string`.

Effect. Expanding `"version": {"instance": "1.0.0", "model": "2.0.0"}` with either context gives `ex:t td:versionInfo _:v` and `td:instance` and `td:model` literals on `_:v`. ROBOT reads the first triple as an annotation assertion with the published set and as an object property assertion with the generated set.
Under RL on the generated `td.ttl`, `ex:t td:versionInfo ex:v` entails `ex:t a td:Thing` and `ex:v a td:VersionInfo`; on the published `td.ttl` it entails no type.

Status. Undecided.

### wotsec:scheme and jsonschema:type are datatype properties instead of rdf:type

Published. Neither term exists. The published context maps the JSON keys `scheme` and `type` to `@type`.

Generated. `wotsec:scheme a owl:DatatypeProperty ; rdfs:range xsd:string .` and `jsonschema:type a owl:DatatypeProperty ; rdfs:domain jsonschema:DataSchema ; rdfs:range xsd:string .`

Effect. Expanding the same TD gives `_:b rdf:type wotsec:OAuth2SecurityScheme` and `_:d rdf:type jsonschema:StringSchema` with the published context, and `<oauth2_sc> wotsec:scheme wotsec:OAuth2SecurityScheme` and `_:d jsonschema:type jsonschema:StringSchema` with the generated context, without any `rdf:type`; `<oauth2_sc>` is the key of the security definition resolved against the base IRI.
Security schemes and data schemas of generated instance data are therefore never instances of their classes.
Because the objects are IRIs and the properties are datatype properties with range `xsd:string`, the RL closure on the generated ontology entails `wotsec:OAuth2SecurityScheme a xsd:string` and `jsonschema:StringSchema a xsd:string`.

Status. Undecided.

### jsonschema:anyOf and jsonschema:properties exist only in the published ontology

Published. `jsonschema:anyOf a owl:ObjectProperty ; schema:domainIncludes jsonschema:DataSchema ; schema:rangeIncludes jsonschema:DataSchema .` and `jsonschema:properties a owl:ObjectProperty ; schema:domainIncludes jsonschema:ObjectSchema ; schema:rangeIncludes jsonschema:DataSchema .`

Generated. Neither term is declared. Both contexts have a `properties` key. The published context has an `anyOf` key; the generated context has none and maps `anyOf` to `jsonschema:anyOf` only through its `@vocab`.

Effect. Instance triples with these predicates use terms the generated ontology does not define.

Status. Undecided.

### tm:Version, tm:hasVersion, tm:model and tm:versionInfo exist only in the published ontology

Published. `tm.ttl` declares `tm:Version a owl:Class`; `tm:hasVersion a owl:ObjectProperty ; schema:domainIncludes tm:ThingModel ; schema:rangeIncludes tm:Version .`; `tm:model a owl:DatatypeProperty ; schema:domainIncludes tm:Version ; schema:rangeIncludes schema:Text .`; and `tm:versionInfo a owl:AnnotationProperty`.

Generated. No module declares any of these terms. Neither context maps a term to them.

Effect. Both contexts map the keys `version` and `model` to `td:versionInfo` and `td:model`, so instance data reaches the TM version terms only through explicit `tm:` IRIs.

Status. Undecided.

### The TM module does not redeclare TD terms

Published. `tm.ttl` redeclares `td:hasInteractionAffordance` and `td:hasLink` as `owl:ObjectProperty`, and `td:title` and `td:description` as `owl:DatatypeProperty`, each with an `@en` label and `rdfs:isDefinedBy td:`.
`td:hasInteractionAffordance` has `rdfs:domain tm:ThingModel` and `rdfs:range td:InteractionAffordance`; `td:hasLink` has `schema:domainIncludes tm:ThingModel` and `schema:rangeIncludes hctl:Link`; `td:title` and `td:description` have `schema:domainIncludes tm:ThingModel` and `schema:rangeIncludes schema:Text`; `td:title` also has `rdfs:subPropertyOf dcterms:title`, which `td.ttl` states as well.
It also declares `dc:publisher`, `dc:title`, `dcterms:author`, `dcterms:contributor`, `dcterms:description`, `dcterms:license`, `vann:preferredNamespacePrefix`, `vann:preferredNamespaceUri`, `schema:name` and `schema:url` as annotation properties.

Generated. `tm.ttl` declares `tm:ThingModel`, `tm:optional`, `tm:required` and `tm:ref` and no TD term.
It declares `dcterms:contributor`, `dcterms:creator`, `dcterms:license`, `dcterms:publisher`, `dcterms:title`, `vann:preferredNamespacePrefix`, `vann:preferredNamespaceUri`, `schema:name`, `schema:url`, `skos:definition` and `skos:inScheme` as annotation properties, and `schema:Organization` as a class.

Effect. The generated set states no domain or range involving `tm:ThingModel` for TD properties. See "tm.ttl makes every Thing a ThingModel" in Part 2 for the consequence of the published `rdfs:domain`.

Status. Undecided.

### Classes are typed owl:Class only

Published. `td.ttl`, `hctl.ttl` and `wotsec.ttl` type their classes as both `owl:Class` and `rdfs:Class`; `jsonschema.ttl` and `tm.ttl` use `owl:Class` only.

Generated. Every class is typed `owl:Class` only.

Effect. No OWL consequence.

Status. Undecided.

### Property types of wotsec:authorization, wotsec:token, wotsec:refresh, wotsec:allOf and wotsec:oneOf

Published. `wotsec:authorization`, `wotsec:token`, `wotsec:refresh`, `wotsec:allOf` and `wotsec:oneOf` are object properties with no range and no `schema:rangeIncludes`.
The published context maps `authorization`, `token` and `refresh` with `@type: @id`.

Generated. `wotsec:authorization`, `wotsec:token` and `wotsec:refresh` are datatype properties with `rdfs:range xsd:anyURI`. `wotsec:allOf` and `wotsec:oneOf` are datatype properties with `rdfs:range xsd:string`.
The generated context maps `authorization`, `token` and `refresh` with `@type: xsd:anyURI`. Within security definitions both contexts map `allOf` and `oneOf` to `wotsec:allOf` and `wotsec:oneOf` with `@container: @set` and no `@type`.

Effect. Expanding a sample TD gives `_:b wotsec:authorization <http://z.example/>` with the published context and `<oauth2_sc> wotsec:authorization "http://z.example/"^^xsd:anyURI` with the generated context, and likewise for `token` and `refresh`; both contexts give `wotsec:allOf "basic_sc"`.
On the merged generated modules plus `ex:s wotsec:authorization "http://z.example/"^^xsd:anyURI ; wotsec:token "http://t.example/"^^xsd:anyURI ; wotsec:refresh "http://r.example/"^^xsd:anyURI` and `ex:c wotsec:allOf "basic_sc" ; wotsec:oneOf "basic_sc"`, ROBOT reports no profile violation on these properties; on the merged published modules plus the same triples it reports "Cannot pun between properties" for all five.
With IRI objects for `wotsec:authorization`, `wotsec:token` and `wotsec:refresh`, as the published context produces them, ROBOT reports "Cannot pun between properties" for the three on the merged generated modules and no violation on them on the merged published modules.
The only violation ROBOT reports on the merged generated modules is "Cannot pun between properties" for `dcterms:title`, which the generated `td.ttl` declares as a datatype property and the generated `hctl.ttl`, `wotsec.ttl`, `jsonschema.ttl` and `tm.ttl` declare as an annotation property, so the generated ontology is not in OWL 2 DL.
Under RL on the generated ontology, `ex:s wotsec:token "http://t.example/"^^xsd:anyURI` entails `ex:s a wotsec:OAuth2SecurityScheme, wotsec:SecurityScheme`, and `wotsec:refresh` behaves the same; `wotsec:authorization` entails no type. The published ontology entails nothing for any of the three.

Status. Undecided.

### Single-class includes replaced by rdfs:domain and rdfs:range

Published. These properties have `schema:domainIncludes` with a single class, and some have `schema:rangeIncludes` with a single class. Neither entails anything.
The td, hctl and wotsec ontologies state no `rdfs:domain` and no `rdfs:range`; jsonschema states `rdfs:range` and no `rdfs:domain`; tm states both only on `td:hasInteractionAffordance`.

Generated. Where the published ontology lists a single class, the generated ontology states `rdfs:domain` or `rdfs:range` with the same class:
in td, `td:baseURI`, `td:definesSecurityScheme`, `td:followsProfile`, `td:hasActionAffordance`, `td:hasEventAffordance`, `td:hasPropertyAffordance`, `td:hasLink` and `td:hasForm` (range only), `td:hasCancellationSchema`, `td:hasNotificationSchema`, `td:hasNotificationResponseSchema`, `td:hasSubscriptionSchema`, `td:hasInputSchema`, `td:hasOutputSchema`, `td:hasInstanceConfiguration`, `td:hasInteractionAffordance`, `td:name`, `td:isIdempotent`, `td:isObservable`, `td:isSafe` and `td:isSynchronous`;
in hctl, `hctl:additionalReturns`, `hctl:returns`, `hctl:forContentCoding`, `hctl:forSubProtocol`, `hctl:hasAdditionalOutputSchema`, `hctl:hasAnchor`, `hctl:hasHreflang`, `hctl:hasOperationType`, `hctl:hasRelationType`, `hctl:hasSizes`, `hctl:hintsAtMediaType` and `hctl:isSuccess`;
in wotsec, `wotsec:alg`, `wotsec:allOf`, `wotsec:apikeyIn`, `wotsec:flow`, `wotsec:format`, `wotsec:identity`, `wotsec:oneOf`, `wotsec:proxy`, `wotsec:qop`, `wotsec:refresh` and `wotsec:token`;
in jsonschema, `jsonschema:allOf`, `jsonschema:oneOf`, `jsonschema:const`, `jsonschema:default`, `jsonschema:enum`, `jsonschema:readOnly` and `jsonschema:writeOnly` (domain `jsonschema:DataSchema`), `jsonschema:items` (domain `jsonschema:ArraySchema`), `jsonschema:contentEncoding`, `jsonschema:contentMediaType`, `jsonschema:maxLength`, `jsonschema:minLength` and `jsonschema:pattern` (domain `jsonschema:StringSchema`), `jsonschema:maxItems` and `jsonschema:minItems` (domain `jsonschema:ArraySchema`), and `jsonschema:required` (domain `jsonschema:ObjectSchema`).
A range that the published ontology gives as a schema.org class becomes an XSD datatype; see "schema.org value classes replaced by XSD datatypes".
Where the published ontology lists several classes, the generated ontology keeps `schema:domainIncludes`: `td:title`, `td:description`, `td:titleInLanguage`, `td:descriptionInLanguage`, `td:hasForm`, `td:hasSecurityConfiguration`, `hctl:hasTarget`, `wotsec:authorization`, `wotsec:in`, `wotsec:name`, `jsonschema:exclusiveMaximum`, `jsonschema:exclusiveMinimum`, `jsonschema:maximum`, `jsonschema:minimum` and `jsonschema:multipleOf`.
`td:hasUriTemplateSchema`, `hctl:forContentType` and `wotsec:scopes` have a single published class; the generated ontology keeps `schema:domainIncludes` for them because it adds classes, see their entries. No generated module uses `schema:rangeIncludes`.
For `td:instance`, `td:model` and `td:versionInfo` see "td:VersionInfo exists only in the generated ontology, and td:versionInfo is an object property".

Effect. Every use now classifies its subject, and for object properties its object. Under RL on the generated ontology, `ex:a td:name "a"` entails `ex:a a td:InteractionAffordance` and `ex:p td:isObservable true` entails `ex:p a td:PropertyAffordance`; the published ontology entails nothing for either.
RDFS entailment alone gives the same result: with `td.ttl` and `ex:a td:name "x"`, the generated ontology entails `ex:a rdf:type td:InteractionAffordance` and the published one entails no type other than `rdfs:Resource`.

Status. Undecided.

### Domains and ranges with no published counterpart

Published. `td:hasActionAffordance`, `td:hasEventAffordance`, `td:hasPropertyAffordance` and `td:hasLink` have `schema:rangeIncludes` and no domain. The following properties have no range and no `schema:rangeIncludes`: `td:definesSecurityScheme`, `td:hasCancellationSchema`, `td:hasInputSchema`, `td:hasNotificationResponseSchema`, `td:hasNotificationSchema`, `td:hasOutputSchema`, `td:hasSubscriptionSchema`, `td:hasUriTemplateSchema`, `td:instance`, `td:model`, `td:hasSecurityConfiguration`, `hctl:hasAdditionalOutputSchema`, `hctl:hasAnchor`, `hctl:hasHreflang`, `hctl:hasOperationType`, `hctl:hasRelationType`, `hctl:hasSizes`, `hctl:hasTarget`, and in wotsec `wotsec:alg`, `wotsec:apikeyIn`, `wotsec:flow`, `wotsec:format`, `wotsec:identity`, `wotsec:in`, `wotsec:name` and `wotsec:qop`. `td:hasUriTemplateSchema` has `schema:domainIncludes td:InteractionAffordance` only.

Generated. `td:hasActionAffordance`, `td:hasEventAffordance`, `td:hasPropertyAffordance` and `td:hasLink` have `rdfs:domain td:Thing`.
Added ranges: `wotsec:SecurityScheme` for `td:definesSecurityScheme` and `td:hasSecurityConfiguration`; `jsonschema:DataSchema` for `hctl:hasAdditionalOutputSchema`, `td:hasCancellationSchema`, `td:hasInputSchema`, `td:hasNotificationResponseSchema`, `td:hasNotificationSchema`, `td:hasOutputSchema`, `td:hasSubscriptionSchema` and `td:hasUriTemplateSchema`; `xsd:string` for `td:instance`, `td:model`, `hctl:hasHreflang`, `hctl:hasRelationType`, `hctl:hasSizes`, `wotsec:alg`, `wotsec:apikeyIn`, `wotsec:flow`, `wotsec:format`, `wotsec:identity`, `wotsec:in`, `wotsec:name` and `wotsec:qop`; `td:OperationType` for `hctl:hasOperationType`; `xsd:anyURI` for `hctl:hasAnchor` and `hctl:hasTarget`. The ranges of `wotsec:authorization`, `wotsec:token`, `wotsec:refresh`, `wotsec:allOf` and `wotsec:oneOf` are in "Property types of wotsec:authorization, wotsec:token, wotsec:refresh, wotsec:allOf and wotsec:oneOf".
`td:hasUriTemplateSchema` gains `schema:domainIncludes td:Thing`. `td:hasInstanceConfiguration` has a domain and no range; the generated context maps no term to it, while the published context uses it as the `@index` key of `securityDefinitions`.
The generated context gives `securityDefinitions` and `schemaDefinitions` `@container: @id`, and maps `security` and `schema` with `@type: @id`. The published context gives both maps `@container: @index`, and maps `security` with `@type: xsd:string` at the top level and `@type: @id` in forms.

Effect. Under RL on the generated ontology, `ex:v td:hasActionAffordance ex:aa` entails `ex:v a td:Thing`; the published set entails `ex:v a tm:ThingModel` instead, see Part 2.
Expanding a sample TD with the generated context gives `ex:t td:definesSecurityScheme <oauth2_sc>` and `ex:t td:hasSecurityConfiguration <oauth2_sc>`, where `<oauth2_sc>` is the key resolved against the base IRI, so the reference and the definition are the same node; a `schema` reference and its `schemaDefinitions` entry likewise share the node `<err>`. With the published context the definition is a blank node with `td:hasInstanceConfiguration <oauth2_sc>` and the top-level reference is the literal `"oauth2_sc"`.
Under RL on the generated ontology, `ex:t td:hasSecurityConfiguration ex:sc` entails `ex:sc a wotsec:SecurityScheme` and no type for `ex:t`, and `ex:r hctl:hasAdditionalOutputSchema ex:d` entails `ex:r a hctl:AdditionalExpectedResponse` and `ex:d a jsonschema:DataSchema`; the published ontology entails nothing for either.
Under RL on the generated ontology, `ex:l hctl:hasAnchor "http://a.example/"^^xsd:anyURI` entails `ex:l a hctl:Link`; the published ontology entails nothing.

Status. Undecided.

### schema.org value classes replaced by XSD datatypes

Published. `schema:rangeIncludes schema:Text` on `td:name`, `hctl:forContentCoding`, `hctl:forContentType`, `hctl:forSubProtocol`, `hctl:hintsAtMediaType`, `tm:optional`, `tm:required` and `tm:ref`; `schema:rangeIncludes schema:Boolean` on `td:isIdempotent`, `td:isObservable`, `td:isSafe`, `td:isSynchronous` and `hctl:isSuccess`; `schema:rangeIncludes schema:URL` on `td:baseURI`.

Generated. The same properties have `rdfs:range xsd:string`, `xsd:boolean` and `xsd:anyURI` respectively.

Effect. The XSD ranges constrain literal values; `schema:rangeIncludes` constrains nothing. HermiT finds the generated `td.ttl` plus `ex:a td:isSafe "yes"` inconsistent and the published `td.ttl` plus the same triple consistent.

Status. Undecided.

### td:title and td:description range rdfs:Literal; language map properties lose their range

Published. `td:title`, `td:description`, `td:titleInLanguage` and `td:descriptionInLanguage` have `schema:rangeIncludes schema:Text`.

Generated. `td:title rdfs:range rdfs:Literal` and `td:description rdfs:range rdfs:Literal`, with the same `schema:domainIncludes`; `td:titleInLanguage` and `td:descriptionInLanguage` have no range.

Effect. HermiT finds the generated `td.ttl` plus `td:title "Lampe"@de, "Lamp"` and `td:description "x"^^xsd:string` consistent; no tested instance data is excluded.

Status. Undecided.

### hctl:forContentType applies to responses as well as forms

Published. `hctl:forContentType schema:domainIncludes hctl:Form ; schema:rangeIncludes schema:Text .`

Generated. `schema:domainIncludes` `hctl:Form`, `hctl:ExpectedResponse` and `hctl:AdditionalExpectedResponse`; `rdfs:range xsd:string`.

Effect. Only the range entails; `contentType` on a response is described by the generated ontology and not by the published one.

Status. Undecided.

### wotsec:scopes on a form classifies the form as an OAuth2 security scheme

Published. `wotsec:scopes schema:domainIncludes wotsec:OAuth2SecurityScheme .`

Generated. `wotsec:scopes rdfs:domain wotsec:OAuth2SecurityScheme ; schema:domainIncludes hctl:Form, wotsec:OAuth2SecurityScheme ; rdfs:range xsd:string .`

Effect. Both contexts map form-level `scopes` to `wotsec:scopes`, and expansion yields `_:form wotsec:scopes "s1"` with either context.
Under RL on the generated ontology, `ex:f a hctl:Form ; wotsec:scopes "x"` entails `ex:f a wotsec:OAuth2SecurityScheme, wotsec:SecurityScheme`; the published ontology entails nothing.

Status. Undecided.

### jsonschema:format has domain DataSchema; jsonschema:propertyName has no domain

Published. `jsonschema:format schema:domainIncludes jsonschema:StringSchema ; rdfs:range xsd:string .` and `jsonschema:propertyName schema:domainIncludes jsonschema:DataSchema ; rdfs:range xsd:string .`
The published context maps `propertyName` to `jsonschema:propertyName` and uses it as the `@index` key of the `properties` map of nested object schemas, such as the members of an action `input`. The first-level `properties` map of a property affordance is indexed by `name`, as are the affordance maps, and `name` maps to `td:name`.

Generated. `jsonschema:format rdfs:domain jsonschema:DataSchema ; rdfs:range xsd:string .` and `jsonschema:propertyName rdfs:range xsd:string .`
The generated context indexes the same maps with the same keys. Expanding a sample TD with either context gives `jsonschema:propertyName "i1"` for a member `i1` of an action `input` and `td:name "k1"` for a member `k1` of `properties` in a property affordance.

Effect. Under RL, `ex:s jsonschema:format "uri"` entails `ex:s a jsonschema:DataSchema` and not `jsonschema:StringSchema`.
Under RL on the generated set, the `k1` node of that sample is entailed to be a `td:InteractionAffordance` through the `rdfs:domain` of `td:name`; on the published set it is not.

Status. Undecided.

### td:supportContact has domain and range on an annotation property

Published. `td:supportContact a owl:AnnotationProperty .`

Generated. `td:supportContact a owl:AnnotationProperty ; rdfs:domain td:Thing ; rdfs:range xsd:anyURI .`

Effect. The owlrl RL and RDFS closures both entail `ex:t a td:Thing` for any subject of `td:supportContact`.

Status. Undecided.

### tm:optional, tm:required and tm:ref lose their domain

Published. `tm:optional` and `tm:required` have `schema:domainIncludes tm:ThingModel`; `tm:ref` has `schema:domainIncludes td:InteractionAffordance`; each has `schema:rangeIncludes schema:Text`.

Generated. Each has `rdfs:range xsd:string` and no domain.

Effect. Only the range entails; the link to the classes where these keys occur is no longer stated.

Status. Undecided.

### Labels are tagged @en and taken from the term IRI

Published. Labels are untagged literals, except `td:Thing` and the labels in `tm.ttl`, which carry `@en`. `td:schemaDefinitions`, `td:VersionInfo`, `wotsec:scheme`, `jsonschema:type` and the JSON Schema classes have no `rdfs:label`, nor do the Dublin Core, VANN and schema.org annotation properties declared in `tm.ttl`.

Generated. Every class, property and individual in a WoT namespace has a single `rdfs:label` tagged `@en`. Its text is the local name of the term IRI, except `wotsec:apikeyIn`, whose label is "in", as in the published ontology. Where the published ontology has a label, the text is the same.

Effect. No logical effect; label lookups by language succeed for every term.

Cause. Renaming the attribute in the LinkML schema while keeping its `slot_uri` left the label unchanged; changing the `slot_uri` changed the label. Removing `alias: in` from the `apikeyIn` attribute changed the label of `wotsec:apikeyIn` to "apikeyIn".

Status. Undecided.

### Term descriptions use skos:definition

Published. Terms are described with `rdfs:comment`, mostly tagged `@en`; some comments in td, hctl, wotsec and jsonschema are untagged.

Generated. Every class, property and individual in a WoT namespace is described with `skos:definition` tagged `@en`; `rdfs:comment` occurs only on the `owl:Ontology` node. Every class and property, but not the `td:OperationType` individuals, also carries `skos:inScheme` pointing to its module ontology.
No generated module contains `skos:exactMatch`. Raw `gen-owl` on `resources/schemas/thing_description.yaml` gives classes such as `td:Thing` and `wotsec:BasicSecurityScheme` a `skos:exactMatch` to their own IRI, and `jsonschema:Any` one to `linkml:Any`.
Every generated module declares `skos:definition` and `skos:inScheme` as annotation properties, and every one except `tm.ttl` also declares `skos:note` and `schema:domainIncludes`; the published modules declare none of these. Neither set declares `schema:rangeIncludes`.

Effect. Consumers that read `rdfs:comment` find no description on generated terms.

Status. Undecided.

### Description wording

Published. Comment texts are short and contain HTML markup in places.

Generated. Definition texts differ from the published comments for many terms in every module. The definition of `hctl:Link` contains markdown emphasis `**_..._**`.

Effect. No logical effect. Some published comments are wrong; see "Wrong or garbled published comments" in Part 2.

Status. Undecided.

### Editorial notes as skos:note

Published. No term has `skos:note`. The `rdfs:comment` of `wotsec:proxy`, `wotsec:qop` and `wotsec:scopes` contains the words "at risk".

Generated. Untagged `skos:note` literals are present on `td:OperationType` and some of its individuals, on `hctl:hasHreflang` and `hctl:hasRelationType`, on `wotsec:in` and `wotsec:oneOf`, on `wotsec:proxy`, `wotsec:qop` and `wotsec:scopes` with the text "This feature is at risk.", and on `jsonschema:allOf` with a note ending "confirm its inclusion with the WoT Working Group.".

Effect. No logical effect. The `jsonschema:allOf` note is internal process text inside a published vocabulary.

Status. Undecided.

### rdfs:isDefinedBy values

Published. In td, most terms have `rdfs:isDefinedBy <https://www.w3.org/2019/wot/td>`, the ontology IRI, and `td:hasNotificationResponseSchema` and `td:isSynchronous` have `td:`, the namespace IRI with `#`. In hctl, only `hctl:hasAdditionalOutputSchema` and `hctl:isSuccess` have it, with the namespace IRI `hctl:`. wotsec and jsonschema terms have none. In `tm.ttl`, TM terms point to `tm:` and the redeclared TD terms to `td:`.

Generated. Every term in a WoT namespace has `rdfs:isDefinedBy` pointing to its module ontology IRI, which has no trailing `#`.

Effect. No logical effect.

Status. Undecided.

### Missing rdfs:seeAlso on JSON Schema bounds

Published. `jsonschema:maximum` and `jsonschema:exclusiveMaximum` have `rdfs:seeAlso schema:maxValue`; `jsonschema:minimum` and `jsonschema:exclusiveMinimum` have `rdfs:seeAlso schema:minValue`.

Generated. None of these has `rdfs:seeAlso`.

Effect. No logical effect.

Status. Undecided.

### Ontology headers

Published. Ontology IRIs are `https://www.w3.org/2019/wot/td`, `https://www.w3.org/2019/wot/hypermedia#`, `https://www.w3.org/2019/wot/security#`, `https://www.w3.org/2019/wot/json-schema#` and `https://www.w3.org/2019/wot/tm`.
Every header has `vann:preferredNamespacePrefix` and `vann:preferredNamespaceUri`. Beyond that, metadata varies per module.
td has `dcterms:author`, `dcterms:contributor`, `dcterms:license`, a blank node `dcterms:publisher`, `dcterms:title` and an `rdfs:comment`, both tagged `@en`, `owl:versionInfo "0.9.0"` and no label.
hctl has `dcterms:creator`, an untagged `rdfs:comment` and the untagged label "Hypermedia Controls Ontology" with a no-break space between "Hypermedia" and "Controls"; it has no license, title or version.
wotsec has `dc:title`, `dcterms:creator`, `dcterms:contributor`, `dcterms:license` and `owl:versionInfo "0.0.1"`, and no comment or label.
jsonschema has an IRI `dc:publisher`, `dc:title`, `dcterms:creator`, `dcterms:license`, an `rdfs:comment` and `owl:versionInfo "0.6.0"`.
tm has a blank node `dc:publisher`, `dc:title`, `dcterms:author` literals, `dcterms:contributor`, `dcterms:description`, `dcterms:license`, an `rdfs:comment` and `owl:versionInfo "1.1.0"`.

Generated. All ontology IRIs end without `#`. Every header has the same shape: `dcterms:title`, `rdfs:label` and a single-sentence `rdfs:comment`, all tagged `@en`; `vann:preferredNamespacePrefix` and `vann:preferredNamespaceUri`; `dcterms:license <http://purl.org/NET/rdflicense/cc-by4.0>`; `dcterms:creator <mailto:mahda.noura@siemens.com>`; `dcterms:contributor` entries; a blank node `dcterms:publisher` typed `schema:Organization` with an untagged `schema:name` and a `schema:url`; and `owl:versionInfo "td-next"`.

Effect. The ontology IRI of hctl, wotsec and jsonschema no longer equals the term namespace with its `#`. The version and authorship statements differ from the published ones in every module.

Status. Undecided.

## Part 2: Defects in the published ontology

### td:schemaDefinitions is in the context but not in the ontology

Published. The published context maps `schemaDefinitions` to `td:schemaDefinitions` with `@type: @id`; `td.ttl` does not declare the term.

Generated. Declared; see the Part 1 entry.

Effect. Published instance data uses an undefined term.

Status. Published defect.

### td:VersionInfo is in the context but in no published ontology

Published. The published context maps `VersionInfo` to `td:VersionInfo`. No published module declares `td:VersionInfo`. `tm.ttl` declares a class `tm:Version`, which no context term maps to.

Generated. `td.ttl` declares `td:VersionInfo a owl:Class` as the range of `td:versionInfo`, and the generated context maps `VersionInfo` to it; see the Part 1 entry.

Effect. A TD that types its version object `VersionInfo` uses a class that no published ontology defines.

Status. Published defect.

### The version terms are declared twice, in td.ttl and in tm.ttl

Published. `td.ttl` declares `td:versionInfo` as `owl:AnnotationProperty`, and `td:instance` and `td:model` as `owl:DatatypeProperty` with `schema:domainIncludes td:versionInfo`.
`tm.ttl` declares `tm:versionInfo` as `owl:AnnotationProperty`, `tm:hasVersion` as `owl:ObjectProperty` from `tm:ThingModel` to `tm:Version`, the class `tm:Version`, and `tm:model` as `owl:DatatypeProperty` with `schema:domainIncludes tm:Version` and `schema:rangeIncludes schema:Text`.
`td:model` and `tm:model` have the same comment, "Provides a version indicator of the underlying TM.".
The published context maps `version`, `instance` and `model` to `td:versionInfo`, `td:instance` and `td:model`, and maps no term to the `tm:` version terms.

Generated. Only the `td:` terms are declared; see the Part 1 entries.

Effect. Two sets of terms with overlapping descriptions exist for version information, and the context reaches only the `td:` set, in which there is no version class.

Status. Published defect.

### td:versionInfo is an annotation property that the context maps with @type: @id

Published. `td.ttl` declares `td:versionInfo` as `owl:AnnotationProperty`. The published context maps `version` to `td:versionInfo` with `@type: @id`, and maps `instance` and `model` to the datatype properties `td:instance` and `td:model`.

Generated. `td:versionInfo` is an object property with range `td:VersionInfo`; the generated context maps `version` with `@type: @id` as well.

Effect. A TD with `"version": {"instance": "1.0.0", "model": "2.0.0"}` expanded with the published context gives `ex:t td:versionInfo _:v` and datatype property assertions on `_:v`. ROBOT reads the first triple as an annotation assertion and reports no profile violation for these triples; under RL on the published `td.ttl` they entail no type for either node.

Status. Published defect.

### Datatype properties whose values the context makes IRIs

Published. `hctl:hasAnchor` and `wotsec:proxy` are `owl:DatatypeProperty`, while the published context maps `anchor` and `proxy` with `@type: @id`.

Generated. Both are datatype properties with `rdfs:range xsd:anyURI`, and the generated context maps `anchor` and `proxy` with `@type: xsd:anyURI`, so their values are literals.

Effect. On the merged published modules plus `ex:l hctl:hasAnchor <http://a.example/>` and `ex:s wotsec:proxy <http://p.example/>`, ROBOT reports "Cannot pun between properties" for `hctl:hasAnchor` and `wotsec:proxy`, so expanded published instance data with these keys is outside OWL 2 DL.
On the merged generated modules plus `ex:l hctl:hasAnchor "http://a.example/"^^xsd:anyURI` and `ex:s wotsec:proxy "http://p.example/"^^xsd:anyURI`, the triples the generated context produces, ROBOT reports no violation on either property.

Status. Published defect.

### dcterms:description is both an annotation property and a super-property of datatype properties

Published. `tm.ttl` declares `dcterms:description` as `owl:AnnotationProperty`; `td.ttl` states `td:description rdfs:subPropertyOf dcterms:description` and `td:descriptionInLanguage rdfs:subPropertyOf dcterms:description`, where both sub-properties are datatype properties.

Generated. `td.ttl` declares `dcterms:description` as a datatype property; no module declares it as an annotation property.

Effect. On the merged published modules ROBOT reports "Cannot pun between properties" for `td:description` and `td:descriptionInLanguage`, so the published set is not in OWL 2 DL.

Status. Published defect.

### td:instance and td:model name a property as their domain

Published. `td:instance` and `td:model` have `schema:domainIncludes td:versionInfo`, which `td.ttl` declares as an annotation property, not a class. Neither has a range or `schema:rangeIncludes`.

Generated. Both have `rdfs:domain td:VersionInfo` and `rdfs:range xsd:string`.

Effect. ROBOT reads both statements as annotation assertions, so the defect has no logical effect. The published ontology names no class for the subject of `td:instance` and `td:model`.

Status. Published defect.

### tm.ttl makes every Thing a ThingModel

Published. `tm.ttl` states `td:hasInteractionAffordance rdfs:domain tm:ThingModel`, while `td.ttl` gives the same property `schema:domainIncludes td:Thing`.

Generated. `td:hasInteractionAffordance rdfs:domain td:Thing`, and `tm.ttl` does not redeclare it.

Effect. Under RL on the merged published modules, `ex:t td:hasPropertyAffordance ex:p` entails `ex:t a tm:ThingModel`; every Thing Description with an affordance becomes a Thing Model. The generated ontology entails `ex:t a td:Thing`.

Status. Published defect.

### jsonschema:pattern has an integer range

Published. `jsonschema:pattern rdfs:range xsd:nonNegativeInteger ; schema:domainIncludes jsonschema:StringSchema .` Pattern values are regular expressions such as `"^a$"`.

Generated. `jsonschema:pattern rdfs:domain jsonschema:StringSchema ; rdfs:range xsd:string .` Under RL, a pattern value entails `jsonschema:StringSchema` and `jsonschema:DataSchema` for its subject.

Effect. HermiT finds the published `jsonschema.ttl` plus `ex:s jsonschema:pattern "^a$"` inconsistent; the generated `jsonschema.ttl` plus the same triple is consistent.

Status. Published defect.

### Wrong or garbled published comments

Published. `td:invokeAction`, `td:readMultipleProperties`, `td:subscribeEvent`, `td:unsubscribeEvent` and `td:writeAllProperties` have the comment "Operation type of forms used to read a property value", and `td:writeMultipleProperties` has "Operation type of forms used to write a property value", the comments of `td:readProperty` and `td:writeProperty`. `td:unobserveAllProperties` has "Operation type of forms used to unobserve all property value".
`jsonschema:contentEncoding` cites "RFC 2054"; the TD 1.1 Recommendation cites RFC 2045 (Section 6.1) and RFC 4648.
`td:instance` says "version identicator"; `td:hasSecurityConfiguration` says "is a a security scheme".
`tm:ref` has `rdfs:seeAlso schema:contactPoint`.

Generated. The operation types have their own definitions, for example "Identifies the invoke operation on Action Affordances to perform the corresponding action." for `td:invokeAction`. `jsonschema:contentEncoding` cites "RFC 2045 (Section 6.1) and RFC 4648". `tm:ref` has no `rdfs:seeAlso`.

Effect. No logical effect. The human-readable documentation is wrong, and the `tm:ref` link points to a schema.org contact property unrelated to references.

Status. Published defect.

### rdfs:isDefinedBy uses both the ontology IRI and the namespace IRI

Published. `td.ttl` uses the ontology IRI `<https://www.w3.org/2019/wot/td>` for most terms and the namespace IRI `td:` for `td:hasNotificationResponseSchema` and `td:isSynchronous`.

Generated. A single value per module; see "rdfs:isDefinedBy values" in Part 1.

Effect. No logical effect. Terms of a single module point to different defining resources.

Status. Published defect.

### dcterms:author is not a DCMI term

Published. The td and tm headers use `dcterms:author`, and `tm.ttl` declares it as an annotation property; `td.ttl` uses it undeclared. The DCMI Metadata Terms vocabulary published at `http://purl.org/dc/terms/` defines `dcterms:creator` and `dcterms:contributor` and no `dcterms:author`.

Generated. Headers use `dcterms:creator` and `dcterms:contributor`.

Effect. No logical effect. The published authorship statements use a property that DCMI does not define.

Status. Published defect.

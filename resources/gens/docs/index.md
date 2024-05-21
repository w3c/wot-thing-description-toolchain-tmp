# thing-description-schema

LinkML schema for modelling the Web of Things Thing Description information model. This schema is used to generate
JSON Schema, SHACL shapes, and RDF.

URI: td

Name: thing-description-schema



## Classes

| Class | Description |
| --- | --- |
| [DataSchema](DataSchema.md) | Metadata that describes the data format used. It can be used for validation. |
| [ExpectedResponse](ExpectedResponse.md) | Communication metadata describing the expected response message for the primary response. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[AdditionalExpectedResponse](AdditionalExpectedResponse.md) | Communication metadata describing the expected response message for additional responses. |
| [Form](Form.md) | A form can be viewed as a statement of to perform an operation type on form context,  make a request method to submission target, where the optional form fields may further describe the required request. In Thing Descriptions, the form context is the surrounding Object,  such as Properties, Actions, and Events or the Thing itself for meta-interactions. |
| [InteractionAffordance](InteractionAffordance.md) | TOOD |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[ActionAffordance](ActionAffordance.md) | An Interaction Affordance that allows to invoke a function of the Thing, which manipulates state (e.g., toggling a lamp on or off) or triggers a process on the Thing (e.g., dim a lamp over time). |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[EventAffordance](EventAffordance.md) | An Interaction Affordance that describes an event source, which asynchronously pushes event data to Consumers (e.g., overhearing alerts). |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[PropertyAffordance](PropertyAffordance.md) | An Interaction Affordance that exposes state of the Thing. This state can be retrieved (read) and/or updated. |
| [Link](Link.md) | A link can be viewed as a statement of the form link context that has a relation type resource at link target", where the optional target attributes may further describe the resource. |
| [MultiLanguage](MultiLanguage.md) | None |
| [SecurityScheme](SecurityScheme.md) | None |
| [Thing](Thing.md) | An abstraction of a physical or a virtual entity whose metadata and interfaces are described by a WoT Thing Description, whereas a virtual entity is the composition of one or more Things. |
| [VersionInfo](VersionInfo.md) | Provides version information. |



## Slots

| Slot | Description |
| --- | --- |
| [@type](@type.md) |  |
| [actions](actions.md) | All Action-based interaction affordances of the Thing |
| [additionalOutputSchema](additionalOutputSchema.md) | This optional term can be used to define a data schema for an additional resp... |
| [additionalReturns](additionalReturns.md) | This optional term can be used if additional expected responses are possible,... |
| [anchor](anchor.md) | By default, the context, or anchor, of a link conveyed in the Link header fie... |
| [base](base.md) | Define the base URI that is used for all relative URI references throughout a... |
| [cancellation](cancellation.md) | Defines any data that needs to be passed to cancel a subscription, e |
| [contentCoding](contentCoding.md) | Content coding values indicate an encoding transformation that has been or ca... |
| [contentType](contentType.md) | TODO Check, was not in hctl ontology, if not could be source of discrepancy |
| [created](created.md) | Provides information when the TD instance was created |
| [description](description.md) |  |
| [descriptionInLanguage](descriptionInLanguage.md) | description of the TD element (Thing, interaction affordance, security scheme... |
| [descriptions](descriptions.md) | TODO, check, according to the description a description should not contain a ... |
| [events](events.md) | All Event-based interaction affordances of the Thing |
| [forms](forms.md) | Set of form hypermedia controls that describe how an operation can be perform... |
| [hintsAtMediaType](hintsAtMediaType.md) | Target attribute providing a hint indicating what the media type [IANA-MEDIA-... |
| [href](href.md) |  |
| [hreflang](hreflang.md) | The hreflang attribute specifies the language of a linked document |
| [id](id.md) | TODO |
| [idempotent](idempotent.md) | Indicates whether the action is idempotent (=true) or not |
| [input](input.md) | Used to define the input data schema of the action |
| [instance](instance.md) |  |
| [key](key.md) |  |
| [links](links.md) | Provides Web links to arbitrary resources that relate to the specified Thing ... |
| [model](model.md) |  |
| [modified](modified.md) | Provides information when the TD instance was last modified |
| [name](name.md) | Indexing property to store entity names when serializing them in a JSON-LD @i... |
| [notification](notification.md) | Defines the data schema of the Event instance messages pushed by the Thing |
| [notificationResponse](notificationResponse.md) | Defines the data schema of the Event response messages sent by the consumer i... |
| [observable](observable.md) | A hint that indicates whether Servients hosting the Thing and Intermediaries ... |
| [operationType](operationType.md) | Indicates the semantic intention of performing the operation(s) described by ... |
| [output](output.md) | Used to define the output data schema of the action |
| [profile](profile.md) | Indicates the WoT Profile mechanisms followed by this Thing Description and t... |
| [properties](properties.md) | All Property-based interaction affordances of the Thing |
| [propertyName](propertyName.md) | Used to store the indexing name in the parent object when this schema appears... |
| [proxy](proxy.md) | URI of the proxy server this security configuration provides access to |
| [readonly](readonly.md) | Boolean value that is a hint to indicate whether a property interaction/value... |
| [relation](relation.md) | A link relation type identifies the semantics of a link |
| [returns](returns.md) | This optional term can be used if, e |
| [safe](safe.md) | Signals if the action is safe (=true) or not |
| [schema](schema.md) | TODO Check, was not in hctl ontology, if not could be source of discrepancy |
| [schemaDefinitions](schemaDefinitions.md) | TODO CHECK |
| [scheme](scheme.md) |  |
| [scopes](scopes.md) | TODO Check, was not in hctl ontology, if not could be source of discrepancy |
| [security](security.md) | A Thing may define abstract security schemes, used to configure the secure ac... |
| [securityDefinitions](securityDefinitions.md) | A security schema applied to a (set of) affordance(s) |
| [sizes](sizes.md) | Target attribute that specifies one or more sizes for the referenced icon |
| [subprotocol](subprotocol.md) | Indicates the exact mechanism by which an interaction will be accomplished fo... |
| [subscription](subscription.md) | Defines data that needs to be passed upon subscription, e |
| [success](success.md) | Signals if the additional response should not be considered an error |
| [supportContact](supportContact.md) | Provides information about the TD maintainer as URI scheme (e |
| [synchronous](synchronous.md) | Indicates whether the action is synchronous (=true) or not |
| [target](target.md) | Target IRI of a link or submission target of a Form |
| [title](title.md) | Provides a human-readable title (e |
| [titleInLanguage](titleInLanguage.md) | title of the TD element (Thing, interaction affordance, security scheme or da... |
| [titles](titles.md) |  |
| [type](type.md) |  |
| [uriVariables](uriVariables.md) | Define URI template variables according to RFC6570 as collection based on sch... |
| [version](version.md) |  |
| [writeOnly](writeOnly.md) | Boolean value that is a hint to indicate whether a property interaction/value... |


## Enumerations

| Enumeration | Description |
| --- | --- |
| [OperationTypes](OperationTypes.md) | Enumerations of well-known operation types necessary to implement the WoT int... |
| [SecuritySchemeType](SecuritySchemeType.md) |  |


## Types

| Type | Description |
| --- | --- |
| [AnyUri](AnyUri.md) | a complete URI |
| [Boolean](Boolean.md) | A binary (true or false) value |
| [Curie](Curie.md) | a compact URI |
| [Date](Date.md) | a date (year, month and day) in an idealized calendar |
| [DateOrDatetime](DateOrDatetime.md) | Either a date or a datetime |
| [Datetime](Datetime.md) | The combination of a date and time |
| [Decimal](Decimal.md) | A real number with arbitrary precision that conforms to the xsd:decimal speci... |
| [Double](Double.md) | A real number that conforms to the xsd:double specification |
| [Float](Float.md) | A real number that conforms to the xsd:float specification |
| [Integer](Integer.md) | An integer |
| [Jsonpath](Jsonpath.md) | A string encoding a JSON Path |
| [Jsonpointer](Jsonpointer.md) | A string encoding a JSON Pointer |
| [Ncname](Ncname.md) | Prefix part of CURIE |
| [Nodeidentifier](Nodeidentifier.md) | A URI, CURIE or BNODE that represents a node in a model |
| [Objectidentifier](Objectidentifier.md) | A URI or CURIE that represents an object in the model |
| [Sparqlpath](Sparqlpath.md) | A string encoding a SPARQL Property Path |
| [String](String.md) | A character string |
| [Time](Time.md) | A time object represents a (local) time of day, independent of any particular... |
| [Uri](Uri.md) | a complete URI |
| [Uriorcurie](Uriorcurie.md) | a URI or a CURIE |


## Subsets

| Subset | Description |
| --- | --- |

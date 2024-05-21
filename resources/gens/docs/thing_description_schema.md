
# thing-description-schema


**metamodel version:** 1.7.0

**version:** None


LinkML schema for modelling the Web of Things Thing Description information model. This schema is used to generate
JSON Schema, SHACL shapes, and RDF.


### Classes

 * [DataSchema](DataSchema.md) - Metadata that describes the data format used. It can be used for validation.
 * [ExpectedResponse](ExpectedResponse.md) - Communication metadata describing the expected response message for the primary response.
     * [AdditionalExpectedResponse](AdditionalExpectedResponse.md) - Communication metadata describing the expected response message for additional responses.
 * [Form](Form.md) - A form can be viewed as a statement of to perform an operation type on form context,  make a request method to submission target, where the optional form fields may further describe the required request. In Thing Descriptions, the form context is the surrounding Object,  such as Properties, Actions, and Events or the Thing itself for meta-interactions.
 * [InteractionAffordance](InteractionAffordance.md) - TOOD
     * [ActionAffordance](ActionAffordance.md) - An Interaction Affordance that allows to invoke a function of the Thing, which manipulates state (e.g., toggling a lamp on or off) or triggers a process on the Thing (e.g., dim a lamp over time).
     * [EventAffordance](EventAffordance.md) - An Interaction Affordance that describes an event source, which asynchronously pushes event data to Consumers (e.g., overhearing alerts).
     * [PropertyAffordance](PropertyAffordance.md) - An Interaction Affordance that exposes state of the Thing. This state can be retrieved (read) and/or updated.
 * [Link](Link.md) - A link can be viewed as a statement of the form link context that has a relation type resource at link target", where the optional target attributes may further describe the resource.
 * [MultiLanguage](MultiLanguage.md)
 * [SecurityScheme](SecurityScheme.md)
 * [Thing](Thing.md) - An abstraction of a physical or a virtual entity whose metadata and interfaces are described by a WoT Thing Description, whereas a virtual entity is the composition of one or more Things.
 * [VersionInfo](VersionInfo.md) - Provides version information.

### Mixins


### Slots

 * [@type](@type.md)
 * [➞idempotent](actionAffordance__idempotent.md) - Indicates whether the action is idempotent (=true) or not. Informs whether the action can be called repeatedly with the same results, if present, based on the same input.
 * [➞input](actionAffordance__input.md) - Used to define the input data schema of the action.
 * [➞output](actionAffordance__output.md) - Used to define the output data schema of the action.
 * [➞safe](actionAffordance__safe.md) - Signals if the action is safe (=true) or not. Used to signal if there is no internal state (cf. resource state) is changed when invoking an Action.
 * [➞synchronous](actionAffordance__synchronous.md) - Indicates whether the action is synchronous (=true) or not. A synchronous action means that the response of action contains all the information about the result of the action and no further querying about the status of the action is needed. Lack of this keyword means that no claim on the synchronicity of the action can be made.
 * [➞additionalOutputSchema](additionalExpectedResponse__additionalOutputSchema.md) - This optional term can be used to define a data schema for an additional response if it differs from the default output data schema. Rather than a DataSchema object, the name of a previous definition given in a SchemaDefinitions map must be used.
 * [➞schema](additionalExpectedResponse__schema.md) - TODO Check, was not in hctl ontology, if not could be source of discrepancy
 * [➞success](additionalExpectedResponse__success.md) - Signals if the additional response should not be considered an error.
 * [➞propertyName](dataSchema__propertyName.md) - Used to store the indexing name in the parent object when this schema appears as a property of an object schema.
 * [➞readonly](dataSchema__readonly.md) - Boolean value that is a hint to indicate whether a property interaction/value is read only (=true) or not (=false).
 * [➞writeOnly](dataSchema__writeOnly.md) - Boolean value that is a hint to indicate whether a property interaction/value is write only (=true) or not (=false).
 * [description](description.md)
 * [descriptionInLanguage](descriptionInLanguage.md) - description of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
 * [descriptions](descriptions.md) - TODO, check, according to the description a description should not contain a lang tag.
 * [➞cancellation](eventAffordance__cancellation.md) - Defines any data that needs to be passed to cancel a subscription, e.g., a specific message to remove a Webhook.
 * [➞notification](eventAffordance__notification.md) - Defines the data schema of the Event instance messages pushed by the Thing.
 * [➞notificationResponse](eventAffordance__notificationResponse.md) - Defines the data schema of the Event response messages sent by the consumer in a response to a data message.
 * [➞subscription](eventAffordance__subscription.md) - Defines data that needs to be passed upon subscription, e.g., filters or message format for setting up Webhooks.
 * [➞contentType](expectedResponse__contentType.md) - TODO Check, was not in hctl ontology, if not could be source of discrepancy
 * [➞additionalReturns](form__additionalReturns.md) - This optional term can be used if additional expected responses are possible, e.g. for error reporting. Each additional response needs to be distinguished from others in some way (for example, by specifying a protocol-specific response code), and may also have its own data schema.
 * [➞contentCoding](form__contentCoding.md) - Content coding values indicate an encoding transformation that has been or can be applied to a representation.  Content codings are primarily used to allow a representation to be compressed or otherwise usefully transformed  without losing the identity of its underlying media type and without loss of information. Examples of content coding include \"gzip\", \"deflate\", etc.
 * [➞contentType](form__contentType.md) - Assign a content type based on a media type IANA-MEDIA-TYPES (e.g., 'text/plain') and potential parameters  (e.g., 'charset=utf-8') for the media type.
 * [➞href](form__href.md)
 * [➞operationType](form__operationType.md) - Indicates the semantic intention of performing the operation(s) described by the form.
 * [➞returns](form__returns.md) - This optional term can be used if, e.g., the output communication metadata differ from input metadata (e.g., output contentType differ from the input contentType). The response name contains metadata that is only valid for the response messages.
 * [➞scopes](form__scopes.md) - TODO Check, was not in hctl ontology, if not could be source of discrepancy
 * [➞securityDefinitions](form__securityDefinitions.md) - A security schema applied to a (set of) affordance(s).
 * [➞subprotocol](form__subprotocol.md) - Indicates the exact mechanism by which an interaction will be accomplished for a given protocol when there are multiple options.
 * [id](id.md) - TODO
 * [➞forms](interactionAffordance__forms.md) - Set of form hypermedia controls that describe how an operation can be performed.
 * [➞name](interactionAffordance__name.md) - Indexing property to store entity names when serializing them in a JSON-LD @index container.
 * [➞uriVariables](interactionAffordance__uriVariables.md) - Define URI template variables according to RFC6570 as collection based on schema specifications. The individual variables DataSchema cannot be an ObjectSchema or an ArraySchema. TODO: range is not obvious from the ontology.
 * [➞anchor](link__anchor.md) - By default, the context, or anchor, of a link conveyed in the Link header field is the URL of the representation it is associated with, as defined in RFC7231, Section 3.1.4.1, and is serialized as a URI.
 * [➞hintsAtMediaType](link__hintsAtMediaType.md) - Target attribute providing a hint indicating what the media type [IANA-MEDIA-TYPES] of the result of dereferencing the link should be.
 * [➞hreflang](link__hreflang.md) - The hreflang attribute specifies the language of a linked document. The value of this must be a valid language tag [[BCP47]].
 * [➞relation](link__relation.md) - A link relation type identifies the semantics of a link.
 * [➞sizes](link__sizes.md) - Target attribute that specifies one or more sizes for the referenced icon. Only applicable for relation type 'icon'. The value pattern follows {Height}x{Width} (e.g., \"16x16\", \"16x16 32x32\").
 * [➞type](link__type.md)
 * [➞key](multiLanguage__key.md)
 * [➞observable](propertyAffordance__observable.md) - A hint that indicates whether Servients hosting the Thing and Intermediaries should probide a Protocol Binding  that supports the observeproperty and unobserveproperty operations for this Property.
 * [➞description](securityScheme__description.md)
 * [➞proxy](securityScheme__proxy.md) - URI of the proxy server this security configuration provides access to. If not given, the corresponding security configuration is for the endpoint.
 * [➞scheme](securityScheme__scheme.md)
 * [target](target.md) - Target IRI of a link or submission target of a Form
 * [➞actions](thing__actions.md) - All Action-based interaction affordances of the Thing.
 * [➞base](thing__base.md) - Define the base URI that is used for all relative URI references throughout a TD document.
 * [➞created](thing__created.md) - Provides information when the TD instance was created.
 * [➞events](thing__events.md) - All Event-based interaction affordances of the Thing.
 * [➞forms](thing__forms.md) - Set of form hypermedia controls that describe how an operation can be performed. Forms are serializations of Protocol Bindings.
 * [➞instance](thing__instance.md) - Provides a version identicator of this TD instance.
 * [➞links](thing__links.md) - Provides Web links to arbitrary resources that relate to the specified Thing Description.
 * [➞modified](thing__modified.md) - Provides information when the TD instance was last modified.
 * [➞profile](thing__profile.md) - Indicates the WoT Profile mechanisms followed by this Thing Description and the corresponding Thing implementation.
 * [➞properties](thing__properties.md) - All Property-based interaction affordances of the Thing.
 * [➞schemaDefinitions](thing__schemaDefinitions.md) - TODO CHECK
 * [➞security](thing__security.md) - A Thing may define abstract security schemes, used to configure the secure access of (a set of) affordance(s). TODO: check
 * [➞securityDefinitions](thing__securityDefinitions.md) - A security scheme applied to a (set of) affordance(s). TODO check
 * [➞supportContact](thing__supportContact.md) - Provides information about the TD maintainer as URI scheme (e.g., <code>mailto</code> [[RFC6068]],<code>tel</code> [[RFC3966]],<code>https</code> [[RFC9112]]).
 * [➞version](thing__version.md)
 * [title](title.md) - Provides a human-readable title (e.g., display a text for UI representation) based on a default language.
 * [titleInLanguage](titleInLanguage.md) - title of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
 * [titles](titles.md)
 * [➞instance](versionInfo__instance.md)
 * [➞model](versionInfo__model.md)

### Enums

 * [OperationTypes](OperationTypes.md) - Enumerations of well-known operation types necessary to implement the WoT interaction model.
 * [SecuritySchemeType](SecuritySchemeType.md)

### Subsets


### Types


#### Built in

 * **Bool**
 * **Curie**
 * **Decimal**
 * **ElementIdentifier**
 * **NCName**
 * **NodeIdentifier**
 * **URI**
 * **URIorCURIE**
 * **XSDDate**
 * **XSDDateTime**
 * **XSDTime**
 * **float**
 * **int**
 * **str**

#### Defined

 * [AnyUri](types/AnyUri.md)  (**URI**)  - a complete URI
 * [Boolean](types/Boolean.md)  (**Bool**)  - A binary (true or false) value
 * [Curie](types/Curie.md)  (**Curie**)  - a compact URI
 * [Date](types/Date.md)  (**XSDDate**)  - a date (year, month and day) in an idealized calendar
 * [DateOrDatetime](types/DateOrDatetime.md)  (**str**)  - Either a date or a datetime
 * [Datetime](types/Datetime.md)  (**XSDDateTime**)  - The combination of a date and time
 * [Decimal](types/Decimal.md)  (**Decimal**)  - A real number with arbitrary precision that conforms to the xsd:decimal specification
 * [Double](types/Double.md)  (**float**)  - A real number that conforms to the xsd:double specification
 * [Float](types/Float.md)  (**float**)  - A real number that conforms to the xsd:float specification
 * [Integer](types/Integer.md)  (**int**)  - An integer
 * [Jsonpath](types/Jsonpath.md)  (**str**)  - A string encoding a JSON Path. The value of the string MUST conform to JSON Point syntax and SHOULD dereference to zero or more valid objects within the current instance document when encoded in tree form.
 * [Jsonpointer](types/Jsonpointer.md)  (**str**)  - A string encoding a JSON Pointer. The value of the string MUST conform to JSON Point syntax and SHOULD dereference to a valid object within the current instance document when encoded in tree form.
 * [Ncname](types/Ncname.md)  (**NCName**)  - Prefix part of CURIE
 * [Nodeidentifier](types/Nodeidentifier.md)  (**NodeIdentifier**)  - A URI, CURIE or BNODE that represents a node in a model.
 * [Objectidentifier](types/Objectidentifier.md)  (**ElementIdentifier**)  - A URI or CURIE that represents an object in the model.
 * [Sparqlpath](types/Sparqlpath.md)  (**str**)  - A string encoding a SPARQL Property Path. The value of the string MUST conform to SPARQL syntax and SHOULD dereference to zero or more valid objects within the current instance document when encoded as RDF.
 * [String](types/String.md)  (**str**)  - A character string
 * [Time](types/Time.md)  (**XSDTime**)  - A time object represents a (local) time of day, independent of any particular day
 * [Uri](types/Uri.md)  (**URI**)  - a complete URI
 * [Uriorcurie](types/Uriorcurie.md)  (**URIorCURIE**)  - a URI or a CURIE


# thing-description-schema


**metamodel version:** 1.7.0

**version:** None


LinkML schema for modelling the W3C Web of Things Thing Description information model. This schema is used to generate
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

# Type: anyUri

a complete URI

URI: [td:AnyUri](https://www.w3.org/2019/wot/td#AnyUri)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **URI** |

# Type: boolean

A binary (true or false) value

URI: [linkml:Boolean](https://w3id.org/linkml/Boolean)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **Bool** |
| Representation | | bool |

## Other properties

|  |  |  |
| --- | --- | --- |
| **Exact Mappings:** | | schema:Boolean |

# Type: curie

a compact URI

URI: [linkml:Curie](https://w3id.org/linkml/Curie)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **Curie** |
| Representation | | str |

## Other properties

|  |  |  |
| --- | --- | --- |
| **Comments:** | | in RDF serializations this MUST be expanded to a URI |
|  | | in non-RDF serializations MAY be serialized as the compact representation |

# Type: date

a date (year, month and day) in an idealized calendar

URI: [linkml:Date](https://w3id.org/linkml/Date)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **XSDDate** |
| Representation | | str |

## Other properties

|  |  |  |
| --- | --- | --- |
| **Exact Mappings:** | | schema:Date |

# Type: date_or_datetime

Either a date or a datetime

URI: [linkml:DateOrDatetime](https://w3id.org/linkml/DateOrDatetime)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **str** |
| Representation | | str |

# Type: datetime

The combination of a date and time

URI: [linkml:Datetime](https://w3id.org/linkml/Datetime)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **XSDDateTime** |
| Representation | | str |

## Other properties

|  |  |  |
| --- | --- | --- |
| **Exact Mappings:** | | schema:DateTime |

# Type: decimal

A real number with arbitrary precision that conforms to the xsd:decimal specification

URI: [linkml:Decimal](https://w3id.org/linkml/Decimal)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **Decimal** |

## Other properties

|  |  |  |
| --- | --- | --- |
| **Broad Mappings:** | | schema:Number |

# Type: double

A real number that conforms to the xsd:double specification

URI: [linkml:Double](https://w3id.org/linkml/Double)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **float** |

## Other properties

|  |  |  |
| --- | --- | --- |
| **Close Mappings:** | | schema:Float |

# Type: float

A real number that conforms to the xsd:float specification

URI: [linkml:Float](https://w3id.org/linkml/Float)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **float** |

## Other properties

|  |  |  |
| --- | --- | --- |
| **Exact Mappings:** | | schema:Float |

# Type: integer

An integer

URI: [linkml:Integer](https://w3id.org/linkml/Integer)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **int** |

## Other properties

|  |  |  |
| --- | --- | --- |
| **Exact Mappings:** | | schema:Integer |

# Type: jsonpath

A string encoding a JSON Path. The value of the string MUST conform to JSON Point syntax and SHOULD dereference to zero or more valid objects within the current instance document when encoded in tree form.

URI: [linkml:Jsonpath](https://w3id.org/linkml/Jsonpath)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **str** |
| Representation | | str |

# Type: jsonpointer

A string encoding a JSON Pointer. The value of the string MUST conform to JSON Point syntax and SHOULD dereference to a valid object within the current instance document when encoded in tree form.

URI: [linkml:Jsonpointer](https://w3id.org/linkml/Jsonpointer)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **str** |
| Representation | | str |

# Type: ncname

Prefix part of CURIE

URI: [linkml:Ncname](https://w3id.org/linkml/Ncname)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **NCName** |
| Representation | | str |

# Type: nodeidentifier

A URI, CURIE or BNODE that represents a node in a model.

URI: [linkml:Nodeidentifier](https://w3id.org/linkml/Nodeidentifier)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **NodeIdentifier** |
| Representation | | str |

# Type: objectidentifier

A URI or CURIE that represents an object in the model.

URI: [linkml:Objectidentifier](https://w3id.org/linkml/Objectidentifier)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **ElementIdentifier** |
| Representation | | str |

## Other properties

|  |  |  |
| --- | --- | --- |
| **Comments:** | | Used for inheritance and type checking |

# Type: sparqlpath

A string encoding a SPARQL Property Path. The value of the string MUST conform to SPARQL syntax and SHOULD dereference to zero or more valid objects within the current instance document when encoded as RDF.

URI: [linkml:Sparqlpath](https://w3id.org/linkml/Sparqlpath)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **str** |
| Representation | | str |

# Type: string

A character string

URI: [linkml:String](https://w3id.org/linkml/String)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **str** |

## Other properties

|  |  |  |
| --- | --- | --- |
| **Exact Mappings:** | | schema:Text |

# Type: time

A time object represents a (local) time of day, independent of any particular day

URI: [linkml:Time](https://w3id.org/linkml/Time)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **XSDTime** |
| Representation | | str |

## Other properties

|  |  |  |
| --- | --- | --- |
| **Exact Mappings:** | | schema:Time |

# Type: uri

a complete URI

URI: [linkml:Uri](https://w3id.org/linkml/Uri)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **URI** |
| Representation | | str |

## Other properties

|  |  |  |
| --- | --- | --- |
| **Comments:** | | in RDF serializations a slot with range of uri is treated as a literal or type xsd:anyURI unless it is an identifier or a reference to an identifier, in which case it is translated directly to a node |
| **Close Mappings:** | | schema:URL |

# Type: uriorcurie

a URI or a CURIE

URI: [linkml:Uriorcurie](https://w3id.org/linkml/Uriorcurie)

|  |  |  |
| --- | --- | --- |
| Root (builtin) type | | **URIorCURIE** |
| Representation | | str |

# Enum: OperationTypes

Enumerations of well-known operation types necessary to implement the WoT interaction model.

URI: [td:OperationTypes](https://www.w3.org/2019/wot/td#OperationTypes)


## Permissible Values

| Text | Description | Meaning | Other Information |
| :--- | :---: | :---: | ---: |
| readproperty | Identifies the read operation on Property Affordances to retrieve the corresponding data. | td:readProperty |  |
| writeproperty | Identifies the write operation on Property Affordances to update the corresponding data. | td:writeProperty |  |
| observeproperty | Identifies the observe operation on Property Affordances to be notified with the new data when the Property is updated. | td:observeProperty |  |
| unobserveproperty | Identifies the unobserve operation on Property Affordances to stop the corresponding notifications. | td:unobserveProperty |  |
| invokeaction | Identifies the invoke operation on Action Affordances to perform the corresponding action. | td:invokeAction |  |
| queryaction | Identifies the querying operation on Action Affordances to get the status of the corresponding action. | td:queryAction |  |
| cancelaction | Identifies the cancel operation on Action Affordances to cancel the ongoing corresponding action. | td:cancelAction |  |
| subscribeevent | Identifies the subscribe operation on Event Affordances to be notified by the Thing when the event occurs. | td:subscribeEvent |  |
| unsubscribeevent | Identifies the unsubscribe operation on Event Affordances to stop the corresponding notifications. | td:unsubscribeEvent |  |
| readallproperties | Identifies the readallproperties operation on a Thing to retrieve the data of all Properties in a single interaction. | td:readAllProperties |  |
| writeallproperties | Identifies the writeallproperties operation on a Thing to update the data of all writable Properties in a single interaction. | writeAllProperties |  |
| readmultipleproperties | Identifies the readmultipleproperties operation on a Thing to retrieve the data of selected Properties in a single interaction. | td:readMultipleProperties |  |
| writemultipleproperties | Identifies the writemultipleproperties operation on a Thing to update the data of selected writable Properties in a single interaction. | td:writeMultipleProperties |  |
| observeallproperties | Identifies the observeallproperties operation on Properties to be notified with new data when any Property is updated. | td:observeAllProperties |  |
| unobserveallproperties | Identifies the unobserveallproperties operation on Properties to stop notifications from all Properties in a single interaction. | td:unobserveAllProperties |  |
| subscribeallevents | Identifies the subscribeallevents operation on Events to subscribe to notifications from all Events in a single interaction. | td:subscribeAllEvents |  |
| unsubscribeallevents | Identifies the unsubscribeallevents operation on Events to unsubscribe from notifications from all Events in a single interaction. | td:unsubscribeAllEvents |  |
| queryallactions | Identifies the queryallactions operation on a Thing to get the status of all Actions in a single interaction. | td:queryAllActions |  |


# Enum: SecuritySchemeType



URI: [td:SecuritySchemeType](https://www.w3.org/2019/wot/td#SecuritySchemeType)


## Permissible Values

| Text | Description | Meaning | Other Information |
| :--- | :---: | :---: | ---: |
| nosec | A security configuration corresponding to identified by the Vocabulary Term nosec, indicating there is no authentication or other mechanism required to access the resource. | wotsec:NoSecurityScheme |  |
| combo | Elements of this scheme define various ways in which other named schemes defined in securityDefinitions, including other ComboSecurityScheme definitions, are to be combined to create a new scheme definition. | wotsec:ComboSecurityScheme |  |
| basic | Uses an unencrypted username and password. | wotsec:BasicSecurityScheme |  |
| digest | This scheme is similar to basic authentication but with added features to avoid man-in-the-middle attacks. | wotsec:DigestSecurityScheme |  |
| bearer | Bearer tokens are used independently of OAuth2. | wotsec:BearerSecurityScheme |  |
| psk | This is meant to identify that a standard is used for pre-shared keys such as TLS-PSK [RFC4279], and that the ciphersuite used for keys will be established during protocol negotiation. | wotsec:PSKSecurityScheme |  |
| oauth2 | OAuth 2.0 authentication security configuration for systems conformant with [RFC6749] and [RFC8252]. | wotsec:OAuth2SecurityScheme |  |
| apikey | This scheme is to be used when the access token is opaque. | wotsec:APIKeySecurityScheme |  |
| auto | This scheme indicates that the security parameters are going to be negotiated by the underlying protocols at runtime | wotsec:AutoSecurityScheme |  |


# Slot: @type



URI: [td:@type](https://www.w3.org/2019/wot/td#@type)


## Domain and Range

None &#8594;  <sub>0..\*</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [SecurityScheme](SecurityScheme.md)
 * [Thing](Thing.md)

# Slot: idempotent

Indicates whether the action is idempotent (=true) or not. Informs whether the action can be called repeatedly with the same results, if present, based on the same input.

URI: [td:actionAffordance__idempotent](https://www.w3.org/2019/wot/td#actionAffordance__idempotent)


## Domain and Range

None &#8594;  <sub>0..1</sub> [Boolean](types/Boolean.md)

## Parents


## Children


## Used by

 * [ActionAffordance](ActionAffordance.md)

# Slot: input

Used to define the input data schema of the action.

URI: [td:actionAffordance__input](https://www.w3.org/2019/wot/td#actionAffordance__input)


## Domain and Range

None &#8594;  <sub>0..1</sub> [DataSchema](DataSchema.md)

## Parents


## Children


## Used by

 * [ActionAffordance](ActionAffordance.md)

# Slot: output

Used to define the output data schema of the action.

URI: [td:actionAffordance__output](https://www.w3.org/2019/wot/td#actionAffordance__output)


## Domain and Range

None &#8594;  <sub>0..1</sub> [DataSchema](DataSchema.md)

## Parents


## Children


## Used by

 * [ActionAffordance](ActionAffordance.md)

# Slot: safe

Signals if the action is safe (=true) or not. Used to signal if there is no internal state (cf. resource state) is changed when invoking an Action.

URI: [td:actionAffordance__safe](https://www.w3.org/2019/wot/td#actionAffordance__safe)


## Domain and Range

None &#8594;  <sub>0..1</sub> [Boolean](types/Boolean.md)

## Parents


## Children


## Used by

 * [ActionAffordance](ActionAffordance.md)

# Slot: synchronous

Indicates whether the action is synchronous (=true) or not. A synchronous action means that the response of action contains all the information about the result of the action and no further querying about the status of the action is needed. Lack of this keyword means that no claim on the synchronicity of the action can be made.

URI: [td:actionAffordance__synchronous](https://www.w3.org/2019/wot/td#actionAffordance__synchronous)


## Domain and Range

None &#8594;  <sub>0..1</sub> [Boolean](types/Boolean.md)

## Parents


## Children


## Used by

 * [ActionAffordance](ActionAffordance.md)

# Slot: additionalOutputSchema

This optional term can be used to define a data schema for an additional response if it differs from the default output data schema. Rather than a DataSchema object, the name of a previous definition given in a SchemaDefinitions map must be used.

URI: [td:additionalExpectedResponse__additionalOutputSchema](https://www.w3.org/2019/wot/td#additionalExpectedResponse__additionalOutputSchema)


## Domain and Range

None &#8594;  <sub>0..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [AdditionalExpectedResponse](AdditionalExpectedResponse.md)

# Slot: schema

TODO Check, was not in hctl ontology, if not could be source of discrepancy

URI: [td:additionalExpectedResponse__schema](https://www.w3.org/2019/wot/td#additionalExpectedResponse__schema)


## Domain and Range

None &#8594;  <sub>0..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [AdditionalExpectedResponse](AdditionalExpectedResponse.md)

# Slot: success

Signals if the additional response should not be considered an error.

URI: [td:additionalExpectedResponse__success](https://www.w3.org/2019/wot/td#additionalExpectedResponse__success)


## Domain and Range

None &#8594;  <sub>0..1</sub> [Boolean](types/Boolean.md)

## Parents


## Children


## Used by

 * [AdditionalExpectedResponse](AdditionalExpectedResponse.md)

# Slot: propertyName

Used to store the indexing name in the parent object when this schema appears as a property of an object schema.

URI: [td:dataSchema__propertyName](https://www.w3.org/2019/wot/td#dataSchema__propertyName)


## Domain and Range

None &#8594;  <sub>0..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [DataSchema](DataSchema.md)
 * [PropertyAffordance](PropertyAffordance.md)

# Slot: readonly

Boolean value that is a hint to indicate whether a property interaction/value is read only (=true) or not (=false).

URI: [td:dataSchema__readonly](https://www.w3.org/2019/wot/td#dataSchema__readonly)


## Domain and Range

None &#8594;  <sub>0..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [DataSchema](DataSchema.md)
 * [PropertyAffordance](PropertyAffordance.md)

# Slot: writeOnly

Boolean value that is a hint to indicate whether a property interaction/value is write only (=true) or not (=false).

URI: [td:dataSchema__writeOnly](https://www.w3.org/2019/wot/td#dataSchema__writeOnly)


## Domain and Range

None &#8594;  <sub>0..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [DataSchema](DataSchema.md)
 * [PropertyAffordance](PropertyAffordance.md)

# Slot: description



URI: [td:description](https://www.w3.org/2019/wot/td#description)


## Domain and Range

None &#8594;  <sub>0..1</sub> [MultiLanguage](MultiLanguage.md)

## Parents


## Children


## Used by

 * [ActionAffordance](ActionAffordance.md)
 * [DataSchema](DataSchema.md)
 * [EventAffordance](EventAffordance.md)
 * [InteractionAffordance](InteractionAffordance.md)
 * [PropertyAffordance](PropertyAffordance.md)
 * [Thing](Thing.md)

# Slot: descriptionInLanguage

description of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.

URI: [td:descriptionInLanguage](https://www.w3.org/2019/wot/td#descriptionInLanguage)


## Domain and Range

None &#8594;  <sub>0..1</sub> [MultiLanguage](MultiLanguage.md)

## Parents


## Children


## Used by

 * [ActionAffordance](ActionAffordance.md)
 * [DataSchema](DataSchema.md)
 * [EventAffordance](EventAffordance.md)
 * [InteractionAffordance](InteractionAffordance.md)
 * [PropertyAffordance](PropertyAffordance.md)
 * [Thing](Thing.md)

# Slot: descriptions

TODO, check, according to the description a description should not contain a lang tag.

URI: [td:descriptions](https://www.w3.org/2019/wot/td#descriptions)


## Domain and Range

None &#8594;  <sub>0..\*</sub> [MultiLanguage](MultiLanguage.md)

## Parents


## Children


## Used by

 * [ActionAffordance](ActionAffordance.md)
 * [EventAffordance](EventAffordance.md)
 * [InteractionAffordance](InteractionAffordance.md)
 * [PropertyAffordance](PropertyAffordance.md)
 * [SecurityScheme](SecurityScheme.md)
 * [Thing](Thing.md)

# Slot: cancellation

Defines any data that needs to be passed to cancel a subscription, e.g., a specific message to remove a Webhook.

URI: [td:eventAffordance__cancellation](https://www.w3.org/2019/wot/td#eventAffordance__cancellation)


## Domain and Range

None &#8594;  <sub>0..1</sub> [DataSchema](DataSchema.md)

## Parents


## Children


## Used by

 * [EventAffordance](EventAffordance.md)

# Slot: notification

Defines the data schema of the Event instance messages pushed by the Thing.

URI: [td:eventAffordance__notification](https://www.w3.org/2019/wot/td#eventAffordance__notification)


## Domain and Range

None &#8594;  <sub>0..1</sub> [DataSchema](DataSchema.md)

## Parents


## Children


## Used by

 * [EventAffordance](EventAffordance.md)

# Slot: notificationResponse

Defines the data schema of the Event response messages sent by the consumer in a response to a data message.

URI: [td:eventAffordance__notificationResponse](https://www.w3.org/2019/wot/td#eventAffordance__notificationResponse)


## Domain and Range

None &#8594;  <sub>0..1</sub> [DataSchema](DataSchema.md)

## Parents


## Children


## Used by

 * [EventAffordance](EventAffordance.md)

# Slot: subscription

Defines data that needs to be passed upon subscription, e.g., filters or message format for setting up Webhooks.

URI: [td:eventAffordance__subscription](https://www.w3.org/2019/wot/td#eventAffordance__subscription)


## Domain and Range

None &#8594;  <sub>0..1</sub> [DataSchema](DataSchema.md)

## Parents


## Children


## Used by

 * [EventAffordance](EventAffordance.md)

# Slot: contentType

TODO Check, was not in hctl ontology, if not could be source of discrepancy

URI: [td:expectedResponse__contentType](https://www.w3.org/2019/wot/td#expectedResponse__contentType)


## Domain and Range

None &#8594;  <sub>1..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [AdditionalExpectedResponse](AdditionalExpectedResponse.md)
 * [ExpectedResponse](ExpectedResponse.md)

# Slot: additionalReturns

This optional term can be used if additional expected responses are possible, e.g. for error reporting. Each additional response needs to be distinguished from others in some way (for example, by specifying a protocol-specific response code), and may also have its own data schema.

URI: [td:form__additionalReturns](https://www.w3.org/2019/wot/td#form__additionalReturns)


## Domain and Range

None &#8594;  <sub>0..\*</sub> [AdditionalExpectedResponse](AdditionalExpectedResponse.md)

## Parents


## Children


## Used by

 * [Form](Form.md)

# Slot: contentCoding

Content coding values indicate an encoding transformation that has been or can be applied to a representation.  Content codings are primarily used to allow a representation to be compressed or otherwise usefully transformed  without losing the identity of its underlying media type and without loss of information. Examples of content coding include \"gzip\", \"deflate\", etc.

URI: [td:form__contentCoding](https://www.w3.org/2019/wot/td#form__contentCoding)


## Domain and Range

None &#8594;  <sub>0..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [Form](Form.md)

# Slot: contentType

Assign a content type based on a media type IANA-MEDIA-TYPES (e.g., 'text/plain') and potential parameters  (e.g., 'charset=utf-8') for the media type.

URI: [td:form__contentType](https://www.w3.org/2019/wot/td#form__contentType)


## Domain and Range

None &#8594;  <sub>0..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [Form](Form.md)

# Slot: href



URI: [td:form__href](https://www.w3.org/2019/wot/td#form__href)


## Domain and Range

None &#8594;  <sub>1..1</sub> [AnyUri](types/AnyUri.md)

## Parents


## Children


## Used by

 * [Form](Form.md)

# Slot: operationType

Indicates the semantic intention of performing the operation(s) described by the form.

URI: [td:form__operationType](https://www.w3.org/2019/wot/td#form__operationType)


## Domain and Range

None &#8594;  <sub>0..\*</sub> [OperationTypes](OperationTypes.md)

## Parents


## Children


## Used by

 * [Form](Form.md)

# Slot: returns

This optional term can be used if, e.g., the output communication metadata differ from input metadata (e.g., output contentType differ from the input contentType). The response name contains metadata that is only valid for the response messages.

URI: [td:form__returns](https://www.w3.org/2019/wot/td#form__returns)


## Domain and Range

None &#8594;  <sub>0..1</sub> [ExpectedResponse](ExpectedResponse.md)

## Parents


## Children


## Used by

 * [Form](Form.md)

# Slot: scopes

TODO Check, was not in hctl ontology, if not could be source of discrepancy

URI: [td:form__scopes](https://www.w3.org/2019/wot/td#form__scopes)


## Domain and Range

None &#8594;  <sub>0..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [Form](Form.md)

# Slot: securityDefinitions

A security schema applied to a (set of) affordance(s).

URI: [td:form__securityDefinitions](https://www.w3.org/2019/wot/td#form__securityDefinitions)


## Domain and Range

None &#8594;  <sub>0..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [Form](Form.md)

# Slot: subprotocol

Indicates the exact mechanism by which an interaction will be accomplished for a given protocol when there are multiple options.

URI: [td:form__subprotocol](https://www.w3.org/2019/wot/td#form__subprotocol)


## Domain and Range

None &#8594;  <sub>0..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [Form](Form.md)

# Slot: id

TODO

URI: [td:id](https://www.w3.org/2019/wot/td#id)


## Domain and Range

None &#8594;  <sub>1..1</sub> [AnyUri](types/AnyUri.md)

## Parents


## Children


## Used by

 * [Thing](Thing.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Mappings:** | | td:id |
# Slot: forms

Set of form hypermedia controls that describe how an operation can be performed.

URI: [td:interactionAffordance__forms](https://www.w3.org/2019/wot/td#interactionAffordance__forms)


## Domain and Range

None &#8594;  <sub>0..\*</sub> [Form](Form.md)

## Parents


## Children


## Used by

 * [ActionAffordance](ActionAffordance.md)
 * [EventAffordance](EventAffordance.md)
 * [InteractionAffordance](InteractionAffordance.md)
 * [PropertyAffordance](PropertyAffordance.md)

# Slot: name

Indexing property to store entity names when serializing them in a JSON-LD @index container.

URI: [td:interactionAffordance__name](https://www.w3.org/2019/wot/td#interactionAffordance__name)


## Domain and Range

None &#8594;  <sub>1..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [ActionAffordance](ActionAffordance.md)
 * [EventAffordance](EventAffordance.md)
 * [InteractionAffordance](InteractionAffordance.md)
 * [PropertyAffordance](PropertyAffordance.md)

# Slot: uriVariables

Define URI template variables according to RFC6570 as collection based on schema specifications. The individual variables DataSchema cannot be an ObjectSchema or an ArraySchema. TODO: range is not obvious from the ontology.

URI: [td:interactionAffordance__uriVariables](https://www.w3.org/2019/wot/td#interactionAffordance__uriVariables)


## Domain and Range

None &#8594;  <sub>0..\*</sub> [DataSchema](DataSchema.md)

## Parents


## Children


## Used by

 * [ActionAffordance](ActionAffordance.md)
 * [EventAffordance](EventAffordance.md)
 * [InteractionAffordance](InteractionAffordance.md)
 * [PropertyAffordance](PropertyAffordance.md)

# Slot: anchor

By default, the context, or anchor, of a link conveyed in the Link header field is the URL of the representation it is associated with, as defined in RFC7231, Section 3.1.4.1, and is serialized as a URI.

URI: [td:link__anchor](https://www.w3.org/2019/wot/td#link__anchor)


## Domain and Range

None &#8594;  <sub>0..1</sub> [AnyUri](types/AnyUri.md)

## Parents


## Children


## Used by

 * [Link](Link.md)

# Slot: hintsAtMediaType

Target attribute providing a hint indicating what the media type [IANA-MEDIA-TYPES] of the result of dereferencing the link should be.

URI: [td:link__hintsAtMediaType](https://www.w3.org/2019/wot/td#link__hintsAtMediaType)


## Domain and Range

None &#8594;  <sub>0..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [Link](Link.md)

# Slot: hreflang

The hreflang attribute specifies the language of a linked document. The value of this must be a valid language tag [[BCP47]].

URI: [td:link__hreflang](https://www.w3.org/2019/wot/td#link__hreflang)


## Domain and Range

None &#8594;  <sub>0..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [Link](Link.md)

# Slot: relation

A link relation type identifies the semantics of a link.

URI: [td:link__relation](https://www.w3.org/2019/wot/td#link__relation)


## Domain and Range

None &#8594;  <sub>0..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [Link](Link.md)

# Slot: sizes

Target attribute that specifies one or more sizes for the referenced icon. Only applicable for relation type 'icon'. The value pattern follows {Height}x{Width} (e.g., \"16x16\", \"16x16 32x32\").

URI: [td:link__sizes](https://www.w3.org/2019/wot/td#link__sizes)


## Domain and Range

None &#8594;  <sub>0..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [Link](Link.md)

# Slot: type



URI: [td:link__type](https://www.w3.org/2019/wot/td#link__type)


## Domain and Range

None &#8594;  <sub>0..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [Link](Link.md)

# Slot: key



URI: [td:multiLanguage__key](https://www.w3.org/2019/wot/td#multiLanguage__key)


## Domain and Range

None &#8594;  <sub>1..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [MultiLanguage](MultiLanguage.md)

# Slot: observable

A hint that indicates whether Servients hosting the Thing and Intermediaries should probide a Protocol Binding  that supports the observeproperty and unobserveproperty operations for this Property.

URI: [td:propertyAffordance__observable](https://www.w3.org/2019/wot/td#propertyAffordance__observable)


## Domain and Range

None &#8594;  <sub>0..1</sub> [Boolean](types/Boolean.md)

## Parents


## Children


## Used by

 * [PropertyAffordance](PropertyAffordance.md)

# Slot: description



URI: [td:securityScheme__description](https://www.w3.org/2019/wot/td#securityScheme__description)


## Domain and Range

None &#8594;  <sub>0..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [SecurityScheme](SecurityScheme.md)

# Slot: proxy

URI of the proxy server this security configuration provides access to. If not given, the corresponding security configuration is for the endpoint.

URI: [td:securityScheme__proxy](https://www.w3.org/2019/wot/td#securityScheme__proxy)


## Domain and Range

None &#8594;  <sub>0..1</sub> [AnyUri](types/AnyUri.md)

## Parents


## Children


## Used by

 * [SecurityScheme](SecurityScheme.md)

# Slot: scheme



URI: [td:securityScheme__scheme](https://www.w3.org/2019/wot/td#securityScheme__scheme)


## Domain and Range

None &#8594;  <sub>1..1</sub> [SecuritySchemeType](SecuritySchemeType.md)

## Parents


## Children


## Used by

 * [SecurityScheme](SecurityScheme.md)

# Slot: target

Target IRI of a link or submission target of a Form

URI: [td:target](https://www.w3.org/2019/wot/td#target)


## Domain and Range

None &#8594;  <sub>1..1</sub> [AnyUri](types/AnyUri.md)

## Parents


## Children


## Used by

 * [Form](Form.md)
 * [Link](Link.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Mappings:** | | hctl:target |
# Slot: actions

All Action-based interaction affordances of the Thing.

URI: [td:thing__actions](https://www.w3.org/2019/wot/td#thing__actions)


## Domain and Range

None &#8594;  <sub>0..\*</sub> [ActionAffordance](ActionAffordance.md)

## Parents


## Children


## Used by

 * [Thing](Thing.md)

# Slot: base

Define the base URI that is used for all relative URI references throughout a TD document.

URI: [td:thing__base](https://www.w3.org/2019/wot/td#thing__base)


## Domain and Range

None &#8594;  <sub>0..1</sub> [AnyUri](types/AnyUri.md)

## Parents


## Children


## Used by

 * [Thing](Thing.md)

# Slot: created

Provides information when the TD instance was created.

URI: [td:thing__created](https://www.w3.org/2019/wot/td#thing__created)


## Domain and Range

None &#8594;  <sub>0..1</sub> [Datetime](types/Datetime.md)

## Parents


## Children


## Used by

 * [Thing](Thing.md)

# Slot: events

All Event-based interaction affordances of the Thing.

URI: [td:thing__events](https://www.w3.org/2019/wot/td#thing__events)


## Domain and Range

None &#8594;  <sub>0..\*</sub> [EventAffordance](EventAffordance.md)

## Parents


## Children


## Used by

 * [Thing](Thing.md)

# Slot: forms

Set of form hypermedia controls that describe how an operation can be performed. Forms are serializations of Protocol Bindings.

URI: [td:thing__forms](https://www.w3.org/2019/wot/td#thing__forms)


## Domain and Range

None &#8594;  <sub>0..\*</sub> [Form](Form.md)

## Parents


## Children


## Used by

 * [Thing](Thing.md)

# Slot: instance

Provides a version identicator of this TD instance.

URI: [td:thing__instance](https://www.w3.org/2019/wot/td#thing__instance)


## Domain and Range

None &#8594;  <sub>0..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [Thing](Thing.md)

# Slot: links

Provides Web links to arbitrary resources that relate to the specified Thing Description.

URI: [td:thing__links](https://www.w3.org/2019/wot/td#thing__links)


## Domain and Range

None &#8594;  <sub>0..\*</sub> [Link](Link.md)

## Parents


## Children


## Used by

 * [Thing](Thing.md)

# Slot: modified

Provides information when the TD instance was last modified.

URI: [td:thing__modified](https://www.w3.org/2019/wot/td#thing__modified)


## Domain and Range

None &#8594;  <sub>0..1</sub> [Datetime](types/Datetime.md)

## Parents


## Children


## Used by

 * [Thing](Thing.md)

# Slot: profile

Indicates the WoT Profile mechanisms followed by this Thing Description and the corresponding Thing implementation.

URI: [td:thing__profile](https://www.w3.org/2019/wot/td#thing__profile)


## Domain and Range

None &#8594;  <sub>0..\*</sub> [AnyUri](types/AnyUri.md)

## Parents


## Children


## Used by

 * [Thing](Thing.md)

# Slot: properties

All Property-based interaction affordances of the Thing.

URI: [td:thing__properties](https://www.w3.org/2019/wot/td#thing__properties)


## Domain and Range

None &#8594;  <sub>0..\*</sub> [PropertyAffordance](PropertyAffordance.md)

## Parents


## Children


## Used by

 * [Thing](Thing.md)

# Slot: schemaDefinitions

TODO CHECK

URI: [td:thing__schemaDefinitions](https://www.w3.org/2019/wot/td#thing__schemaDefinitions)


## Domain and Range

None &#8594;  <sub>0..\*</sub> [DataSchema](DataSchema.md)

## Parents


## Children


## Used by

 * [Thing](Thing.md)

# Slot: security

A Thing may define abstract security schemes, used to configure the secure access of (a set of) affordance(s). TODO: check

URI: [td:thing__security](https://www.w3.org/2019/wot/td#thing__security)


## Domain and Range

None &#8594;  <sub>0..\*</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [Thing](Thing.md)

# Slot: securityDefinitions

A security scheme applied to a (set of) affordance(s). TODO check

URI: [td:thing__securityDefinitions](https://www.w3.org/2019/wot/td#thing__securityDefinitions)


## Domain and Range

None &#8594;  <sub>0..\*</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [Thing](Thing.md)

# Slot: supportContact

Provides information about the TD maintainer as URI scheme (e.g., <code>mailto</code> [[RFC6068]],<code>tel</code> [[RFC3966]],<code>https</code> [[RFC9112]]).

URI: [td:thing__supportContact](https://www.w3.org/2019/wot/td#thing__supportContact)


## Domain and Range

None &#8594;  <sub>0..1</sub> [AnyUri](types/AnyUri.md)

## Parents


## Children


## Used by

 * [Thing](Thing.md)

# Slot: version



URI: [td:thing__version](https://www.w3.org/2019/wot/td#thing__version)


## Domain and Range

None &#8594;  <sub>0..1</sub> [VersionInfo](VersionInfo.md)

## Parents


## Children


## Used by

 * [Thing](Thing.md)

# Slot: title

Provides a human-readable title (e.g., display a text for UI representation) based on a default language.

URI: [td:title](https://www.w3.org/2019/wot/td#title)


## Domain and Range

None &#8594;  <sub>0..1</sub> [MultiLanguage](MultiLanguage.md)

## Parents


## Children


## Used by

 * [ActionAffordance](ActionAffordance.md)
 * [DataSchema](DataSchema.md)
 * [EventAffordance](EventAffordance.md)
 * [InteractionAffordance](InteractionAffordance.md)
 * [PropertyAffordance](PropertyAffordance.md)
 * [Thing](Thing.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Mappings:** | | td:title |
# Slot: titleInLanguage

title of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.

URI: [td:titleInLanguage](https://www.w3.org/2019/wot/td#titleInLanguage)


## Domain and Range

None &#8594;  <sub>0..1</sub> [MultiLanguage](MultiLanguage.md)

## Parents


## Children


## Used by

 * [ActionAffordance](ActionAffordance.md)
 * [DataSchema](DataSchema.md)
 * [EventAffordance](EventAffordance.md)
 * [InteractionAffordance](InteractionAffordance.md)
 * [PropertyAffordance](PropertyAffordance.md)
 * [Thing](Thing.md)

# Slot: titles



URI: [td:titles](https://www.w3.org/2019/wot/td#titles)


## Domain and Range

None &#8594;  <sub>0..\*</sub> [MultiLanguage](MultiLanguage.md)

## Parents


## Children


## Used by

 * [ActionAffordance](ActionAffordance.md)
 * [EventAffordance](EventAffordance.md)
 * [InteractionAffordance](InteractionAffordance.md)
 * [PropertyAffordance](PropertyAffordance.md)
 * [Thing](Thing.md)

# Slot: instance



URI: [td:versionInfo__instance](https://www.w3.org/2019/wot/td#versionInfo__instance)


## Domain and Range

None &#8594;  <sub>1..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [VersionInfo](VersionInfo.md)

# Slot: model



URI: [td:versionInfo__model](https://www.w3.org/2019/wot/td#versionInfo__model)


## Domain and Range

None &#8594;  <sub>0..1</sub> [String](types/String.md)

## Parents


## Children


## Used by

 * [VersionInfo](VersionInfo.md)

# Class: ActionAffordance

An Interaction Affordance that allows to invoke a function of the Thing, which manipulates state (e.g., toggling a lamp on or off) or triggers a process on the Thing (e.g., dim a lamp over time).

URI: [td:ActionAffordance](https://www.w3.org/2019/wot/td#ActionAffordance)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[MultiLanguage],[InteractionAffordance],[Form],[DataSchema],[DataSchema]<output%200..1-++[ActionAffordance&#124;safe:boolean%20%3F;synchronous:boolean%20%3F;idempotent:boolean%20%3F;name(i):string],[DataSchema]<input%200..1-++[ActionAffordance],[Thing]++-%20actions%200..*>[ActionAffordance],[InteractionAffordance]^-[ActionAffordance],[Thing])](https://yuml.me/diagram/nofunky;dir:TB/class/[MultiLanguage],[InteractionAffordance],[Form],[DataSchema],[DataSchema]<output%200..1-++[ActionAffordance&#124;safe:boolean%20%3F;synchronous:boolean%20%3F;idempotent:boolean%20%3F;name(i):string],[DataSchema]<input%200..1-++[ActionAffordance],[Thing]++-%20actions%200..*>[ActionAffordance],[InteractionAffordance]^-[ActionAffordance],[Thing])

## Parents

 *  is_a: [InteractionAffordance](InteractionAffordance.md) - TOOD

## Referenced by Class

 *  **None** *[➞actions](thing__actions.md)*  <sub>0..\*</sub>  **[ActionAffordance](ActionAffordance.md)**

## Attributes


### Own

 * [➞safe](actionAffordance__safe.md)  <sub>0..1</sub>
     * Description: Signals if the action is safe (=true) or not. Used to signal if there is no internal state (cf. resource state) is changed when invoking an Action.
     * Range: [Boolean](types/Boolean.md)
 * [➞synchronous](actionAffordance__synchronous.md)  <sub>0..1</sub>
     * Description: Indicates whether the action is synchronous (=true) or not. A synchronous action means that the response of action contains all the information about the result of the action and no further querying about the status of the action is needed. Lack of this keyword means that no claim on the synchronicity of the action can be made.
     * Range: [Boolean](types/Boolean.md)
 * [➞idempotent](actionAffordance__idempotent.md)  <sub>0..1</sub>
     * Description: Indicates whether the action is idempotent (=true) or not. Informs whether the action can be called repeatedly with the same results, if present, based on the same input.
     * Range: [Boolean](types/Boolean.md)
 * [➞input](actionAffordance__input.md)  <sub>0..1</sub>
     * Description: Used to define the input data schema of the action.
     * Range: [DataSchema](DataSchema.md)
 * [➞output](actionAffordance__output.md)  <sub>0..1</sub>
     * Description: Used to define the output data schema of the action.
     * Range: [DataSchema](DataSchema.md)

### Inherited from InteractionAffordance:

 * [titles](titles.md)  <sub>0..\*</sub>
     * Range: [MultiLanguage](MultiLanguage.md)
 * [descriptions](descriptions.md)  <sub>0..\*</sub>
     * Description: TODO, check, according to the description a description should not contain a lang tag.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [title](title.md)  <sub>0..1</sub>
     * Description: Provides a human-readable title (e.g., display a text for UI representation) based on a default language.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [description](description.md)  <sub>0..1</sub>
     * Range: [MultiLanguage](MultiLanguage.md)
 * [titleInLanguage](titleInLanguage.md)  <sub>0..1</sub>
     * Description: title of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [descriptionInLanguage](descriptionInLanguage.md)  <sub>0..1</sub>
     * Description: description of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [➞name](interactionAffordance__name.md)  <sub>1..1</sub>
     * Description: Indexing property to store entity names when serializing them in a JSON-LD @index container.
     * Range: [String](types/String.md)
 * [➞uriVariables](interactionAffordance__uriVariables.md)  <sub>0..\*</sub>
     * Description: Define URI template variables according to RFC6570 as collection based on schema specifications. The individual variables DataSchema cannot be an ObjectSchema or an ArraySchema. TODO: range is not obvious from the ontology.
     * Range: [DataSchema](DataSchema.md)
 * [➞forms](interactionAffordance__forms.md)  <sub>0..\*</sub>
     * Description: Set of form hypermedia controls that describe how an operation can be performed.
     * Range: [Form](Form.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Mappings:** | | td:ActionAffordance |
# Class: AdditionalExpectedResponse

Communication metadata describing the expected response message for additional responses.

URI: [td:AdditionalExpectedResponse](https://www.w3.org/2019/wot/td#AdditionalExpectedResponse)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[ExpectedResponse],[Form]++-%20additionalReturns%200..*>[AdditionalExpectedResponse&#124;additionalOutputSchema:string%20%3F;success:boolean%20%3F;schema:string%20%3F;contentType(i):string],[ExpectedResponse]^-[AdditionalExpectedResponse],[Form])](https://yuml.me/diagram/nofunky;dir:TB/class/[ExpectedResponse],[Form]++-%20additionalReturns%200..*>[AdditionalExpectedResponse&#124;additionalOutputSchema:string%20%3F;success:boolean%20%3F;schema:string%20%3F;contentType(i):string],[ExpectedResponse]^-[AdditionalExpectedResponse],[Form])

## Parents

 *  is_a: [ExpectedResponse](ExpectedResponse.md) - Communication metadata describing the expected response message for the primary response.

## Referenced by Class

 *  **None** *[➞additionalReturns](form__additionalReturns.md)*  <sub>0..\*</sub>  **[AdditionalExpectedResponse](AdditionalExpectedResponse.md)**

## Attributes


### Own

 * [➞additionalOutputSchema](additionalExpectedResponse__additionalOutputSchema.md)  <sub>0..1</sub>
     * Description: This optional term can be used to define a data schema for an additional response if it differs from the default output data schema. Rather than a DataSchema object, the name of a previous definition given in a SchemaDefinitions map must be used.
     * Range: [String](types/String.md)
 * [➞success](additionalExpectedResponse__success.md)  <sub>0..1</sub>
     * Description: Signals if the additional response should not be considered an error.
     * Range: [Boolean](types/Boolean.md)
 * [➞schema](additionalExpectedResponse__schema.md)  <sub>0..1</sub>
     * Description: TODO Check, was not in hctl ontology, if not could be source of discrepancy
     * Range: [String](types/String.md)

### Inherited from ExpectedResponse:

 * [➞contentType](expectedResponse__contentType.md)  <sub>1..1</sub>
     * Description: TODO Check, was not in hctl ontology, if not could be source of discrepancy
     * Range: [String](types/String.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Mappings:** | | hctl:AdditionalExpectedResponse |
# Class: DataSchema

Metadata that describes the data format used. It can be used for validation.

URI: [td:DataSchema](https://www.w3.org/2019/wot/td#DataSchema)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[MultiLanguage],[MultiLanguage]<descriptionInLanguage%200..1-%20[DataSchema&#124;propertyName:string%20%3F;writeOnly:string%20%3F;readonly:string%20%3F],[MultiLanguage]<titleInLanguage%200..1-%20[DataSchema],[MultiLanguage]<title%200..1-%20[DataSchema],[MultiLanguage]<description%200..1-%20[DataSchema],[ActionAffordance]++-%20input%200..1>[DataSchema],[ActionAffordance]++-%20output%200..1>[DataSchema],[EventAffordance]++-%20cancellation%200..1>[DataSchema],[EventAffordance]++-%20notification%200..1>[DataSchema],[EventAffordance]++-%20notificationResponse%200..1>[DataSchema],[EventAffordance]++-%20subscription%200..1>[DataSchema],[InteractionAffordance]++-%20uriVariables%200..*>[DataSchema],[Thing]++-%20schemaDefinitions%200..*>[DataSchema],[PropertyAffordance]uses%20-.->[DataSchema],[Thing],[PropertyAffordance],[InteractionAffordance],[EventAffordance],[ActionAffordance])](https://yuml.me/diagram/nofunky;dir:TB/class/[MultiLanguage],[MultiLanguage]<descriptionInLanguage%200..1-%20[DataSchema&#124;propertyName:string%20%3F;writeOnly:string%20%3F;readonly:string%20%3F],[MultiLanguage]<titleInLanguage%200..1-%20[DataSchema],[MultiLanguage]<title%200..1-%20[DataSchema],[MultiLanguage]<description%200..1-%20[DataSchema],[ActionAffordance]++-%20input%200..1>[DataSchema],[ActionAffordance]++-%20output%200..1>[DataSchema],[EventAffordance]++-%20cancellation%200..1>[DataSchema],[EventAffordance]++-%20notification%200..1>[DataSchema],[EventAffordance]++-%20notificationResponse%200..1>[DataSchema],[EventAffordance]++-%20subscription%200..1>[DataSchema],[InteractionAffordance]++-%20uriVariables%200..*>[DataSchema],[Thing]++-%20schemaDefinitions%200..*>[DataSchema],[PropertyAffordance]uses%20-.->[DataSchema],[Thing],[PropertyAffordance],[InteractionAffordance],[EventAffordance],[ActionAffordance])

## Mixin for

 * [PropertyAffordance](PropertyAffordance.md) (mixin)  - An Interaction Affordance that exposes state of the Thing. This state can be retrieved (read) and/or updated.

## Referenced by Class

 *  **None** *[➞input](actionAffordance__input.md)*  <sub>0..1</sub>  **[DataSchema](DataSchema.md)**
 *  **None** *[➞output](actionAffordance__output.md)*  <sub>0..1</sub>  **[DataSchema](DataSchema.md)**
 *  **None** *[➞cancellation](eventAffordance__cancellation.md)*  <sub>0..1</sub>  **[DataSchema](DataSchema.md)**
 *  **None** *[➞notification](eventAffordance__notification.md)*  <sub>0..1</sub>  **[DataSchema](DataSchema.md)**
 *  **None** *[➞notificationResponse](eventAffordance__notificationResponse.md)*  <sub>0..1</sub>  **[DataSchema](DataSchema.md)**
 *  **None** *[➞subscription](eventAffordance__subscription.md)*  <sub>0..1</sub>  **[DataSchema](DataSchema.md)**
 *  **None** *[➞uriVariables](interactionAffordance__uriVariables.md)*  <sub>0..\*</sub>  **[DataSchema](DataSchema.md)**
 *  **None** *[➞schemaDefinitions](thing__schemaDefinitions.md)*  <sub>0..\*</sub>  **[DataSchema](DataSchema.md)**

## Attributes


### Own

 * [description](description.md)  <sub>0..1</sub>
     * Range: [MultiLanguage](MultiLanguage.md)
 * [title](title.md)  <sub>0..1</sub>
     * Description: Provides a human-readable title (e.g., display a text for UI representation) based on a default language.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [titleInLanguage](titleInLanguage.md)  <sub>0..1</sub>
     * Description: title of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [descriptionInLanguage](descriptionInLanguage.md)  <sub>0..1</sub>
     * Description: description of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [➞propertyName](dataSchema__propertyName.md)  <sub>0..1</sub>
     * Description: Used to store the indexing name in the parent object when this schema appears as a property of an object schema.
     * Range: [String](types/String.md)
 * [➞writeOnly](dataSchema__writeOnly.md)  <sub>0..1</sub>
     * Description: Boolean value that is a hint to indicate whether a property interaction/value is write only (=true) or not (=false).
     * Range: [String](types/String.md)
 * [➞readonly](dataSchema__readonly.md)  <sub>0..1</sub>
     * Description: Boolean value that is a hint to indicate whether a property interaction/value is read only (=true) or not (=false).
     * Range: [String](types/String.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Mappings:** | | jsonschema:DataSchema |
# Class: EventAffordance

An Interaction Affordance that describes an event source, which asynchronously pushes event data to Consumers (e.g., overhearing alerts).

URI: [td:EventAffordance](https://www.w3.org/2019/wot/td#EventAffordance)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[MultiLanguage],[InteractionAffordance],[Form],[DataSchema]<notificationResponse%200..1-++[EventAffordance&#124;name(i):string],[DataSchema]<notification%200..1-++[EventAffordance],[DataSchema]<cancellation%200..1-++[EventAffordance],[DataSchema]<subscription%200..1-++[EventAffordance],[Thing]++-%20events%200..*>[EventAffordance],[InteractionAffordance]^-[EventAffordance],[Thing],[DataSchema])](https://yuml.me/diagram/nofunky;dir:TB/class/[MultiLanguage],[InteractionAffordance],[Form],[DataSchema]<notificationResponse%200..1-++[EventAffordance&#124;name(i):string],[DataSchema]<notification%200..1-++[EventAffordance],[DataSchema]<cancellation%200..1-++[EventAffordance],[DataSchema]<subscription%200..1-++[EventAffordance],[Thing]++-%20events%200..*>[EventAffordance],[InteractionAffordance]^-[EventAffordance],[Thing],[DataSchema])

## Parents

 *  is_a: [InteractionAffordance](InteractionAffordance.md) - TOOD

## Referenced by Class

 *  **None** *[➞events](thing__events.md)*  <sub>0..\*</sub>  **[EventAffordance](EventAffordance.md)**

## Attributes


### Own

 * [➞subscription](eventAffordance__subscription.md)  <sub>0..1</sub>
     * Description: Defines data that needs to be passed upon subscription, e.g., filters or message format for setting up Webhooks.
     * Range: [DataSchema](DataSchema.md)
 * [➞cancellation](eventAffordance__cancellation.md)  <sub>0..1</sub>
     * Description: Defines any data that needs to be passed to cancel a subscription, e.g., a specific message to remove a Webhook.
     * Range: [DataSchema](DataSchema.md)
 * [➞notification](eventAffordance__notification.md)  <sub>0..1</sub>
     * Description: Defines the data schema of the Event instance messages pushed by the Thing.
     * Range: [DataSchema](DataSchema.md)
 * [➞notificationResponse](eventAffordance__notificationResponse.md)  <sub>0..1</sub>
     * Description: Defines the data schema of the Event response messages sent by the consumer in a response to a data message.
     * Range: [DataSchema](DataSchema.md)

### Inherited from InteractionAffordance:

 * [titles](titles.md)  <sub>0..\*</sub>
     * Range: [MultiLanguage](MultiLanguage.md)
 * [descriptions](descriptions.md)  <sub>0..\*</sub>
     * Description: TODO, check, according to the description a description should not contain a lang tag.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [title](title.md)  <sub>0..1</sub>
     * Description: Provides a human-readable title (e.g., display a text for UI representation) based on a default language.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [description](description.md)  <sub>0..1</sub>
     * Range: [MultiLanguage](MultiLanguage.md)
 * [titleInLanguage](titleInLanguage.md)  <sub>0..1</sub>
     * Description: title of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [descriptionInLanguage](descriptionInLanguage.md)  <sub>0..1</sub>
     * Description: description of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [➞name](interactionAffordance__name.md)  <sub>1..1</sub>
     * Description: Indexing property to store entity names when serializing them in a JSON-LD @index container.
     * Range: [String](types/String.md)
 * [➞uriVariables](interactionAffordance__uriVariables.md)  <sub>0..\*</sub>
     * Description: Define URI template variables according to RFC6570 as collection based on schema specifications. The individual variables DataSchema cannot be an ObjectSchema or an ArraySchema. TODO: range is not obvious from the ontology.
     * Range: [DataSchema](DataSchema.md)
 * [➞forms](interactionAffordance__forms.md)  <sub>0..\*</sub>
     * Description: Set of form hypermedia controls that describe how an operation can be performed.
     * Range: [Form](Form.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Mappings:** | | td:EventAffordance |
# Class: ExpectedResponse

Communication metadata describing the expected response message for the primary response.

URI: [td:ExpectedResponse](https://www.w3.org/2019/wot/td#ExpectedResponse)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[Form]++-%20returns%200..1>[ExpectedResponse&#124;contentType:string],[ExpectedResponse]^-[AdditionalExpectedResponse],[Form],[AdditionalExpectedResponse])](https://yuml.me/diagram/nofunky;dir:TB/class/[Form]++-%20returns%200..1>[ExpectedResponse&#124;contentType:string],[ExpectedResponse]^-[AdditionalExpectedResponse],[Form],[AdditionalExpectedResponse])

## Children

 * [AdditionalExpectedResponse](AdditionalExpectedResponse.md) - Communication metadata describing the expected response message for additional responses.

## Referenced by Class

 *  **None** *[➞returns](form__returns.md)*  <sub>0..1</sub>  **[ExpectedResponse](ExpectedResponse.md)**

## Attributes


### Own

 * [➞contentType](expectedResponse__contentType.md)  <sub>1..1</sub>
     * Description: TODO Check, was not in hctl ontology, if not could be source of discrepancy
     * Range: [String](types/String.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Mappings:** | | hctl:ExpectedResponse |
# Class: Form

A form can be viewed as a statement of to perform an operation type on form context,  make a request method to submission target, where the optional form fields may further describe the required request. In Thing Descriptions, the form context is the surrounding Object,  such as Properties, Actions, and Events or the Thing itself for meta-interactions.

URI: [td:Form](https://www.w3.org/2019/wot/td#Form)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[AdditionalExpectedResponse]<additionalReturns%200..*-++[Form&#124;target:anyUri;href:anyUri;contentType:string%20%3F;contentCoding:string%20%3F;securityDefinitions:string%20%3F;scopes:string%20%3F;subprotocol:string%20%3F;operationType:OperationTypes%20*],[ExpectedResponse]<returns%200..1-++[Form],[InteractionAffordance]++-%20forms%200..*>[Form],[Thing]++-%20forms%200..*>[Form],[Thing],[InteractionAffordance],[ExpectedResponse],[AdditionalExpectedResponse])](https://yuml.me/diagram/nofunky;dir:TB/class/[AdditionalExpectedResponse]<additionalReturns%200..*-++[Form&#124;target:anyUri;href:anyUri;contentType:string%20%3F;contentCoding:string%20%3F;securityDefinitions:string%20%3F;scopes:string%20%3F;subprotocol:string%20%3F;operationType:OperationTypes%20*],[ExpectedResponse]<returns%200..1-++[Form],[InteractionAffordance]++-%20forms%200..*>[Form],[Thing]++-%20forms%200..*>[Form],[Thing],[InteractionAffordance],[ExpectedResponse],[AdditionalExpectedResponse])

## Referenced by Class

 *  **None** *[➞forms](interactionAffordance__forms.md)*  <sub>0..\*</sub>  **[Form](Form.md)**
 *  **None** *[➞forms](thing__forms.md)*  <sub>0..\*</sub>  **[Form](Form.md)**

## Attributes


### Own

 * [target](target.md)  <sub>1..1</sub>
     * Description: Target IRI of a link or submission target of a Form
     * Range: [AnyUri](types/AnyUri.md)
 * [➞href](form__href.md)  <sub>1..1</sub>
     * Range: [AnyUri](types/AnyUri.md)
 * [➞contentType](form__contentType.md)  <sub>0..1</sub>
     * Description: Assign a content type based on a media type IANA-MEDIA-TYPES (e.g., 'text/plain') and potential parameters  (e.g., 'charset=utf-8') for the media type.
     * Range: [String](types/String.md)
 * [➞contentCoding](form__contentCoding.md)  <sub>0..1</sub>
     * Description: Content coding values indicate an encoding transformation that has been or can be applied to a representation.  Content codings are primarily used to allow a representation to be compressed or otherwise usefully transformed  without losing the identity of its underlying media type and without loss of information. Examples of content coding include \"gzip\", \"deflate\", etc.
     * Range: [String](types/String.md)
 * [➞securityDefinitions](form__securityDefinitions.md)  <sub>0..1</sub>
     * Description: A security schema applied to a (set of) affordance(s).
     * Range: [String](types/String.md)
 * [➞scopes](form__scopes.md)  <sub>0..1</sub>
     * Description: TODO Check, was not in hctl ontology, if not could be source of discrepancy
     * Range: [String](types/String.md)
 * [➞returns](form__returns.md)  <sub>0..1</sub>
     * Description: This optional term can be used if, e.g., the output communication metadata differ from input metadata (e.g., output contentType differ from the input contentType). The response name contains metadata that is only valid for the response messages.
     * Range: [ExpectedResponse](ExpectedResponse.md)
 * [➞additionalReturns](form__additionalReturns.md)  <sub>0..\*</sub>
     * Description: This optional term can be used if additional expected responses are possible, e.g. for error reporting. Each additional response needs to be distinguished from others in some way (for example, by specifying a protocol-specific response code), and may also have its own data schema.
     * Range: [AdditionalExpectedResponse](AdditionalExpectedResponse.md)
 * [➞subprotocol](form__subprotocol.md)  <sub>0..1</sub>
     * Description: Indicates the exact mechanism by which an interaction will be accomplished for a given protocol when there are multiple options.
     * Range: [String](types/String.md)
 * [➞operationType](form__operationType.md)  <sub>0..\*</sub>
     * Description: Indicates the semantic intention of performing the operation(s) described by the form.
     * Range: [OperationTypes](OperationTypes.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Mappings:** | | hctl:Form |
# Class: InteractionAffordance

TOOD

URI: [td:InteractionAffordance](https://www.w3.org/2019/wot/td#InteractionAffordance)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[PropertyAffordance],[MultiLanguage],[Form]<forms%200..*-++[InteractionAffordance&#124;name:string],[DataSchema]<uriVariables%200..*-++[InteractionAffordance],[MultiLanguage]<descriptionInLanguage%200..1-%20[InteractionAffordance],[MultiLanguage]<titleInLanguage%200..1-%20[InteractionAffordance],[MultiLanguage]<description%200..1-%20[InteractionAffordance],[MultiLanguage]<title%200..1-%20[InteractionAffordance],[MultiLanguage]<descriptions%200..*-++[InteractionAffordance],[MultiLanguage]<titles%200..*-++[InteractionAffordance],[InteractionAffordance]^-[PropertyAffordance],[InteractionAffordance]^-[EventAffordance],[InteractionAffordance]^-[ActionAffordance],[Form],[EventAffordance],[DataSchema],[ActionAffordance])](https://yuml.me/diagram/nofunky;dir:TB/class/[PropertyAffordance],[MultiLanguage],[Form]<forms%200..*-++[InteractionAffordance&#124;name:string],[DataSchema]<uriVariables%200..*-++[InteractionAffordance],[MultiLanguage]<descriptionInLanguage%200..1-%20[InteractionAffordance],[MultiLanguage]<titleInLanguage%200..1-%20[InteractionAffordance],[MultiLanguage]<description%200..1-%20[InteractionAffordance],[MultiLanguage]<title%200..1-%20[InteractionAffordance],[MultiLanguage]<descriptions%200..*-++[InteractionAffordance],[MultiLanguage]<titles%200..*-++[InteractionAffordance],[InteractionAffordance]^-[PropertyAffordance],[InteractionAffordance]^-[EventAffordance],[InteractionAffordance]^-[ActionAffordance],[Form],[EventAffordance],[DataSchema],[ActionAffordance])

## Children

 * [ActionAffordance](ActionAffordance.md) - An Interaction Affordance that allows to invoke a function of the Thing, which manipulates state (e.g., toggling a lamp on or off) or triggers a process on the Thing (e.g., dim a lamp over time).
 * [EventAffordance](EventAffordance.md) - An Interaction Affordance that describes an event source, which asynchronously pushes event data to Consumers (e.g., overhearing alerts).
 * [PropertyAffordance](PropertyAffordance.md) - An Interaction Affordance that exposes state of the Thing. This state can be retrieved (read) and/or updated.

## Referenced by Class


## Attributes


### Own

 * [titles](titles.md)  <sub>0..\*</sub>
     * Range: [MultiLanguage](MultiLanguage.md)
 * [descriptions](descriptions.md)  <sub>0..\*</sub>
     * Description: TODO, check, according to the description a description should not contain a lang tag.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [title](title.md)  <sub>0..1</sub>
     * Description: Provides a human-readable title (e.g., display a text for UI representation) based on a default language.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [description](description.md)  <sub>0..1</sub>
     * Range: [MultiLanguage](MultiLanguage.md)
 * [titleInLanguage](titleInLanguage.md)  <sub>0..1</sub>
     * Description: title of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [descriptionInLanguage](descriptionInLanguage.md)  <sub>0..1</sub>
     * Description: description of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [➞name](interactionAffordance__name.md)  <sub>1..1</sub>
     * Description: Indexing property to store entity names when serializing them in a JSON-LD @index container.
     * Range: [String](types/String.md)
 * [➞uriVariables](interactionAffordance__uriVariables.md)  <sub>0..\*</sub>
     * Description: Define URI template variables according to RFC6570 as collection based on schema specifications. The individual variables DataSchema cannot be an ObjectSchema or an ArraySchema. TODO: range is not obvious from the ontology.
     * Range: [DataSchema](DataSchema.md)
 * [➞forms](interactionAffordance__forms.md)  <sub>0..\*</sub>
     * Description: Set of form hypermedia controls that describe how an operation can be performed.
     * Range: [Form](Form.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Mappings:** | | td:InteractionAffordance |
# Class: Link

A link can be viewed as a statement of the form link context that has a relation type resource at link target", where the optional target attributes may further describe the resource.

URI: [td:Link](https://www.w3.org/2019/wot/td#Link)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[Thing]++-%20links%200..*>[Link&#124;target:anyUri;hintsAtMediaType:string%20%3F;type:string%20%3F;relation:string%20%3F;anchor:anyUri%20%3F;sizes:string%20%3F;hreflang:string%20%3F],[Thing])](https://yuml.me/diagram/nofunky;dir:TB/class/[Thing]++-%20links%200..*>[Link&#124;target:anyUri;hintsAtMediaType:string%20%3F;type:string%20%3F;relation:string%20%3F;anchor:anyUri%20%3F;sizes:string%20%3F;hreflang:string%20%3F],[Thing])

## Referenced by Class

 *  **None** *[➞links](thing__links.md)*  <sub>0..\*</sub>  **[Link](Link.md)**

## Attributes


### Own

 * [target](target.md)  <sub>1..1</sub>
     * Description: Target IRI of a link or submission target of a Form
     * Range: [AnyUri](types/AnyUri.md)
 * [➞hintsAtMediaType](link__hintsAtMediaType.md)  <sub>0..1</sub>
     * Description: Target attribute providing a hint indicating what the media type [IANA-MEDIA-TYPES] of the result of dereferencing the link should be.
     * Range: [String](types/String.md)
 * [➞type](link__type.md)  <sub>0..1</sub>
     * Range: [String](types/String.md)
 * [➞relation](link__relation.md)  <sub>0..1</sub>
     * Description: A link relation type identifies the semantics of a link.
     * Range: [String](types/String.md)
 * [➞anchor](link__anchor.md)  <sub>0..1</sub>
     * Description: By default, the context, or anchor, of a link conveyed in the Link header field is the URL of the representation it is associated with, as defined in RFC7231, Section 3.1.4.1, and is serialized as a URI.
     * Range: [AnyUri](types/AnyUri.md)
 * [➞sizes](link__sizes.md)  <sub>0..1</sub>
     * Description: Target attribute that specifies one or more sizes for the referenced icon. Only applicable for relation type 'icon'. The value pattern follows {Height}x{Width} (e.g., \"16x16\", \"16x16 32x32\").
     * Range: [String](types/String.md)
 * [➞hreflang](link__hreflang.md)  <sub>0..1</sub>
     * Description: The hreflang attribute specifies the language of a linked document. The value of this must be a valid language tag [[BCP47]].
     * Range: [String](types/String.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Mappings:** | | hctl:Link |
# Class: MultiLanguage



URI: [td:MultiLanguage](https://www.w3.org/2019/wot/td#MultiLanguage)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[DataSchema]-%20description%200..1>[MultiLanguage&#124;key:string],[InteractionAffordance]-%20description%200..1>[MultiLanguage],[Thing]-%20description%200..1>[MultiLanguage],[DataSchema]-%20descriptionInLanguage%200..1>[MultiLanguage],[InteractionAffordance]-%20descriptionInLanguage%200..1>[MultiLanguage],[Thing]-%20descriptionInLanguage%200..1>[MultiLanguage],[SecurityScheme]++-%20descriptions%200..*>[MultiLanguage],[InteractionAffordance]++-%20descriptions%200..*>[MultiLanguage],[Thing]++-%20descriptions%200..*>[MultiLanguage],[DataSchema]-%20title%200..1>[MultiLanguage],[InteractionAffordance]-%20title%200..1>[MultiLanguage],[Thing]-%20title%200..1>[MultiLanguage],[DataSchema]-%20titleInLanguage%200..1>[MultiLanguage],[InteractionAffordance]-%20titleInLanguage%200..1>[MultiLanguage],[Thing]-%20titleInLanguage%200..1>[MultiLanguage],[InteractionAffordance]++-%20titles%200..*>[MultiLanguage],[Thing]++-%20titles%200..*>[MultiLanguage],[Thing],[SecurityScheme],[InteractionAffordance],[DataSchema])](https://yuml.me/diagram/nofunky;dir:TB/class/[DataSchema]-%20description%200..1>[MultiLanguage&#124;key:string],[InteractionAffordance]-%20description%200..1>[MultiLanguage],[Thing]-%20description%200..1>[MultiLanguage],[DataSchema]-%20descriptionInLanguage%200..1>[MultiLanguage],[InteractionAffordance]-%20descriptionInLanguage%200..1>[MultiLanguage],[Thing]-%20descriptionInLanguage%200..1>[MultiLanguage],[SecurityScheme]++-%20descriptions%200..*>[MultiLanguage],[InteractionAffordance]++-%20descriptions%200..*>[MultiLanguage],[Thing]++-%20descriptions%200..*>[MultiLanguage],[DataSchema]-%20title%200..1>[MultiLanguage],[InteractionAffordance]-%20title%200..1>[MultiLanguage],[Thing]-%20title%200..1>[MultiLanguage],[DataSchema]-%20titleInLanguage%200..1>[MultiLanguage],[InteractionAffordance]-%20titleInLanguage%200..1>[MultiLanguage],[Thing]-%20titleInLanguage%200..1>[MultiLanguage],[InteractionAffordance]++-%20titles%200..*>[MultiLanguage],[Thing]++-%20titles%200..*>[MultiLanguage],[Thing],[SecurityScheme],[InteractionAffordance],[DataSchema])

## Referenced by Class

 *  **None** *[description](description.md)*  <sub>0..1</sub>  **[MultiLanguage](MultiLanguage.md)**
 *  **None** *[descriptionInLanguage](descriptionInLanguage.md)*  <sub>0..1</sub>  **[MultiLanguage](MultiLanguage.md)**
 *  **None** *[descriptions](descriptions.md)*  <sub>0..\*</sub>  **[MultiLanguage](MultiLanguage.md)**
 *  **None** *[title](title.md)*  <sub>0..1</sub>  **[MultiLanguage](MultiLanguage.md)**
 *  **None** *[titleInLanguage](titleInLanguage.md)*  <sub>0..1</sub>  **[MultiLanguage](MultiLanguage.md)**
 *  **None** *[titles](titles.md)*  <sub>0..\*</sub>  **[MultiLanguage](MultiLanguage.md)**

## Attributes


### Own

 * [➞key](multiLanguage__key.md)  <sub>1..1</sub>
     * Range: [String](types/String.md)

# Class: PropertyAffordance

An Interaction Affordance that exposes state of the Thing. This state can be retrieved (read) and/or updated.

URI: [td:PropertyAffordance](https://www.w3.org/2019/wot/td#PropertyAffordance)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[Thing]++-%20properties%200..*>[PropertyAffordance&#124;observable:boolean%20%3F;propertyName:string%20%3F;writeOnly:string%20%3F;readonly:string%20%3F;name(i):string],[PropertyAffordance]uses%20-.->[DataSchema],[InteractionAffordance]^-[PropertyAffordance],[Thing],[MultiLanguage],[InteractionAffordance],[Form],[DataSchema])](https://yuml.me/diagram/nofunky;dir:TB/class/[Thing]++-%20properties%200..*>[PropertyAffordance&#124;observable:boolean%20%3F;propertyName:string%20%3F;writeOnly:string%20%3F;readonly:string%20%3F;name(i):string],[PropertyAffordance]uses%20-.->[DataSchema],[InteractionAffordance]^-[PropertyAffordance],[Thing],[MultiLanguage],[InteractionAffordance],[Form],[DataSchema])

## Parents

 *  is_a: [InteractionAffordance](InteractionAffordance.md) - TOOD

## Uses Mixin

 *  mixin: [DataSchema](DataSchema.md) - Metadata that describes the data format used. It can be used for validation.

## Referenced by Class

 *  **None** *[➞properties](thing__properties.md)*  <sub>0..\*</sub>  **[PropertyAffordance](PropertyAffordance.md)**

## Attributes


### Own

 * [➞observable](propertyAffordance__observable.md)  <sub>0..1</sub>
     * Description: A hint that indicates whether Servients hosting the Thing and Intermediaries should probide a Protocol Binding  that supports the observeproperty and unobserveproperty operations for this Property.
     * Range: [Boolean](types/Boolean.md)

### Inherited from InteractionAffordance:

 * [titles](titles.md)  <sub>0..\*</sub>
     * Range: [MultiLanguage](MultiLanguage.md)
 * [descriptions](descriptions.md)  <sub>0..\*</sub>
     * Description: TODO, check, according to the description a description should not contain a lang tag.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [title](title.md)  <sub>0..1</sub>
     * Description: Provides a human-readable title (e.g., display a text for UI representation) based on a default language.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [description](description.md)  <sub>0..1</sub>
     * Range: [MultiLanguage](MultiLanguage.md)
 * [titleInLanguage](titleInLanguage.md)  <sub>0..1</sub>
     * Description: title of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [descriptionInLanguage](descriptionInLanguage.md)  <sub>0..1</sub>
     * Description: description of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [➞name](interactionAffordance__name.md)  <sub>1..1</sub>
     * Description: Indexing property to store entity names when serializing them in a JSON-LD @index container.
     * Range: [String](types/String.md)
 * [➞uriVariables](interactionAffordance__uriVariables.md)  <sub>0..\*</sub>
     * Description: Define URI template variables according to RFC6570 as collection based on schema specifications. The individual variables DataSchema cannot be an ObjectSchema or an ArraySchema. TODO: range is not obvious from the ontology.
     * Range: [DataSchema](DataSchema.md)
 * [➞forms](interactionAffordance__forms.md)  <sub>0..\*</sub>
     * Description: Set of form hypermedia controls that describe how an operation can be performed.
     * Range: [Form](Form.md)

### Mixed in from DataSchema:

 * [➞propertyName](dataSchema__propertyName.md)  <sub>0..1</sub>
     * Description: Used to store the indexing name in the parent object when this schema appears as a property of an object schema.
     * Range: [String](types/String.md)

### Mixed in from DataSchema:

 * [➞writeOnly](dataSchema__writeOnly.md)  <sub>0..1</sub>
     * Description: Boolean value that is a hint to indicate whether a property interaction/value is write only (=true) or not (=false).
     * Range: [String](types/String.md)

### Mixed in from DataSchema:

 * [➞readonly](dataSchema__readonly.md)  <sub>0..1</sub>
     * Description: Boolean value that is a hint to indicate whether a property interaction/value is read only (=true) or not (=false).
     * Range: [String](types/String.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Mappings:** | | td:PropertyAffordance |
# Class: SecurityScheme



URI: [td:SecurityScheme](https://www.w3.org/2019/wot/td#SecurityScheme)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[MultiLanguage]<descriptions%200..*-++[SecurityScheme&#124;@type:string%20*;description:string%20%3F;proxy:anyUri%20%3F;scheme:SecuritySchemeType],[MultiLanguage])](https://yuml.me/diagram/nofunky;dir:TB/class/[MultiLanguage]<descriptions%200..*-++[SecurityScheme&#124;@type:string%20*;description:string%20%3F;proxy:anyUri%20%3F;scheme:SecuritySchemeType],[MultiLanguage])

## Attributes


### Own

 * [@type](@type.md)  <sub>0..\*</sub>
     * Range: [String](types/String.md)
 * [descriptions](descriptions.md)  <sub>0..\*</sub>
     * Description: TODO, check, according to the description a description should not contain a lang tag.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [➞description](securityScheme__description.md)  <sub>0..1</sub>
     * Range: [String](types/String.md)
 * [➞proxy](securityScheme__proxy.md)  <sub>0..1</sub>
     * Description: URI of the proxy server this security configuration provides access to. If not given, the corresponding security configuration is for the endpoint.
     * Range: [AnyUri](types/AnyUri.md)
 * [➞scheme](securityScheme__scheme.md)  <sub>1..1</sub>
     * Range: [SecuritySchemeType](SecuritySchemeType.md)

# Class: Thing

An abstraction of a physical or a virtual entity whose metadata and interfaces are described by a WoT Thing Description, whereas a virtual entity is the composition of one or more Things.

URI: [td:Thing](https://www.w3.org/2019/wot/td#Thing)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[VersionInfo],[EventAffordance]<events%200..*-++[Thing&#124;id:anyUri;@type:string%20*;securityDefinitions:string%20*;security:string%20*;profile:anyUri%20*;instance:string%20%3F;created:datetime%20%3F;modified:datetime%20%3F;supportContact:anyUri%20%3F;base:anyUri%20%3F],[ActionAffordance]<actions%200..*-++[Thing],[PropertyAffordance]<properties%200..*-++[Thing],[Link]<links%200..*-++[Thing],[Form]<forms%200..*-++[Thing],[VersionInfo]<version%200..1-++[Thing],[DataSchema]<schemaDefinitions%200..*-++[Thing],[MultiLanguage]<descriptionInLanguage%200..1-%20[Thing],[MultiLanguage]<titleInLanguage%200..1-%20[Thing],[MultiLanguage]<descriptions%200..*-++[Thing],[MultiLanguage]<titles%200..*-++[Thing],[MultiLanguage]<description%200..1-%20[Thing],[MultiLanguage]<title%200..1-%20[Thing],[PropertyAffordance],[MultiLanguage],[Link],[Form],[EventAffordance],[DataSchema],[ActionAffordance])](https://yuml.me/diagram/nofunky;dir:TB/class/[VersionInfo],[EventAffordance]<events%200..*-++[Thing&#124;id:anyUri;@type:string%20*;securityDefinitions:string%20*;security:string%20*;profile:anyUri%20*;instance:string%20%3F;created:datetime%20%3F;modified:datetime%20%3F;supportContact:anyUri%20%3F;base:anyUri%20%3F],[ActionAffordance]<actions%200..*-++[Thing],[PropertyAffordance]<properties%200..*-++[Thing],[Link]<links%200..*-++[Thing],[Form]<forms%200..*-++[Thing],[VersionInfo]<version%200..1-++[Thing],[DataSchema]<schemaDefinitions%200..*-++[Thing],[MultiLanguage]<descriptionInLanguage%200..1-%20[Thing],[MultiLanguage]<titleInLanguage%200..1-%20[Thing],[MultiLanguage]<descriptions%200..*-++[Thing],[MultiLanguage]<titles%200..*-++[Thing],[MultiLanguage]<description%200..1-%20[Thing],[MultiLanguage]<title%200..1-%20[Thing],[PropertyAffordance],[MultiLanguage],[Link],[Form],[EventAffordance],[DataSchema],[ActionAffordance])

## Attributes


### Own

 * [id](id.md)  <sub>1..1</sub>
     * Description: TODO
     * Range: [AnyUri](types/AnyUri.md)
 * [title](title.md)  <sub>0..1</sub>
     * Description: Provides a human-readable title (e.g., display a text for UI representation) based on a default language.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [description](description.md)  <sub>0..1</sub>
     * Range: [MultiLanguage](MultiLanguage.md)
 * [titles](titles.md)  <sub>0..\*</sub>
     * Range: [MultiLanguage](MultiLanguage.md)
 * [descriptions](descriptions.md)  <sub>0..\*</sub>
     * Description: TODO, check, according to the description a description should not contain a lang tag.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [@type](@type.md)  <sub>0..\*</sub>
     * Range: [String](types/String.md)
 * [titleInLanguage](titleInLanguage.md)  <sub>0..1</sub>
     * Description: title of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [descriptionInLanguage](descriptionInLanguage.md)  <sub>0..1</sub>
     * Description: description of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [➞securityDefinitions](thing__securityDefinitions.md)  <sub>0..\*</sub>
     * Description: A security scheme applied to a (set of) affordance(s). TODO check
     * Range: [String](types/String.md)
 * [➞security](thing__security.md)  <sub>0..\*</sub>
     * Description: A Thing may define abstract security schemes, used to configure the secure access of (a set of) affordance(s). TODO: check
     * Range: [String](types/String.md)
 * [➞schemaDefinitions](thing__schemaDefinitions.md)  <sub>0..\*</sub>
     * Description: TODO CHECK
     * Range: [DataSchema](DataSchema.md)
 * [➞profile](thing__profile.md)  <sub>0..\*</sub>
     * Description: Indicates the WoT Profile mechanisms followed by this Thing Description and the corresponding Thing implementation.
     * Range: [AnyUri](types/AnyUri.md)
 * [➞instance](thing__instance.md)  <sub>0..1</sub>
     * Description: Provides a version identicator of this TD instance.
     * Range: [String](types/String.md)
 * [➞created](thing__created.md)  <sub>0..1</sub>
     * Description: Provides information when the TD instance was created.
     * Range: [Datetime](types/Datetime.md)
 * [➞modified](thing__modified.md)  <sub>0..1</sub>
     * Description: Provides information when the TD instance was last modified.
     * Range: [Datetime](types/Datetime.md)
 * [➞supportContact](thing__supportContact.md)  <sub>0..1</sub>
     * Description: Provides information about the TD maintainer as URI scheme (e.g., <code>mailto</code> [[RFC6068]],<code>tel</code> [[RFC3966]],<code>https</code> [[RFC9112]]).
     * Range: [AnyUri](types/AnyUri.md)
 * [➞base](thing__base.md)  <sub>0..1</sub>
     * Description: Define the base URI that is used for all relative URI references throughout a TD document.
     * Range: [AnyUri](types/AnyUri.md)
 * [➞version](thing__version.md)  <sub>0..1</sub>
     * Range: [VersionInfo](VersionInfo.md)
 * [➞forms](thing__forms.md)  <sub>0..\*</sub>
     * Description: Set of form hypermedia controls that describe how an operation can be performed. Forms are serializations of Protocol Bindings.
     * Range: [Form](Form.md)
 * [➞links](thing__links.md)  <sub>0..\*</sub>
     * Description: Provides Web links to arbitrary resources that relate to the specified Thing Description.
     * Range: [Link](Link.md)
 * [➞properties](thing__properties.md)  <sub>0..\*</sub>
     * Description: All Property-based interaction affordances of the Thing.
     * Range: [PropertyAffordance](PropertyAffordance.md)
 * [➞actions](thing__actions.md)  <sub>0..\*</sub>
     * Description: All Action-based interaction affordances of the Thing.
     * Range: [ActionAffordance](ActionAffordance.md)
 * [➞events](thing__events.md)  <sub>0..\*</sub>
     * Description: All Event-based interaction affordances of the Thing.
     * Range: [EventAffordance](EventAffordance.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Mappings:** | | td:Thing |
# Class: VersionInfo

Provides version information.

URI: [td:VersionInfo](https://www.w3.org/2019/wot/td#VersionInfo)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[Thing]++-%20version%200..1>[VersionInfo&#124;instance:string;model:string%20%3F],[Thing])](https://yuml.me/diagram/nofunky;dir:TB/class/[Thing]++-%20version%200..1>[VersionInfo&#124;instance:string;model:string%20%3F],[Thing])

## Referenced by Class

 *  **None** *[➞version](thing__version.md)*  <sub>0..1</sub>  **[VersionInfo](VersionInfo.md)**

## Attributes


### Own

 * [➞instance](versionInfo__instance.md)  <sub>1..1</sub>
     * Range: [String](types/String.md)
 * [➞model](versionInfo__model.md)  <sub>0..1</sub>
     * Range: [String](types/String.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Mappings:** | | schema:version |
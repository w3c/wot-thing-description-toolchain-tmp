export type MultiLanguageKey = string;
export type InteractionAffordanceName = string;
export type PropertyAffordanceName = string;
export type ActionAffordanceName = string;
export type EventAffordanceName = string;
export type ThingId = string;
/**
* Enumerations of well-known operation types necessary to implement the WoT interaction model.
*/
export enum OperationTypes {
    
    /** Identifies the read operation on Property Affordances to retrieve the corresponding data. */
    readproperty = "readproperty",
    /** Identifies the write operation on Property Affordances to update the corresponding data. */
    writeproperty = "writeproperty",
    /** Identifies the observe operation on Property Affordances to be notified with the new data when the Property is updated. */
    observeproperty = "observeproperty",
    /** Identifies the unobserve operation on Property Affordances to stop the corresponding notifications. */
    unobserveproperty = "unobserveproperty",
    /** Identifies the invoke operation on Action Affordances to perform the corresponding action. */
    invokeaction = "invokeaction",
    /** Identifies the querying operation on Action Affordances to get the status of the corresponding action. */
    queryaction = "queryaction",
    /** Identifies the cancel operation on Action Affordances to cancel the ongoing corresponding action. */
    cancelaction = "cancelaction",
    /** Identifies the subscribe operation on Event Affordances to be notified by the Thing when the event occurs. */
    subscribeevent = "subscribeevent",
    /** Identifies the unsubscribe operation on Event Affordances to stop the corresponding notifications. */
    unsubscribeevent = "unsubscribeevent",
    /** Identifies the readallproperties operation on a Thing to retrieve the data of all Properties in a single interaction. */
    readallproperties = "readallproperties",
    /** Identifies the writeallproperties operation on a Thing to update the data of all writable Properties in a single interaction. */
    writeallproperties = "writeallproperties",
    /** Identifies the readmultipleproperties operation on a Thing to retrieve the data of selected Properties in a single interaction. */
    readmultipleproperties = "readmultipleproperties",
    /** Identifies the writemultipleproperties operation on a Thing to update the data of selected writable Properties in a single interaction. */
    writemultipleproperties = "writemultipleproperties",
    /** Identifies the observeallproperties operation on Properties to be notified with new data when any Property is updated. */
    observeallproperties = "observeallproperties",
    /** Identifies the unobserveallproperties operation on Properties to stop notifications from all Properties in a single interaction. */
    unobserveallproperties = "unobserveallproperties",
    /** Identifies the subscribeallevents operation on Events to subscribe to notifications from all Events in a single interaction. */
    subscribeallevents = "subscribeallevents",
    /** Identifies the unsubscribeallevents operation on Events to unsubscribe from notifications from all Events in a single interaction. */
    unsubscribeallevents = "unsubscribeallevents",
    /** Identifies the queryallactions operation on a Thing to get the status of all Actions in a single interaction. */
    queryallactions = "queryallactions",
};

export enum SecuritySchemeType {
    
    /** A security configuration corresponding to identified by the Vocabulary Term nosec, indicating there is no authentication or other mechanism required to access the resource. */
    nosec = "nosec",
    /** Elements of this scheme define various ways in which other named schemes defined in securityDefinitions, including other ComboSecurityScheme definitions, are to be combined to create a new scheme definition. */
    combo = "combo",
    /** Uses an unencrypted username and password. */
    basic = "basic",
    /** This scheme is similar to basic authentication but with added features to avoid man-in-the-middle attacks. */
    digest = "digest",
    /** Bearer tokens are used independently of OAuth2. */
    bearer = "bearer",
    /** This is meant to identify that a standard is used for pre-shared keys such as TLS-PSK [RFC4279], and that the ciphersuite used for keys will be established during protocol negotiation. */
    psk = "psk",
    /** OAuth 2.0 authentication security configuration for systems conformant with [RFC6749] and [RFC8252]. */
    oauth2 = "oauth2",
    /** This scheme is to be used when the access token is opaque. */
    apikey = "apikey",
    /** This scheme indicates that the security parameters are going to be negotiated by the underlying protocols at runtime */
    auto = "auto",
};


/**
 * Provides version information.
 */
export interface VersionInfo {
    instance: string,
    model?: string,
}



export interface MultiLanguage {
    key: string,
}


/**
 * A link can be viewed as a statement of the form link context that has a relation type resource at link target", where the optional target attributes may further describe the resource.
 */
export interface Link {
    /** Target IRI of a link or submission target of a Form */
    target: string,
    /** Target attribute providing a hint indicating what the media type [IANA-MEDIA-TYPES] of the result of dereferencing the link should be. */
    hintsAtMediaType?: string,
    type?: string,
    /** A link relation type identifies the semantics of a link. */
    relation?: string,
    /** By default, the context, or anchor, of a link conveyed in the Link header field is the URL of the representation it is associated with, as defined in RFC7231, Section 3.1.4.1, and is serialized as a URI. */
    anchor?: string,
    /** Target attribute that specifies one or more sizes for the referenced icon. Only applicable for relation type 'icon'. The value pattern follows {Height}x{Width} (e.g., \"16x16\", \"16x16 32x32\"). */
    sizes?: string,
    /** The hreflang attribute specifies the language of a linked document. The value of this must be a valid language tag [[BCP47]]. */
    hreflang?: string,
}


/**
 * Communication metadata describing the expected response message for the primary response.
 */
export interface ExpectedResponse {
    /** TODO Check, was not in hctl ontology, if not could be source of discrepancy */
    contentType: string,
}


/**
 * Communication metadata describing the expected response message for additional responses.
 */
export interface AdditionalExpectedResponse extends ExpectedResponse {
    /** This optional term can be used to define a data schema for an additional response if it differs from the default output data schema. Rather than a DataSchema object, the name of a previous definition given in a SchemaDefinitions map must be used. */
    additionalOutputSchema?: string,
    /** Signals if the additional response should not be considered an error. */
    success?: boolean,
    /** TODO Check, was not in hctl ontology, if not could be source of discrepancy */
    schema?: string,
}


/**
 * A form can be viewed as a statement of to perform an operation type on form context,  make a request method to submission target, where the optional form fields may further describe the required request. In Thing Descriptions, the form context is the surrounding Object,  such as Properties, Actions, and Events or the Thing itself for meta-interactions.
 */
export interface Form {
    /** Target IRI of a link or submission target of a Form */
    target: string,
    href: string,
    /** Assign a content type based on a media type IANA-MEDIA-TYPES (e.g., 'text/plain') and potential parameters  (e.g., 'charset=utf-8') for the media type. */
    contentType?: string,
    /** Content coding values indicate an encoding transformation that has been or can be applied to a representation.  Content codings are primarily used to allow a representation to be compressed or otherwise usefully transformed  without losing the identity of its underlying media type and without loss of information. Examples of content coding include \"gzip\", \"deflate\", etc. */
    contentCoding?: string,
    /** A security schema applied to a (set of) affordance(s). */
    securityDefinitions?: string,
    /** TODO Check, was not in hctl ontology, if not could be source of discrepancy */
    scopes?: string,
    /** This optional term can be used if, e.g., the output communication metadata differ from input metadata (e.g., output contentType differ from the input contentType). The response name contains metadata that is only valid for the response messages. */
    returns?: ExpectedResponse,
    /** This optional term can be used if additional expected responses are possible, e.g. for error reporting. Each additional response needs to be distinguished from others in some way (for example, by specifying a protocol-specific response code), and may also have its own data schema. */
    additionalReturns?: AdditionalExpectedResponse[],
    /** Indicates the exact mechanism by which an interaction will be accomplished for a given protocol when there are multiple options. */
    subprotocol?: string,
    /** Indicates the semantic intention of performing the operation(s) described by the form. */
    operationType?: string,
}



export interface SecurityScheme {
    @type?: string[],
    /** TODO, check, according to the description a description should not contain a lang tag. */
    descriptions?: {[index: MultiLanguageKey]: MultiLanguage },
    description?: string,
    /** URI of the proxy server this security configuration provides access to. If not given, the corresponding security configuration is for the endpoint. */
    proxy?: string,
    scheme: string,
}


/**
 * Metadata that describes the data format used. It can be used for validation.
 */
export interface DataSchema {
    description?: MultiLanguageKey,
    /** Provides a human-readable title (e.g., display a text for UI representation) based on a default language. */
    title?: MultiLanguageKey,
    /** title of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description. */
    titleInLanguage?: MultiLanguageKey,
    /** description of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description. */
    descriptionInLanguage?: MultiLanguageKey,
    /** Used to store the indexing name in the parent object when this schema appears as a property of an object schema. */
    propertyName?: string,
    /** Boolean value that is a hint to indicate whether a property interaction/value is write only (=true) or not (=false). */
    writeOnly?: string,
    /** Boolean value that is a hint to indicate whether a property interaction/value is read only (=true) or not (=false). */
    readonly?: string,
}


/**
 * TOOD
 */
export interface InteractionAffordance {
    titles?: {[index: MultiLanguageKey]: MultiLanguage },
    /** TODO, check, according to the description a description should not contain a lang tag. */
    descriptions?: {[index: MultiLanguageKey]: MultiLanguage },
    /** Provides a human-readable title (e.g., display a text for UI representation) based on a default language. */
    title?: MultiLanguageKey,
    description?: MultiLanguageKey,
    /** title of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description. */
    titleInLanguage?: MultiLanguageKey,
    /** description of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description. */
    descriptionInLanguage?: MultiLanguageKey,
    /** Indexing property to store entity names when serializing them in a JSON-LD @index container. */
    name: string,
    /** Define URI template variables according to RFC6570 as collection based on schema specifications. The individual variables DataSchema cannot be an ObjectSchema or an ArraySchema. TODO: range is not obvious from the ontology. */
    uriVariables?: DataSchema[],
    /** Set of form hypermedia controls that describe how an operation can be performed. */
    forms?: Form[],
}


/**
 * An Interaction Affordance that exposes state of the Thing. This state can be retrieved (read) and/or updated.
 */
export interface PropertyAffordance extends InteractionAffordance, DataSchema {
    /** A hint that indicates whether Servients hosting the Thing and Intermediaries should probide a Protocol Binding  that supports the observeproperty and unobserveproperty operations for this Property. */
    observable?: boolean,
}


/**
 * An Interaction Affordance that allows to invoke a function of the Thing, which manipulates state (e.g., toggling a lamp on or off) or triggers a process on the Thing (e.g., dim a lamp over time).
 */
export interface ActionAffordance extends InteractionAffordance {
    /** Signals if the action is safe (=true) or not. Used to signal if there is no internal state (cf. resource state) is changed when invoking an Action. */
    safe?: boolean,
    /** Indicates whether the action is synchronous (=true) or not. A synchronous action means that the response of action contains all the information about the result of the action and no further querying about the status of the action is needed. Lack of this keyword means that no claim on the synchronicity of the action can be made. */
    synchronous?: boolean,
    /** Indicates whether the action is idempotent (=true) or not. Informs whether the action can be called repeatedly with the same results, if present, based on the same input. */
    idempotent?: boolean,
    /** Used to define the input data schema of the action. */
    input?: DataSchema,
    /** Used to define the output data schema of the action. */
    output?: DataSchema,
}


/**
 * An Interaction Affordance that describes an event source, which asynchronously pushes event data to Consumers (e.g., overhearing alerts).
 */
export interface EventAffordance extends InteractionAffordance {
    /** Defines data that needs to be passed upon subscription, e.g., filters or message format for setting up Webhooks. */
    subscription?: DataSchema,
    /** Defines any data that needs to be passed to cancel a subscription, e.g., a specific message to remove a Webhook. */
    cancellation?: DataSchema,
    /** Defines the data schema of the Event instance messages pushed by the Thing. */
    notification?: DataSchema,
    /** Defines the data schema of the Event response messages sent by the consumer in a response to a data message. */
    notificationResponse?: DataSchema,
}


/**
 * An abstraction of a physical or a virtual entity whose metadata and interfaces are described by a WoT Thing Description, whereas a virtual entity is the composition of one or more Things.
 */
export interface Thing {
    /** TODO */
    id: string,
    /** Provides a human-readable title (e.g., display a text for UI representation) based on a default language. */
    title?: MultiLanguageKey,
    description?: MultiLanguageKey,
    titles?: {[index: MultiLanguageKey]: MultiLanguage },
    /** TODO, check, according to the description a description should not contain a lang tag. */
    descriptions?: {[index: MultiLanguageKey]: MultiLanguage },
    @type?: string[],
    /** title of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description. */
    titleInLanguage?: MultiLanguageKey,
    /** description of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description. */
    descriptionInLanguage?: MultiLanguageKey,
    /** A security scheme applied to a (set of) affordance(s). TODO check */
    securityDefinitions?: string[],
    /** A Thing may define abstract security schemes, used to configure the secure access of (a set of) affordance(s). TODO: check */
    security?: string[],
    /** TODO CHECK */
    schemaDefinitions?: DataSchema[],
    /** Indicates the WoT Profile mechanisms followed by this Thing Description and the corresponding Thing implementation. */
    profile?: string[],
    /** Provides a version identicator of this TD instance. */
    instance?: string,
    /** Provides information when the TD instance was created. */
    created?: string,
    /** Provides information when the TD instance was last modified. */
    modified?: string,
    /** Provides information about the TD maintainer as URI scheme (e.g., <code>mailto</code> [[RFC6068]],<code>tel</code> [[RFC3966]],<code>https</code> [[RFC9112]]). */
    supportContact?: string,
    /** Define the base URI that is used for all relative URI references throughout a TD document. */
    base?: string,
    version?: VersionInfo,
    /** Set of form hypermedia controls that describe how an operation can be performed. Forms are serializations of Protocol Bindings. */
    forms?: Form[],
    /** Provides Web links to arbitrary resources that relate to the specified Thing Description. */
    links?: Link[],
    /** All Property-based interaction affordances of the Thing. */
    properties?: {[index: PropertyAffordanceName]: PropertyAffordance },
    /** All Action-based interaction affordances of the Thing. */
    actions?: {[index: ActionAffordanceName]: ActionAffordance },
    /** All Event-based interaction affordances of the Thing. */
    events?: {[index: EventAffordanceName]: EventAffordance },
}



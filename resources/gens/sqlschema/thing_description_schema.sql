-- # Class: "VersionInfo" Description: "Provides version information."
--     * Slot: id Description: 
--     * Slot: instance Description: 
--     * Slot: model Description: 
-- # Class: "MultiLanguage" Description: ""
--     * Slot: key Description: 
--     * Slot: SecurityScheme_id Description: Autocreated FK slot
--     * Slot: InteractionAffordance_name Description: Autocreated FK slot
--     * Slot: PropertyAffordance_name Description: Autocreated FK slot
--     * Slot: ActionAffordance_name Description: Autocreated FK slot
--     * Slot: EventAffordance_name Description: Autocreated FK slot
--     * Slot: Thing_id Description: Autocreated FK slot
-- # Class: "Link" Description: "A link can be viewed as a statement of the form link context that has a relation type resource at link target", where the optional target attributes may further describe the resource."
--     * Slot: id Description: 
--     * Slot: target Description: Target IRI of a link or submission target of a Form
--     * Slot: hintsAtMediaType Description: Target attribute providing a hint indicating what the media type [IANA-MEDIA-TYPES] of the result of dereferencing the link should be.
--     * Slot: type Description: 
--     * Slot: relation Description: A link relation type identifies the semantics of a link.
--     * Slot: anchor Description: By default, the context, or anchor, of a link conveyed in the Link header field is the URL of the representation it is associated with, as defined in RFC7231, Section 3.1.4.1, and is serialized as a URI.
--     * Slot: sizes Description: Target attribute that specifies one or more sizes for the referenced icon. Only applicable for relation type 'icon'. The value pattern follows {Height}x{Width} (e.g., \"16x16\", \"16x16 32x32\").
--     * Slot: hreflang Description: The hreflang attribute specifies the language of a linked document. The value of this must be a valid language tag [[BCP47]].
-- # Class: "ExpectedResponse" Description: "Communication metadata describing the expected response message for the primary response."
--     * Slot: id Description: 
--     * Slot: contentType Description: TODO Check, was not in hctl ontology, if not could be source of discrepancy
-- # Class: "AdditionalExpectedResponse" Description: "Communication metadata describing the expected response message for additional responses."
--     * Slot: id Description: 
--     * Slot: additionalOutputSchema Description: This optional term can be used to define a data schema for an additional response if it differs from the default output data schema. Rather than a DataSchema object, the name of a previous definition given in a SchemaDefinitions map must be used.
--     * Slot: success Description: Signals if the additional response should not be considered an error.
--     * Slot: schema Description: TODO Check, was not in hctl ontology, if not could be source of discrepancy
--     * Slot: contentType Description: TODO Check, was not in hctl ontology, if not could be source of discrepancy
-- # Class: "Form" Description: "A form can be viewed as a statement of to perform an operation type on form context,  make a request method to submission target, where the optional form fields may further describe the required request. In Thing Descriptions, the form context is the surrounding Object,  such as Properties, Actions, and Events or the Thing itself for meta-interactions."
--     * Slot: id Description: 
--     * Slot: target Description: Target IRI of a link or submission target of a Form
--     * Slot: href Description: 
--     * Slot: contentType Description: Assign a content type based on a media type IANA-MEDIA-TYPES (e.g., 'text/plain') and potential parameters  (e.g., 'charset=utf-8') for the media type.
--     * Slot: contentCoding Description: Content coding values indicate an encoding transformation that has been or can be applied to a representation.  Content codings are primarily used to allow a representation to be compressed or otherwise usefully transformed  without losing the identity of its underlying media type and without loss of information. Examples of content coding include \"gzip\", \"deflate\", etc.
--     * Slot: securityDefinitions Description: A security schema applied to a (set of) affordance(s).
--     * Slot: scopes Description: TODO Check, was not in hctl ontology, if not could be source of discrepancy
--     * Slot: subprotocol Description: Indicates the exact mechanism by which an interaction will be accomplished for a given protocol when there are multiple options.
--     * Slot: returns_id Description: This optional term can be used if, e.g., the output communication metadata differ from input metadata (e.g., output contentType differ from the input contentType). The response name contains metadata that is only valid for the response messages.
-- # Class: "SecurityScheme" Description: ""
--     * Slot: id Description: 
--     * Slot: description Description: 
--     * Slot: proxy Description: URI of the proxy server this security configuration provides access to. If not given, the corresponding security configuration is for the endpoint.
--     * Slot: scheme Description: 
-- # Class: "DataSchema" Description: "Metadata that describes the data format used. It can be used for validation."
--     * Slot: id Description: 
--     * Slot: description Description: 
--     * Slot: title Description: Provides a human-readable title (e.g., display a text for UI representation) based on a default language.
--     * Slot: titleInLanguage Description: title of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
--     * Slot: descriptionInLanguage Description: description of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
--     * Slot: propertyName Description: Used to store the indexing name in the parent object when this schema appears as a property of an object schema.
--     * Slot: writeOnly Description: Boolean value that is a hint to indicate whether a property interaction/value is write only (=true) or not (=false).
--     * Slot: readonly Description: Boolean value that is a hint to indicate whether a property interaction/value is read only (=true) or not (=false).
-- # Class: "InteractionAffordance" Description: "TOOD"
--     * Slot: title Description: Provides a human-readable title (e.g., display a text for UI representation) based on a default language.
--     * Slot: description Description: 
--     * Slot: titleInLanguage Description: title of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
--     * Slot: descriptionInLanguage Description: description of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
--     * Slot: name Description: Indexing property to store entity names when serializing them in a JSON-LD @index container.
-- # Class: "PropertyAffordance" Description: "An Interaction Affordance that exposes state of the Thing. This state can be retrieved (read) and/or updated."
--     * Slot: observable Description: A hint that indicates whether Servients hosting the Thing and Intermediaries should probide a Protocol Binding  that supports the observeproperty and unobserveproperty operations for this Property.
--     * Slot: description Description: 
--     * Slot: title Description: Provides a human-readable title (e.g., display a text for UI representation) based on a default language.
--     * Slot: titleInLanguage Description: title of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
--     * Slot: descriptionInLanguage Description: description of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
--     * Slot: propertyName Description: Used to store the indexing name in the parent object when this schema appears as a property of an object schema.
--     * Slot: writeOnly Description: Boolean value that is a hint to indicate whether a property interaction/value is write only (=true) or not (=false).
--     * Slot: readonly Description: Boolean value that is a hint to indicate whether a property interaction/value is read only (=true) or not (=false).
--     * Slot: name Description: Indexing property to store entity names when serializing them in a JSON-LD @index container.
--     * Slot: Thing_id Description: Autocreated FK slot
-- # Class: "ActionAffordance" Description: "An Interaction Affordance that allows to invoke a function of the Thing, which manipulates state (e.g., toggling a lamp on or off) or triggers a process on the Thing (e.g., dim a lamp over time)."
--     * Slot: safe Description: Signals if the action is safe (=true) or not. Used to signal if there is no internal state (cf. resource state) is changed when invoking an Action.
--     * Slot: synchronous Description: Indicates whether the action is synchronous (=true) or not. A synchronous action means that the response of action contains all the information about the result of the action and no further querying about the status of the action is needed. Lack of this keyword means that no claim on the synchronicity of the action can be made.
--     * Slot: idempotent Description: Indicates whether the action is idempotent (=true) or not. Informs whether the action can be called repeatedly with the same results, if present, based on the same input.
--     * Slot: title Description: Provides a human-readable title (e.g., display a text for UI representation) based on a default language.
--     * Slot: description Description: 
--     * Slot: titleInLanguage Description: title of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
--     * Slot: descriptionInLanguage Description: description of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
--     * Slot: name Description: Indexing property to store entity names when serializing them in a JSON-LD @index container.
--     * Slot: Thing_id Description: Autocreated FK slot
--     * Slot: input_id Description: Used to define the input data schema of the action.
--     * Slot: output_id Description: Used to define the output data schema of the action.
-- # Class: "EventAffordance" Description: "An Interaction Affordance that describes an event source, which asynchronously pushes event data to Consumers (e.g., overhearing alerts)."
--     * Slot: title Description: Provides a human-readable title (e.g., display a text for UI representation) based on a default language.
--     * Slot: description Description: 
--     * Slot: titleInLanguage Description: title of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
--     * Slot: descriptionInLanguage Description: description of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
--     * Slot: name Description: Indexing property to store entity names when serializing them in a JSON-LD @index container.
--     * Slot: Thing_id Description: Autocreated FK slot
--     * Slot: subscription_id Description: Defines data that needs to be passed upon subscription, e.g., filters or message format for setting up Webhooks.
--     * Slot: cancellation_id Description: Defines any data that needs to be passed to cancel a subscription, e.g., a specific message to remove a Webhook.
--     * Slot: notification_id Description: Defines the data schema of the Event instance messages pushed by the Thing.
--     * Slot: notificationResponse_id Description: Defines the data schema of the Event response messages sent by the consumer in a response to a data message.
-- # Class: "Thing" Description: "An abstraction of a physical or a virtual entity whose metadata and interfaces are described by a WoT Thing Description, whereas a virtual entity is the composition of one or more Things."
--     * Slot: id Description: TODO
--     * Slot: title Description: Provides a human-readable title (e.g., display a text for UI representation) based on a default language.
--     * Slot: description Description: 
--     * Slot: titleInLanguage Description: title of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
--     * Slot: descriptionInLanguage Description: description of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description.
--     * Slot: instance Description: Provides a version identicator of this TD instance.
--     * Slot: created Description: Provides information when the TD instance was created.
--     * Slot: modified Description: Provides information when the TD instance was last modified.
--     * Slot: supportContact Description: Provides information about the TD maintainer as URI scheme (e.g., <code>mailto</code> [[RFC6068]],<code>tel</code> [[RFC3966]],<code>https</code> [[RFC9112]]).
--     * Slot: base Description: Define the base URI that is used for all relative URI references throughout a TD document.
--     * Slot: version_id Description: 
-- # Class: "Form_additionalReturns" Description: ""
--     * Slot: Form_id Description: Autocreated FK slot
--     * Slot: additionalReturns_id Description: This optional term can be used if additional expected responses are possible, e.g. for error reporting. Each additional response needs to be distinguished from others in some way (for example, by specifying a protocol-specific response code), and may also have its own data schema.
-- # Class: "Form_operationType" Description: ""
--     * Slot: Form_id Description: Autocreated FK slot
--     * Slot: operationType Description: Indicates the semantic intention of performing the operation(s) described by the form.
-- # Class: "SecurityScheme_@type" Description: ""
--     * Slot: SecurityScheme_id Description: Autocreated FK slot
--     * Slot: @type Description: 
-- # Class: "InteractionAffordance_uriVariables" Description: ""
--     * Slot: InteractionAffordance_name Description: Autocreated FK slot
--     * Slot: uriVariables_id Description: Define URI template variables according to RFC6570 as collection based on schema specifications. The individual variables DataSchema cannot be an ObjectSchema or an ArraySchema. TODO: range is not obvious from the ontology.
-- # Class: "InteractionAffordance_forms" Description: ""
--     * Slot: InteractionAffordance_name Description: Autocreated FK slot
--     * Slot: forms_id Description: Set of form hypermedia controls that describe how an operation can be performed.
-- # Class: "PropertyAffordance_uriVariables" Description: ""
--     * Slot: PropertyAffordance_name Description: Autocreated FK slot
--     * Slot: uriVariables_id Description: Define URI template variables according to RFC6570 as collection based on schema specifications. The individual variables DataSchema cannot be an ObjectSchema or an ArraySchema. TODO: range is not obvious from the ontology.
-- # Class: "PropertyAffordance_forms" Description: ""
--     * Slot: PropertyAffordance_name Description: Autocreated FK slot
--     * Slot: forms_id Description: Set of form hypermedia controls that describe how an operation can be performed.
-- # Class: "ActionAffordance_uriVariables" Description: ""
--     * Slot: ActionAffordance_name Description: Autocreated FK slot
--     * Slot: uriVariables_id Description: Define URI template variables according to RFC6570 as collection based on schema specifications. The individual variables DataSchema cannot be an ObjectSchema or an ArraySchema. TODO: range is not obvious from the ontology.
-- # Class: "ActionAffordance_forms" Description: ""
--     * Slot: ActionAffordance_name Description: Autocreated FK slot
--     * Slot: forms_id Description: Set of form hypermedia controls that describe how an operation can be performed.
-- # Class: "EventAffordance_uriVariables" Description: ""
--     * Slot: EventAffordance_name Description: Autocreated FK slot
--     * Slot: uriVariables_id Description: Define URI template variables according to RFC6570 as collection based on schema specifications. The individual variables DataSchema cannot be an ObjectSchema or an ArraySchema. TODO: range is not obvious from the ontology.
-- # Class: "EventAffordance_forms" Description: ""
--     * Slot: EventAffordance_name Description: Autocreated FK slot
--     * Slot: forms_id Description: Set of form hypermedia controls that describe how an operation can be performed.
-- # Class: "Thing_@type" Description: ""
--     * Slot: Thing_id Description: Autocreated FK slot
--     * Slot: @type Description: 
-- # Class: "Thing_securityDefinitions" Description: ""
--     * Slot: Thing_id Description: Autocreated FK slot
--     * Slot: securityDefinitions Description: A security scheme applied to a (set of) affordance(s). TODO check
-- # Class: "Thing_security" Description: ""
--     * Slot: Thing_id Description: Autocreated FK slot
--     * Slot: security Description: A Thing may define abstract security schemes, used to configure the secure access of (a set of) affordance(s). TODO: check
-- # Class: "Thing_schemaDefinitions" Description: ""
--     * Slot: Thing_id Description: Autocreated FK slot
--     * Slot: schemaDefinitions_id Description: TODO CHECK
-- # Class: "Thing_profile" Description: ""
--     * Slot: Thing_id Description: Autocreated FK slot
--     * Slot: profile Description: Indicates the WoT Profile mechanisms followed by this Thing Description and the corresponding Thing implementation.
-- # Class: "Thing_forms" Description: ""
--     * Slot: Thing_id Description: Autocreated FK slot
--     * Slot: forms_id Description: Set of form hypermedia controls that describe how an operation can be performed. Forms are serializations of Protocol Bindings.
-- # Class: "Thing_links" Description: ""
--     * Slot: Thing_id Description: Autocreated FK slot
--     * Slot: links_id Description: Provides Web links to arbitrary resources that relate to the specified Thing Description.

CREATE TABLE "VersionInfo" (
	id INTEGER NOT NULL, 
	instance TEXT NOT NULL, 
	model TEXT, 
	PRIMARY KEY (id)
);
CREATE TABLE "MultiLanguage" (
	"key" TEXT NOT NULL, 
	"SecurityScheme_id" INTEGER, 
	"InteractionAffordance_name" TEXT, 
	"PropertyAffordance_name" TEXT, 
	"ActionAffordance_name" TEXT, 
	"EventAffordance_name" TEXT, 
	"Thing_id" TEXT, 
	PRIMARY KEY ("key"), 
	FOREIGN KEY("SecurityScheme_id") REFERENCES "SecurityScheme" (id), 
	FOREIGN KEY("InteractionAffordance_name") REFERENCES "InteractionAffordance" (name), 
	FOREIGN KEY("PropertyAffordance_name") REFERENCES "PropertyAffordance" (name), 
	FOREIGN KEY("ActionAffordance_name") REFERENCES "ActionAffordance" (name), 
	FOREIGN KEY("EventAffordance_name") REFERENCES "EventAffordance" (name), 
	FOREIGN KEY("Thing_id") REFERENCES "Thing" (id)
);
CREATE TABLE "Link" (
	id INTEGER NOT NULL, 
	target TEXT NOT NULL, 
	"hintsAtMediaType" TEXT, 
	type TEXT, 
	relation TEXT, 
	anchor TEXT, 
	sizes TEXT, 
	hreflang TEXT, 
	PRIMARY KEY (id)
);
CREATE TABLE "ExpectedResponse" (
	id INTEGER NOT NULL, 
	"contentType" TEXT NOT NULL, 
	PRIMARY KEY (id)
);
CREATE TABLE "AdditionalExpectedResponse" (
	id INTEGER NOT NULL, 
	"additionalOutputSchema" TEXT, 
	success BOOLEAN, 
	schema TEXT, 
	"contentType" TEXT NOT NULL, 
	PRIMARY KEY (id)
);
CREATE TABLE "SecurityScheme" (
	id INTEGER NOT NULL, 
	description TEXT, 
	proxy TEXT, 
	scheme VARCHAR(6) NOT NULL, 
	PRIMARY KEY (id)
);
CREATE TABLE "DataSchema" (
	id INTEGER NOT NULL, 
	description TEXT, 
	title TEXT, 
	"titleInLanguage" TEXT, 
	"descriptionInLanguage" TEXT, 
	"propertyName" TEXT, 
	"writeOnly" TEXT, 
	readonly TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(description) REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY(title) REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY("titleInLanguage") REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY("descriptionInLanguage") REFERENCES "MultiLanguage" ("key")
);
CREATE TABLE "InteractionAffordance" (
	title TEXT, 
	description TEXT, 
	"titleInLanguage" TEXT, 
	"descriptionInLanguage" TEXT, 
	name TEXT NOT NULL, 
	PRIMARY KEY (name), 
	FOREIGN KEY(title) REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY(description) REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY("titleInLanguage") REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY("descriptionInLanguage") REFERENCES "MultiLanguage" ("key")
);
CREATE TABLE "PropertyAffordance" (
	observable BOOLEAN, 
	description TEXT, 
	title TEXT, 
	"titleInLanguage" TEXT, 
	"descriptionInLanguage" TEXT, 
	"propertyName" TEXT, 
	"writeOnly" TEXT, 
	readonly TEXT, 
	name TEXT NOT NULL, 
	"Thing_id" TEXT, 
	PRIMARY KEY (name), 
	FOREIGN KEY(description) REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY(title) REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY("titleInLanguage") REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY("descriptionInLanguage") REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY("Thing_id") REFERENCES "Thing" (id)
);
CREATE TABLE "ActionAffordance" (
	safe BOOLEAN, 
	synchronous BOOLEAN, 
	idempotent BOOLEAN, 
	title TEXT, 
	description TEXT, 
	"titleInLanguage" TEXT, 
	"descriptionInLanguage" TEXT, 
	name TEXT NOT NULL, 
	"Thing_id" TEXT, 
	input_id INTEGER, 
	output_id INTEGER, 
	PRIMARY KEY (name), 
	FOREIGN KEY(title) REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY(description) REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY("titleInLanguage") REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY("descriptionInLanguage") REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY("Thing_id") REFERENCES "Thing" (id), 
	FOREIGN KEY(input_id) REFERENCES "DataSchema" (id), 
	FOREIGN KEY(output_id) REFERENCES "DataSchema" (id)
);
CREATE TABLE "EventAffordance" (
	title TEXT, 
	description TEXT, 
	"titleInLanguage" TEXT, 
	"descriptionInLanguage" TEXT, 
	name TEXT NOT NULL, 
	"Thing_id" TEXT, 
	subscription_id INTEGER, 
	cancellation_id INTEGER, 
	notification_id INTEGER, 
	"notificationResponse_id" INTEGER, 
	PRIMARY KEY (name), 
	FOREIGN KEY(title) REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY(description) REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY("titleInLanguage") REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY("descriptionInLanguage") REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY("Thing_id") REFERENCES "Thing" (id), 
	FOREIGN KEY(subscription_id) REFERENCES "DataSchema" (id), 
	FOREIGN KEY(cancellation_id) REFERENCES "DataSchema" (id), 
	FOREIGN KEY(notification_id) REFERENCES "DataSchema" (id), 
	FOREIGN KEY("notificationResponse_id") REFERENCES "DataSchema" (id)
);
CREATE TABLE "Thing" (
	id TEXT NOT NULL, 
	title TEXT, 
	description TEXT, 
	"titleInLanguage" TEXT, 
	"descriptionInLanguage" TEXT, 
	instance TEXT, 
	created DATETIME, 
	modified DATETIME, 
	"supportContact" TEXT, 
	base TEXT, 
	version_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(title) REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY(description) REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY("titleInLanguage") REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY("descriptionInLanguage") REFERENCES "MultiLanguage" ("key"), 
	FOREIGN KEY(version_id) REFERENCES "VersionInfo" (id)
);
CREATE TABLE "Form" (
	id INTEGER NOT NULL, 
	target TEXT NOT NULL, 
	href TEXT NOT NULL, 
	"contentType" TEXT, 
	"contentCoding" TEXT, 
	"securityDefinitions" TEXT, 
	scopes TEXT, 
	subprotocol TEXT, 
	returns_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(returns_id) REFERENCES "ExpectedResponse" (id)
);
CREATE TABLE "SecurityScheme_@type" (
	"SecurityScheme_id" INTEGER, 
	"@type" TEXT, 
	PRIMARY KEY ("SecurityScheme_id", "@type"), 
	FOREIGN KEY("SecurityScheme_id") REFERENCES "SecurityScheme" (id)
);
CREATE TABLE "InteractionAffordance_uriVariables" (
	"InteractionAffordance_name" TEXT, 
	"uriVariables_id" INTEGER, 
	PRIMARY KEY ("InteractionAffordance_name", "uriVariables_id"), 
	FOREIGN KEY("InteractionAffordance_name") REFERENCES "InteractionAffordance" (name), 
	FOREIGN KEY("uriVariables_id") REFERENCES "DataSchema" (id)
);
CREATE TABLE "PropertyAffordance_uriVariables" (
	"PropertyAffordance_name" TEXT, 
	"uriVariables_id" INTEGER, 
	PRIMARY KEY ("PropertyAffordance_name", "uriVariables_id"), 
	FOREIGN KEY("PropertyAffordance_name") REFERENCES "PropertyAffordance" (name), 
	FOREIGN KEY("uriVariables_id") REFERENCES "DataSchema" (id)
);
CREATE TABLE "ActionAffordance_uriVariables" (
	"ActionAffordance_name" TEXT, 
	"uriVariables_id" INTEGER, 
	PRIMARY KEY ("ActionAffordance_name", "uriVariables_id"), 
	FOREIGN KEY("ActionAffordance_name") REFERENCES "ActionAffordance" (name), 
	FOREIGN KEY("uriVariables_id") REFERENCES "DataSchema" (id)
);
CREATE TABLE "EventAffordance_uriVariables" (
	"EventAffordance_name" TEXT, 
	"uriVariables_id" INTEGER, 
	PRIMARY KEY ("EventAffordance_name", "uriVariables_id"), 
	FOREIGN KEY("EventAffordance_name") REFERENCES "EventAffordance" (name), 
	FOREIGN KEY("uriVariables_id") REFERENCES "DataSchema" (id)
);
CREATE TABLE "Thing_@type" (
	"Thing_id" TEXT, 
	"@type" TEXT, 
	PRIMARY KEY ("Thing_id", "@type"), 
	FOREIGN KEY("Thing_id") REFERENCES "Thing" (id)
);
CREATE TABLE "Thing_securityDefinitions" (
	"Thing_id" TEXT, 
	"securityDefinitions" TEXT, 
	PRIMARY KEY ("Thing_id", "securityDefinitions"), 
	FOREIGN KEY("Thing_id") REFERENCES "Thing" (id)
);
CREATE TABLE "Thing_security" (
	"Thing_id" TEXT, 
	security TEXT, 
	PRIMARY KEY ("Thing_id", security), 
	FOREIGN KEY("Thing_id") REFERENCES "Thing" (id)
);
CREATE TABLE "Thing_schemaDefinitions" (
	"Thing_id" TEXT, 
	"schemaDefinitions_id" INTEGER, 
	PRIMARY KEY ("Thing_id", "schemaDefinitions_id"), 
	FOREIGN KEY("Thing_id") REFERENCES "Thing" (id), 
	FOREIGN KEY("schemaDefinitions_id") REFERENCES "DataSchema" (id)
);
CREATE TABLE "Thing_profile" (
	"Thing_id" TEXT, 
	profile TEXT, 
	PRIMARY KEY ("Thing_id", profile), 
	FOREIGN KEY("Thing_id") REFERENCES "Thing" (id)
);
CREATE TABLE "Thing_links" (
	"Thing_id" TEXT, 
	links_id INTEGER, 
	PRIMARY KEY ("Thing_id", links_id), 
	FOREIGN KEY("Thing_id") REFERENCES "Thing" (id), 
	FOREIGN KEY(links_id) REFERENCES "Link" (id)
);
CREATE TABLE "Form_additionalReturns" (
	"Form_id" INTEGER, 
	"additionalReturns_id" INTEGER, 
	PRIMARY KEY ("Form_id", "additionalReturns_id"), 
	FOREIGN KEY("Form_id") REFERENCES "Form" (id), 
	FOREIGN KEY("additionalReturns_id") REFERENCES "AdditionalExpectedResponse" (id)
);
CREATE TABLE "Form_operationType" (
	"Form_id" INTEGER, 
	"operationType" VARCHAR(23), 
	PRIMARY KEY ("Form_id", "operationType"), 
	FOREIGN KEY("Form_id") REFERENCES "Form" (id)
);
CREATE TABLE "InteractionAffordance_forms" (
	"InteractionAffordance_name" TEXT, 
	forms_id INTEGER, 
	PRIMARY KEY ("InteractionAffordance_name", forms_id), 
	FOREIGN KEY("InteractionAffordance_name") REFERENCES "InteractionAffordance" (name), 
	FOREIGN KEY(forms_id) REFERENCES "Form" (id)
);
CREATE TABLE "PropertyAffordance_forms" (
	"PropertyAffordance_name" TEXT, 
	forms_id INTEGER, 
	PRIMARY KEY ("PropertyAffordance_name", forms_id), 
	FOREIGN KEY("PropertyAffordance_name") REFERENCES "PropertyAffordance" (name), 
	FOREIGN KEY(forms_id) REFERENCES "Form" (id)
);
CREATE TABLE "ActionAffordance_forms" (
	"ActionAffordance_name" TEXT, 
	forms_id INTEGER, 
	PRIMARY KEY ("ActionAffordance_name", forms_id), 
	FOREIGN KEY("ActionAffordance_name") REFERENCES "ActionAffordance" (name), 
	FOREIGN KEY(forms_id) REFERENCES "Form" (id)
);
CREATE TABLE "EventAffordance_forms" (
	"EventAffordance_name" TEXT, 
	forms_id INTEGER, 
	PRIMARY KEY ("EventAffordance_name", forms_id), 
	FOREIGN KEY("EventAffordance_name") REFERENCES "EventAffordance" (name), 
	FOREIGN KEY(forms_id) REFERENCES "Form" (id)
);
CREATE TABLE "Thing_forms" (
	"Thing_id" TEXT, 
	forms_id INTEGER, 
	PRIMARY KEY ("Thing_id", forms_id), 
	FOREIGN KEY("Thing_id") REFERENCES "Thing" (id), 
	FOREIGN KEY(forms_id) REFERENCES "Form" (id)
);
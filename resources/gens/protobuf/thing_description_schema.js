 syntax="proto3";
 package
// metamodel_version: 1.7.0
// An Interaction Affordance that allows to invoke a function of the Thing, which manipulates state (e.g., toggling a lamp on or off) or triggers a process on the Thing (e.g., dim a lamp over time).
message ActionAffordance
 {
 repeated  multiLanguage titles = 0
 repeated  multiLanguage descriptions = 0
  multiLanguage title = 0
  multiLanguage description = 0
  multiLanguage titleInLanguage = 0
  multiLanguage descriptionInLanguage = 0
  string name = 0
 repeated  dataSchema uriVariables = 0
 repeated  form forms = 0
  boolean safe = 0
  boolean synchronous = 0
  boolean idempotent = 0
  dataSchema input = 0
  dataSchema output = 0
 }
// Communication metadata describing the expected response message for additional responses.
message AdditionalExpectedResponse
 {
  string contentType = 0
  string additionalOutputSchema = 0
  boolean success = 0
  string schema = 0
 }
// Metadata that describes the data format used. It can be used for validation.
message DataSchema
 {
  multiLanguage description = 0
  multiLanguage title = 0
  multiLanguage titleInLanguage = 0
  multiLanguage descriptionInLanguage = 0
  string propertyName = 0
  string writeOnly = 0
  string readonly = 0
 }
// An Interaction Affordance that describes an event source, which asynchronously pushes event data to Consumers (e.g., overhearing alerts).
message EventAffordance
 {
 repeated  multiLanguage titles = 0
 repeated  multiLanguage descriptions = 0
  multiLanguage title = 0
  multiLanguage description = 0
  multiLanguage titleInLanguage = 0
  multiLanguage descriptionInLanguage = 0
  string name = 0
 repeated  dataSchema uriVariables = 0
 repeated  form forms = 0
  dataSchema subscription = 0
  dataSchema cancellation = 0
  dataSchema notification = 0
  dataSchema notificationResponse = 0
 }
// Communication metadata describing the expected response message for the primary response.
message ExpectedResponse
 {
  string contentType = 0
 }
// A form can be viewed as a statement of to perform an operation type on form context,  make a request method to submission target, where the optional form fields may further describe the required request. In Thing Descriptions, the form context is the surrounding Object,  such as Properties, Actions, and Events or the Thing itself for meta-interactions.
message Form
 {
  anyUri target = 0
  anyUri href = 0
  string contentType = 0
  string contentCoding = 0
  string securityDefinitions = 0
  string scopes = 0
  expectedResponse returns = 0
 repeated  additionalExpectedResponse additionalReturns = 0
  string subprotocol = 0
 repeated  operationTypes operationType = 0
 }
// TOOD
message InteractionAffordance
 {
 repeated  multiLanguage titles = 0
 repeated  multiLanguage descriptions = 0
  multiLanguage title = 0
  multiLanguage description = 0
  multiLanguage titleInLanguage = 0
  multiLanguage descriptionInLanguage = 0
  string name = 0
 repeated  dataSchema uriVariables = 0
 repeated  form forms = 0
 }
// A link can be viewed as a statement of the form link context that has a relation type resource at link target", where the optional target attributes may further describe the resource.
message Link
 {
  anyUri target = 0
  string hintsAtMediaType = 0
  string type = 0
  string relation = 0
  anyUri anchor = 0
  string sizes = 0
  string hreflang = 0
 }
message MultiLanguage
 {
  string key = 0
 }
// An Interaction Affordance that exposes state of the Thing. This state can be retrieved (read) and/or updated.
message PropertyAffordance
 {
 repeated  multiLanguage titles = 0
 repeated  multiLanguage descriptions = 0
  multiLanguage title = 0
  multiLanguage description = 0
  multiLanguage titleInLanguage = 0
  multiLanguage descriptionInLanguage = 0
  string name = 0
 repeated  dataSchema uriVariables = 0
 repeated  form forms = 0
  boolean observable = 0
  string propertyName = 0
  string writeOnly = 0
  string readonly = 0
 }
message SecurityScheme
 {
 repeated  string @type = 0
 repeated  multiLanguage descriptions = 0
  string description = 0
  anyUri proxy = 0
  securitySchemeType scheme = 0
 }
// An abstraction of a physical or a virtual entity whose metadata and interfaces are described by a WoT Thing Description, whereas a virtual entity is the composition of one or more Things.
message Thing
 {
  anyUri id = 0
  multiLanguage title = 0
  multiLanguage description = 0
 repeated  multiLanguage titles = 0
 repeated  multiLanguage descriptions = 0
 repeated  string @type = 0
  multiLanguage titleInLanguage = 0
  multiLanguage descriptionInLanguage = 0
 repeated  string securityDefinitions = 0
 repeated  string security = 0
 repeated  dataSchema schemaDefinitions = 0
 repeated  anyUri profile = 0
  string instance = 0
  datetime created = 0
  datetime modified = 0
  anyUri supportContact = 0
  anyUri base = 0
  versionInfo version = 0
 repeated  form forms = 0
 repeated  link links = 0
 repeated  propertyAffordance properties = 0
 repeated  actionAffordance actions = 0
 repeated  eventAffordance events = 0
 }
// Provides version information.
message VersionInfo
 {
  string instance = 0
  string model = 0
 }


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

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
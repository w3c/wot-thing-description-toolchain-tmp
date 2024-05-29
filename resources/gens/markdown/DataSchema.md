
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
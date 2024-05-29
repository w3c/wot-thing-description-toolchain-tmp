
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
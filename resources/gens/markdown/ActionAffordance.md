
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
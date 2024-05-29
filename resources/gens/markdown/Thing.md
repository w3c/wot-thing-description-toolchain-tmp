
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
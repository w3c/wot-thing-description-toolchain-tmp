

# Slot: descriptionInLanguage


_description of the TD element (Thing, interaction affordance, security scheme or data scheme) with language tag. By convention, a language tag must be added to the object of descriptionInLanguage. Otherwise use description._



URI: [td:descriptionInLanguage](https://www.w3.org/2019/wot/td#descriptionInLanguage)



<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [DataSchema](DataSchema.md) | Metadata that describes the data format used |  no  |
| [PropertyAffordance](PropertyAffordance.md) | An Interaction Affordance that exposes state of the Thing |  no  |
| [Thing](Thing.md) | An abstraction of a physical or a virtual entity whose metadata and interface... |  no  |
| [EventAffordance](EventAffordance.md) | An Interaction Affordance that describes an event source, which asynchronousl... |  no  |
| [InteractionAffordance](InteractionAffordance.md) | TOOD |  no  |
| [ActionAffordance](ActionAffordance.md) | An Interaction Affordance that allows to invoke a function of the Thing, whic... |  no  |







## Properties

* Range: [MultiLanguage](MultiLanguage.md)





## Identifier and Mapping Information







### Schema Source


* from schema: td




## LinkML Source

<details>
```yaml
name: descriptionInLanguage
description: description of the TD element (Thing, interaction affordance, security
  scheme or data scheme) with language tag. By convention, a language tag must be
  added to the object of descriptionInLanguage. Otherwise use description.
from_schema: td
rank: 1000
alias: descriptionInLanguage
domain_of:
- DataSchema
- InteractionAffordance
- Thing
range: MultiLanguage

```
</details>
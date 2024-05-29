

# Slot: title


_Provides a human-readable title (e.g., display a text for UI representation) based on a default language._



URI: [td:title](https://www.w3.org/2019/wot/td#title)



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
name: title
description: Provides a human-readable title (e.g., display a text for UI representation)
  based on a default language.
from_schema: td
rank: 1000
slot_uri: td:title
alias: title
domain_of:
- DataSchema
- InteractionAffordance
- Thing
range: MultiLanguage

```
</details>
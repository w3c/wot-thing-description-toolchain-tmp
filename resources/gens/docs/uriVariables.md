

# Slot: uriVariables


_Define URI template variables according to RFC6570 as collection based on schema specifications. The individual variables DataSchema cannot be an ObjectSchema or an ArraySchema. TODO: range is not obvious from the ontology._



URI: [td:uriVariables](https://www.w3.org/2019/wot/td#uriVariables)



<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [PropertyAffordance](PropertyAffordance.md) | An Interaction Affordance that exposes state of the Thing |  no  |
| [InteractionAffordance](InteractionAffordance.md) | TOOD |  no  |
| [ActionAffordance](ActionAffordance.md) | An Interaction Affordance that allows to invoke a function of the Thing, whic... |  no  |
| [EventAffordance](EventAffordance.md) | An Interaction Affordance that describes an event source, which asynchronousl... |  no  |







## Properties

* Range: [DataSchema](DataSchema.md)

* Multivalued: True





## Identifier and Mapping Information







### Schema Source


* from schema: td




## LinkML Source

<details>
```yaml
name: uriVariables
description: 'Define URI template variables according to RFC6570 as collection based
  on schema specifications. The individual variables DataSchema cannot be an ObjectSchema
  or an ArraySchema. TODO: range is not obvious from the ontology.'
from_schema: td
rank: 1000
multivalued: true
alias: uriVariables
owner: InteractionAffordance
domain_of:
- InteractionAffordance
range: DataSchema

```
</details>
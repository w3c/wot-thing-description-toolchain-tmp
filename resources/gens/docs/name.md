

# Slot: name


_Indexing property to store entity names when serializing them in a JSON-LD @index container._



URI: [td:name](https://www.w3.org/2019/wot/td#name)



<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ActionAffordance](ActionAffordance.md) | An Interaction Affordance that allows to invoke a function of the Thing, whic... |  no  |
| [EventAffordance](EventAffordance.md) | An Interaction Affordance that describes an event source, which asynchronousl... |  no  |
| [PropertyAffordance](PropertyAffordance.md) | An Interaction Affordance that exposes state of the Thing |  no  |
| [InteractionAffordance](InteractionAffordance.md) | TOOD |  no  |







## Properties

* Range: [String](String.md)

* Required: True





## Identifier and Mapping Information







### Schema Source


* from schema: td




## LinkML Source

<details>
```yaml
name: name
description: Indexing property to store entity names when serializing them in a JSON-LD
  @index container.
from_schema: td
rank: 1000
identifier: true
alias: name
owner: InteractionAffordance
domain_of:
- InteractionAffordance
range: string
required: true

```
</details>
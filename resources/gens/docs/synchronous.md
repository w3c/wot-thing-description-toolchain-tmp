

# Slot: synchronous


_Indicates whether the action is synchronous (=true) or not. A synchronous action means that the response of action contains all the information about the result of the action and no further querying about the status of the action is needed. Lack of this keyword means that no claim on the synchronicity of the action can be made._



URI: [td:synchronous](https://www.w3.org/2019/wot/td#synchronous)



<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ActionAffordance](ActionAffordance.md) | An Interaction Affordance that allows to invoke a function of the Thing, whic... |  no  |







## Properties

* Range: [Boolean](Boolean.md)





## Identifier and Mapping Information







### Schema Source


* from schema: td




## LinkML Source

<details>
```yaml
name: synchronous
description: Indicates whether the action is synchronous (=true) or not. A synchronous
  action means that the response of action contains all the information about the
  result of the action and no further querying about the status of the action is needed.
  Lack of this keyword means that no claim on the synchronicity of the action can
  be made.
from_schema: td
rank: 1000
alias: synchronous
owner: ActionAffordance
domain_of:
- ActionAffordance
range: boolean

```
</details>
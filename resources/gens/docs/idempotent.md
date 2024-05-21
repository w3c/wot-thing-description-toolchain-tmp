

# Slot: idempotent


_Indicates whether the action is idempotent (=true) or not. Informs whether the action can be called repeatedly with the same results, if present, based on the same input._



URI: [td:idempotent](https://www.w3.org/2019/wot/td#idempotent)



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
name: idempotent
description: Indicates whether the action is idempotent (=true) or not. Informs whether
  the action can be called repeatedly with the same results, if present, based on
  the same input.
from_schema: td
rank: 1000
alias: idempotent
owner: ActionAffordance
domain_of:
- ActionAffordance
range: boolean

```
</details>
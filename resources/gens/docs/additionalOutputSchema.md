

# Slot: additionalOutputSchema


_This optional term can be used to define a data schema for an additional response if it differs from the default output data schema. Rather than a DataSchema object, the name of a previous definition given in a SchemaDefinitions map must be used._



URI: [td:additionalOutputSchema](https://www.w3.org/2019/wot/td#additionalOutputSchema)



<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [AdditionalExpectedResponse](AdditionalExpectedResponse.md) | Communication metadata describing the expected response message for additiona... |  no  |







## Properties

* Range: [String](String.md)





## Identifier and Mapping Information







### Schema Source


* from schema: td




## LinkML Source

<details>
```yaml
name: additionalOutputSchema
description: This optional term can be used to define a data schema for an additional
  response if it differs from the default output data schema. Rather than a DataSchema
  object, the name of a previous definition given in a SchemaDefinitions map must
  be used.
from_schema: td
rank: 1000
alias: additionalOutputSchema
owner: AdditionalExpectedResponse
domain_of:
- AdditionalExpectedResponse
range: string

```
</details>
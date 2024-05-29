

# Slot: additionalReturns


_This optional term can be used if additional expected responses are possible, e.g. for error reporting. Each additional response needs to be distinguished from others in some way (for example, by specifying a protocol-specific response code), and may also have its own data schema._



URI: [td:additionalReturns](https://www.w3.org/2019/wot/td#additionalReturns)



<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Form](Form.md) | A form can be viewed as a statement of to perform an operation type on form c... |  no  |







## Properties

* Range: [AdditionalExpectedResponse](AdditionalExpectedResponse.md)

* Multivalued: True





## Identifier and Mapping Information







### Schema Source


* from schema: td




## LinkML Source

<details>
```yaml
name: additionalReturns
description: This optional term can be used if additional expected responses are possible,
  e.g. for error reporting. Each additional response needs to be distinguished from
  others in some way (for example, by specifying a protocol-specific response code),
  and may also have its own data schema.
from_schema: td
rank: 1000
multivalued: true
alias: additionalReturns
owner: Form
domain_of:
- Form
range: AdditionalExpectedResponse

```
</details>
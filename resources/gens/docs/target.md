

# Slot: target


_Target IRI of a link or submission target of a Form_



URI: [hctl:target](https://www.w3.org/2019/wot/hypermedia#target)



<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Form](Form.md) | A form can be viewed as a statement of to perform an operation type on form c... |  no  |
| [Link](Link.md) | A link can be viewed as a statement of the form link context that has a relat... |  no  |







## Properties

* Range: [AnyUri](AnyUri.md)

* Required: True





## Identifier and Mapping Information







### Schema Source


* from schema: td




## LinkML Source

<details>
```yaml
name: target
description: Target IRI of a link or submission target of a Form
from_schema: td
rank: 1000
slot_uri: hctl:target
alias: target
domain_of:
- Link
- Form
range: anyUri
required: true

```
</details>
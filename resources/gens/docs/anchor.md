

# Slot: anchor


_By default, the context, or anchor, of a link conveyed in the Link header field is the URL of the representation it is associated with, as defined in RFC7231, Section 3.1.4.1, and is serialized as a URI._



URI: [td:anchor](https://www.w3.org/2019/wot/td#anchor)



<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Link](Link.md) | A link can be viewed as a statement of the form link context that has a relat... |  no  |







## Properties

* Range: [AnyUri](AnyUri.md)





## Identifier and Mapping Information







### Schema Source


* from schema: td




## LinkML Source

<details>
```yaml
name: anchor
description: By default, the context, or anchor, of a link conveyed in the Link header
  field is the URL of the representation it is associated with, as defined in RFC7231,
  Section 3.1.4.1, and is serialized as a URI.
from_schema: td
rank: 1000
alias: anchor
owner: Link
domain_of:
- Link
range: anyUri

```
</details>


# Slot: sizes


_Target attribute that specifies one or more sizes for the referenced icon. Only applicable for relation type 'icon'. The value pattern follows {Height}x{Width} (e.g., \"16x16\", \"16x16 32x32\")._



URI: [td:sizes](https://www.w3.org/2019/wot/td#sizes)



<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Link](Link.md) | A link can be viewed as a statement of the form link context that has a relat... |  no  |







## Properties

* Range: [String](String.md)





## Identifier and Mapping Information







### Schema Source


* from schema: td




## LinkML Source

<details>
```yaml
name: sizes
description: Target attribute that specifies one or more sizes for the referenced
  icon. Only applicable for relation type 'icon'. The value pattern follows {Height}x{Width}
  (e.g., \"16x16\", \"16x16 32x32\").
from_schema: td
rank: 1000
alias: sizes
owner: Link
domain_of:
- Link
range: string

```
</details>
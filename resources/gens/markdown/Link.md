
# Class: Link

A link can be viewed as a statement of the form link context that has a relation type resource at link target", where the optional target attributes may further describe the resource.

URI: [td:Link](https://www.w3.org/2019/wot/td#Link)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[Thing]++-%20links%200..*>[Link&#124;target:anyUri;hintsAtMediaType:string%20%3F;type:string%20%3F;relation:string%20%3F;anchor:anyUri%20%3F;sizes:string%20%3F;hreflang:string%20%3F],[Thing])](https://yuml.me/diagram/nofunky;dir:TB/class/[Thing]++-%20links%200..*>[Link&#124;target:anyUri;hintsAtMediaType:string%20%3F;type:string%20%3F;relation:string%20%3F;anchor:anyUri%20%3F;sizes:string%20%3F;hreflang:string%20%3F],[Thing])

## Referenced by Class

 *  **None** *[➞links](thing__links.md)*  <sub>0..\*</sub>  **[Link](Link.md)**

## Attributes


### Own

 * [target](target.md)  <sub>1..1</sub>
     * Description: Target IRI of a link or submission target of a Form
     * Range: [AnyUri](types/AnyUri.md)
 * [➞hintsAtMediaType](link__hintsAtMediaType.md)  <sub>0..1</sub>
     * Description: Target attribute providing a hint indicating what the media type [IANA-MEDIA-TYPES] of the result of dereferencing the link should be.
     * Range: [String](types/String.md)
 * [➞type](link__type.md)  <sub>0..1</sub>
     * Range: [String](types/String.md)
 * [➞relation](link__relation.md)  <sub>0..1</sub>
     * Description: A link relation type identifies the semantics of a link.
     * Range: [String](types/String.md)
 * [➞anchor](link__anchor.md)  <sub>0..1</sub>
     * Description: By default, the context, or anchor, of a link conveyed in the Link header field is the URL of the representation it is associated with, as defined in RFC7231, Section 3.1.4.1, and is serialized as a URI.
     * Range: [AnyUri](types/AnyUri.md)
 * [➞sizes](link__sizes.md)  <sub>0..1</sub>
     * Description: Target attribute that specifies one or more sizes for the referenced icon. Only applicable for relation type 'icon'. The value pattern follows {Height}x{Width} (e.g., \"16x16\", \"16x16 32x32\").
     * Range: [String](types/String.md)
 * [➞hreflang](link__hreflang.md)  <sub>0..1</sub>
     * Description: The hreflang attribute specifies the language of a linked document. The value of this must be a valid language tag [[BCP47]].
     * Range: [String](types/String.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Mappings:** | | hctl:Link |
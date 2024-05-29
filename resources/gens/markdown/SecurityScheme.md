
# Class: SecurityScheme



URI: [td:SecurityScheme](https://www.w3.org/2019/wot/td#SecurityScheme)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[MultiLanguage]<descriptions%200..*-++[SecurityScheme&#124;@type:string%20*;description:string%20%3F;proxy:anyUri%20%3F;scheme:SecuritySchemeType],[MultiLanguage])](https://yuml.me/diagram/nofunky;dir:TB/class/[MultiLanguage]<descriptions%200..*-++[SecurityScheme&#124;@type:string%20*;description:string%20%3F;proxy:anyUri%20%3F;scheme:SecuritySchemeType],[MultiLanguage])

## Attributes


### Own

 * [@type](@type.md)  <sub>0..\*</sub>
     * Range: [String](types/String.md)
 * [descriptions](descriptions.md)  <sub>0..\*</sub>
     * Description: TODO, check, according to the description a description should not contain a lang tag.
     * Range: [MultiLanguage](MultiLanguage.md)
 * [➞description](securityScheme__description.md)  <sub>0..1</sub>
     * Range: [String](types/String.md)
 * [➞proxy](securityScheme__proxy.md)  <sub>0..1</sub>
     * Description: URI of the proxy server this security configuration provides access to. If not given, the corresponding security configuration is for the endpoint.
     * Range: [AnyUri](types/AnyUri.md)
 * [➞scheme](securityScheme__scheme.md)  <sub>1..1</sub>
     * Range: [SecuritySchemeType](SecuritySchemeType.md)

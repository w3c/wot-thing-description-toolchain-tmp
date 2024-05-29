
# Class: ExpectedResponse

Communication metadata describing the expected response message for the primary response.

URI: [td:ExpectedResponse](https://www.w3.org/2019/wot/td#ExpectedResponse)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[Form]++-%20returns%200..1>[ExpectedResponse&#124;contentType:string],[ExpectedResponse]^-[AdditionalExpectedResponse],[Form],[AdditionalExpectedResponse])](https://yuml.me/diagram/nofunky;dir:TB/class/[Form]++-%20returns%200..1>[ExpectedResponse&#124;contentType:string],[ExpectedResponse]^-[AdditionalExpectedResponse],[Form],[AdditionalExpectedResponse])

## Children

 * [AdditionalExpectedResponse](AdditionalExpectedResponse.md) - Communication metadata describing the expected response message for additional responses.

## Referenced by Class

 *  **None** *[➞returns](form__returns.md)*  <sub>0..1</sub>  **[ExpectedResponse](ExpectedResponse.md)**

## Attributes


### Own

 * [➞contentType](expectedResponse__contentType.md)  <sub>1..1</sub>
     * Description: TODO Check, was not in hctl ontology, if not could be source of discrepancy
     * Range: [String](types/String.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Mappings:** | | hctl:ExpectedResponse |
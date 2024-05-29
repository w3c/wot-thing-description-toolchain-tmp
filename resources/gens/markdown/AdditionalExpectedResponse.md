
# Class: AdditionalExpectedResponse

Communication metadata describing the expected response message for additional responses.

URI: [td:AdditionalExpectedResponse](https://www.w3.org/2019/wot/td#AdditionalExpectedResponse)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[ExpectedResponse],[Form]++-%20additionalReturns%200..*>[AdditionalExpectedResponse&#124;additionalOutputSchema:string%20%3F;success:boolean%20%3F;schema:string%20%3F;contentType(i):string],[ExpectedResponse]^-[AdditionalExpectedResponse],[Form])](https://yuml.me/diagram/nofunky;dir:TB/class/[ExpectedResponse],[Form]++-%20additionalReturns%200..*>[AdditionalExpectedResponse&#124;additionalOutputSchema:string%20%3F;success:boolean%20%3F;schema:string%20%3F;contentType(i):string],[ExpectedResponse]^-[AdditionalExpectedResponse],[Form])

## Parents

 *  is_a: [ExpectedResponse](ExpectedResponse.md) - Communication metadata describing the expected response message for the primary response.

## Referenced by Class

 *  **None** *[➞additionalReturns](form__additionalReturns.md)*  <sub>0..\*</sub>  **[AdditionalExpectedResponse](AdditionalExpectedResponse.md)**

## Attributes


### Own

 * [➞additionalOutputSchema](additionalExpectedResponse__additionalOutputSchema.md)  <sub>0..1</sub>
     * Description: This optional term can be used to define a data schema for an additional response if it differs from the default output data schema. Rather than a DataSchema object, the name of a previous definition given in a SchemaDefinitions map must be used.
     * Range: [String](types/String.md)
 * [➞success](additionalExpectedResponse__success.md)  <sub>0..1</sub>
     * Description: Signals if the additional response should not be considered an error.
     * Range: [Boolean](types/Boolean.md)
 * [➞schema](additionalExpectedResponse__schema.md)  <sub>0..1</sub>
     * Description: TODO Check, was not in hctl ontology, if not could be source of discrepancy
     * Range: [String](types/String.md)

### Inherited from ExpectedResponse:

 * [➞contentType](expectedResponse__contentType.md)  <sub>1..1</sub>
     * Description: TODO Check, was not in hctl ontology, if not could be source of discrepancy
     * Range: [String](types/String.md)

## Other properties

|  |  |  |
| --- | --- | --- |
| **Mappings:** | | hctl:AdditionalExpectedResponse |
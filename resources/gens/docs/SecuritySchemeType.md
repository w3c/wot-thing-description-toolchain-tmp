# Enum: SecuritySchemeType



URI: [SecuritySchemeType](SecuritySchemeType.md)

## Permissible Values

| Value | Meaning | Description |
| --- | --- | --- |
| nosec | wotsec:NoSecurityScheme | A security configuration corresponding to identified by the Vocabulary Term n... |
| combo | wotsec:ComboSecurityScheme | Elements of this scheme define various ways in which other named schemes defi... |
| basic | wotsec:BasicSecurityScheme | Uses an unencrypted username and password |
| digest | wotsec:DigestSecurityScheme | This scheme is similar to basic authentication but with added features to avo... |
| bearer | wotsec:BearerSecurityScheme | Bearer tokens are used independently of OAuth2 |
| psk | wotsec:PSKSecurityScheme | This is meant to identify that a standard is used for pre-shared keys such as... |
| oauth2 | wotsec:OAuth2SecurityScheme | OAuth 2 |
| apikey | wotsec:APIKeySecurityScheme | This scheme is to be used when the access token is opaque |
| auto | wotsec:AutoSecurityScheme | This scheme indicates that the security parameters are going to be negotiated... |




## Slots

| Name | Description |
| ---  | --- |
| [scheme](scheme.md) |  |






## Identifier and Mapping Information







### Schema Source


* from schema: td




## LinkML Source

<details>
```yaml
name: SecuritySchemeType
from_schema: td
rank: 1000
permissible_values:
  nosec:
    text: nosec
    description: A security configuration corresponding to identified by the Vocabulary
      Term nosec, indicating there is no authentication or other mechanism required
      to access the resource.
    meaning: wotsec:NoSecurityScheme
  combo:
    text: combo
    description: Elements of this scheme define various ways in which other named
      schemes defined in securityDefinitions, including other ComboSecurityScheme
      definitions, are to be combined to create a new scheme definition.
    meaning: wotsec:ComboSecurityScheme
  basic:
    text: basic
    description: Uses an unencrypted username and password.
    meaning: wotsec:BasicSecurityScheme
  digest:
    text: digest
    description: This scheme is similar to basic authentication but with added features
      to avoid man-in-the-middle attacks.
    meaning: wotsec:DigestSecurityScheme
  bearer:
    text: bearer
    description: Bearer tokens are used independently of OAuth2.
    meaning: wotsec:BearerSecurityScheme
  psk:
    text: psk
    description: This is meant to identify that a standard is used for pre-shared
      keys such as TLS-PSK [RFC4279], and that the ciphersuite used for keys will
      be established during protocol negotiation.
    meaning: wotsec:PSKSecurityScheme
  oauth2:
    text: oauth2
    description: OAuth 2.0 authentication security configuration for systems conformant
      with [RFC6749] and [RFC8252].
    meaning: wotsec:OAuth2SecurityScheme
  apikey:
    text: apikey
    description: This scheme is to be used when the access token is opaque.
    meaning: wotsec:APIKeySecurityScheme
  auto:
    text: auto
    description: This scheme indicates that the security parameters are going to be
      negotiated by the underlying protocols at runtime
    meaning: wotsec:AutoSecurityScheme

```
</details>

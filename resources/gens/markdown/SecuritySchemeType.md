
# Enum: SecuritySchemeType



URI: [td:SecuritySchemeType](https://www.w3.org/2019/wot/td#SecuritySchemeType)


## Permissible Values

| Text | Description | Meaning | Other Information |
| :--- | :---: | :---: | ---: |
| nosec | A security configuration corresponding to identified by the Vocabulary Term nosec, indicating there is no authentication or other mechanism required to access the resource. | wotsec:NoSecurityScheme |  |
| combo | Elements of this scheme define various ways in which other named schemes defined in securityDefinitions, including other ComboSecurityScheme definitions, are to be combined to create a new scheme definition. | wotsec:ComboSecurityScheme |  |
| basic | Uses an unencrypted username and password. | wotsec:BasicSecurityScheme |  |
| digest | This scheme is similar to basic authentication but with added features to avoid man-in-the-middle attacks. | wotsec:DigestSecurityScheme |  |
| bearer | Bearer tokens are used independently of OAuth2. | wotsec:BearerSecurityScheme |  |
| psk | This is meant to identify that a standard is used for pre-shared keys such as TLS-PSK [RFC4279], and that the ciphersuite used for keys will be established during protocol negotiation. | wotsec:PSKSecurityScheme |  |
| oauth2 | OAuth 2.0 authentication security configuration for systems conformant with [RFC6749] and [RFC8252]. | wotsec:OAuth2SecurityScheme |  |
| apikey | This scheme is to be used when the access token is opaque. | wotsec:APIKeySecurityScheme |  |
| auto | This scheme indicates that the security parameters are going to be negotiated by the underlying protocols at runtime | wotsec:AutoSecurityScheme |  |


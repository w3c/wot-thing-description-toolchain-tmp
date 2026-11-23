# Differences between the generated and the published JSON Schema

This note compares the generated schema `resources/gens/jsonschema/jsonschema.json` (JSON Schema 2019-09) with the published W3C TD 1.1 validation schema `resources/upstream/schemas/td11-json-schema-validation.json` (draft-07), and lists defects of the published schema.

The status words Undecided and Published defect are defined in the [README](README.md) of this directory.

## Method

The reference is the published schema `resources/upstream/schemas/td11-json-schema-validation.json`; the generated schema is `resources/gens/jsonschema/jsonschema.json`.
Each schema is loaded with the Python `jsonschema` package, using the validator class that its `$schema` names.
Format checking is off unless an entry says otherwise.

Every TD under `tests/data/*/*.jsonld` and every snippet under `resources/snippets/` is validated against both schemas in three ways: as is; with the context URI `https://www.w3.org/ns/wot-next/td` replaced by `https://www.w3.org/2022/wot/td/v1.1`; and with that replacement plus format checking.
Both schemas are walked definition by definition, and each keyword that differs between corresponding locations is exercised by a one-constraint change to a minimal TD.
The raw LinkML output, taken before the tool's post-processing, is compared with the generated schema to locate where a difference arises.

The minimal TD, written B below, is

```json
{"@context": "https://www.w3.org/2022/wot/td/v1.1", "title": "T",
 "securityDefinitions": {"nosec_sc": {"scheme": "nosec"}}, "security": "nosec_sc",
 "properties": {"p": {"type": "string", "forms": [{"href": "http://e.org/p"}]}}}
```

Both schemas accept B.

Part 1 is ordered by verdict: first instances that the published schema accepts and the generated schema rejects, then instances that the generated schema accepts and the published schema rejects, then differences that change no verdict.

## Part 1: Where the generated schema differs

### Media type and content encoding enumerations

Published. `contentMediaType` and `contentEncoding` are strings in a data schema and are unconstrained on a property affordance.

Generated. `contentMediaType` is one of `image/png` and `audio/mpeg`; `contentEncoding` is one of `7bit`, `8bit`, `binary`, `quoted-printable`, `base16`, `base32` and `base64`.

Effect. B with `"contentMediaType": "text/plain"` or `"contentEncoding": "gzip"` on `p` is rejected by the generated schema and accepted by the published one.
The snippet `resources/snippets/form-response.json` with the TD 1.1 context is rejected by the generated schema because of `"contentMediaType": "image/jpeg"`.

Cause. The enumerations are already in the raw LinkML output.

Status. Undecided.

### Bearer `alg` and `format` enumerations

Published. `alg` and `format` of the bearer scheme are strings.

Generated. `alg` is one of `ES256` and `ES512-256`; `format` is one of `jwt`, `jws`, `cwt` and `jwe`.

Effect. B with the scheme `{"scheme": "bearer", "alg": "RS256"}` or `{"scheme": "bearer", "format": "jwk"}` is rejected by the generated schema and accepted by the published one.

Cause. The enumerations are already in the raw LinkML output.

Status. Undecided.

### Required scheme members: OAuth2 `flow` and API key `in`

Published. `flow` of the OAuth2 scheme is optional and accepts any string. `in` of the API key scheme is optional.

Generated. `flow` is required and is one of `code` and `client`. `in` of the API key scheme is required.

Effect. B with the scheme `{"scheme": "oauth2"}`, `{"scheme": "oauth2", "flow": "implicit"}` or `{"scheme": "apikey"}` is rejected by the generated schema and accepted by the published one.

Cause. `required` and the `flow` enumeration are already in the raw LinkML output.

Status. Undecided.

### Icon links and `sizes`

Published. `sizes` has the unanchored pattern `[0-9]*x[0-9]+`. An icon link does not require `sizes`. A link whose `rel` is not `icon` must not carry `sizes`, and a TD link with `rel` `tm:extends` is rejected.

Generated. `sizes` has the anchored pattern `^(\d+x\d+)(\s+\d+x\d+)*$`. An `if`/`then` requires `sizes` when `rel` is `icon`. `sizes` is allowed on any link, and any `rel` is accepted.

Effect. B with the link `{"href": "http://e.org/i", "rel": "icon"}`, or with an icon link carrying `"sizes": "foo 1x1"` or `"sizes": "ab x16x16"`, is rejected by the generated schema and accepted by the published one.
B with the link `{"href": "http://e.org/i", "rel": "next", "sizes": "16x16"}`, `{"href": "http://e.org/i", "sizes": "16x16"}` or `{"href": "http://e.org/i", "rel": "tm:extends"}` is accepted by the generated schema and rejected by the published one.

Cause. The pattern and the `if`/`then` are already in the raw LinkML output.

Status. Undecided.

### Empty `@context` array

Published. The first branch of the context schema is an array with tuple `items` and no `minItems`.

Generated. A context array needs at least one item and must contain one of the known context URIs.

Effect. B with `"@context": []` is rejected by the generated schema and accepted by the published one.
Part 2 shows why the published verdict is a defect.

Status. Undecided.

### Empty form `scopes`

Published. `scopes` of a form is a string or an array of strings.

Generated. `scopes` of a form is a string or an array of strings with at least one item.

Effect. B with `"scopes": []` on its form is rejected by the generated schema and accepted by the published one.
`"scopes": []` on an OAuth2 scheme is accepted by both schemas.

Cause. The `oneOf` with `minItems: 1` on the form `scopes` is already in the raw LinkML output.

Status. Undecided.

### Members without a type in the published schema

Published. `pattern` and `allOf` of a data schema and `model` of `version` have no schema. `properties` of a data schema has `additionalProperties` but no `type`.

Generated. `pattern` and `model` are strings, `allOf` is an array of data schemas, and `properties` is an object.

Effect. B with `"pattern": 5`, `"allOf": 5` or `"properties": 5` on `p`, or with `"version": {"instance": "1", "model": 5}`, is rejected by the generated schema and accepted by the published one.

Status. Undecided.

### URI format on IRI-valued members

Published. Only `id` carries `format: uri`. `base`, `href`, `anchor`, `support`, `profile`, `proxy`, `authorization`, `token` and `refresh` are plain strings.

Generated. All of these carry `format: uri`. Context array items also carry it, inside an `anyOf` with `{}`, where it has no effect.

Effect. This entry depends on format checking.
With format checking, B with `"base": "./x"`, with the form `href` `http://e.org/{x}` or `./p`, or with a relative `support`, `profile`, link `anchor`, `proxy`, `authorization`, `token` or `refresh`, is rejected by the generated schema and accepted by the published one.
Without format checking, both schemas give the same verdict.
With the TD 1.1 context and format checking, TDs and snippets that use URI templates in a form `href` or relative references in a link `href` are rejected by the generated schema only.

Cause. `format: uri` is already in the raw LinkML output.

Status. Undecided.

### `@type`

Published. `@type` is a string or an array of strings, and `tm:ThingModel` is rejected, as a string or as an array item, at the root, in affordances, in security schemes and in extension schemes.

Generated. `@type` is a string or an array with at least one string, and `tm:ThingModel` is accepted.

Effect. B with `"@type": []` at the root, on `p` or on a security scheme is rejected by the generated schema and accepted by the published one.
B with `"@type": "tm:ThingModel"` or `"@type": ["tm:ThingModel"]` is accepted by the generated schema and rejected by the published one.

Cause. `minItems: 1` is already in the raw LinkML output.

Status. Undecided.

### Context URI `wot-next`

Published. A context string must be the TD 1.0 or the TD 1.1 URI, and a context array must contain one of them.

Generated. A context string is one of the TD 1.0, TD 1.1 and `https://www.w3.org/ns/wot-next/td` URIs, and a context array must contain one of these three.

Effect. B with `"@context"` set to `"https://www.w3.org/ns/wot-next/td"`, `["https://www.w3.org/ns/wot-next/td"]` or `[{"a": "b"}, "https://www.w3.org/ns/wot-next/td"]` is accepted by the generated schema and rejected by the published one.
`["https://www.w3.org/2022/wot/td/v1.1", "https://www.w3.org/ns/wot-next/td"]` is accepted by both.
Every TD and snippet that uses only the wot-next URI is rejected by the published schema for this reason.

Cause. The URI is a permissible value of the enumeration `ThingContextUri` in `resources/schemas/thing_description.yaml` and is already in the raw LinkML output.

Status. Undecided.

### Forms and `op`

Published. Root `forms` needs at least one item and every root form needs `op`. `op` in any form is a string or an array with at least one item.

Generated. Root `forms` can be empty, a root form needs only `href`, and `op` can be an empty array in root, property, action and event forms.

Effect. B with `"forms": []`, with `"forms": [{"href": "http://e.org/a"}]`, or with `"op": []` on its property form is accepted by the generated schema and rejected by the published one.

Cause. The raw LinkML output already has root `forms` without `minItems` and a form that requires only `href`. Its `op` array has `minItems: 1`. The pass `build_enum_subset_partitions` in `src/wot_toolchain/artifacts/jsonschema/partitions.py` replaces `op` in each per-affordance form definition with a `oneOf` of constants and an array of the enumeration without `minItems`.

Status. Undecided.

### Empty and repeated collections

Published. `schemaDefinitions` needs at least one entry, `profile` as an array needs at least one item, and a data schema `enum` needs at least one item and unique items.

Generated. All of these can be empty, and `enum` can repeat items.

Effect. B with `"schemaDefinitions": {}` or `"profile": []`, or with `"enum": []` or `"enum": [1, 1]` on `p`, is accepted by the generated schema and rejected by the published one.

Status. Undecided.

### `hreflang`

Published. `hreflang` is a string matching the BCP 47 pattern `bcp47_string`, or an array of such strings.

Generated. `hreflang` is any string or array of strings.

Effect. B with a link carrying `"hreflang": "not a tag!"` or `"hreflang": ["not a tag!"]` is accepted by the generated schema and rejected by the published one.

Cause. The raw LinkML output already has plain strings.

Status. Undecided.

### Expected response `contentType`

Published. `response` requires `contentType`.

Generated. `contentType` is optional.

Effect. B with `"response": {}` on its form is accepted by the generated schema and rejected by the published one.
The snippet `resources/snippets/form-response-empty.json` with the TD 1.1 context is rejected by the published schema for this reason.

Cause. The raw LinkML output already leaves `contentType` optional.

Status. Undecided.

### Combo scheme

Published. A combo scheme needs exactly one of `allOf` and `oneOf`, each an array of at least two strings.

Generated. Each of `allOf` and `oneOf` is an array of at least two strings, but neither member is required and both can appear together.

Effect. B with `{"scheme": "combo"}` or `{"scheme": "combo", "allOf": ["a", "b"], "oneOf": ["a", "b"]}` is accepted by the generated schema and rejected by the published one.

Status. Undecided.

### Auto scheme `name`

Published. The auto scheme must not carry `name`.

Generated. `name` is not forbidden.

Effect. B with the scheme `{"scheme": "auto", "name": "n"}` is accepted by the generated schema and rejected by the published one.

Status. Undecided.

### `in` value `uri` for basic, digest and bearer

Published. `in` of the basic, digest and bearer schemes is one of `header`, `query`, `body`, `cookie` and `auto`.

Generated. `uri` is also accepted.

Effect. B with the scheme `{"scheme": "basic", "in": "uri"}`, or the digest or bearer equivalent, is accepted by the generated schema and rejected by the published one.
`{"scheme": "apikey", "in": "uri"}` is accepted by both.

Cause. All schemes share the enumeration `SecurityLocationType` in `resources/schemas/wot_security.yaml`, which includes `uri`.

Status. Undecided.

### Extension security schemes

Published. A scheme whose `scheme` value matches `.+:.*` still has `@type`, `description`, `descriptions` and `proxy` checked.

Generated. The fallback branch for such a scheme checks only that `scheme` is a string matching `.+:.*`.

Effect. B with the scheme `{"scheme": "ex:foo", "description": 5}`, `{"scheme": "ex:foo", "descriptions": 5}`, `{"scheme": "ex:foo", "proxy": 5}`, `{"scheme": "ex:foo", "@type": 5}` or `{"scheme": "ex:foo", "@type": "tm:ThingModel"}` is accepted by the generated schema and rejected by the published one.

Status. Undecided.

### Structural differences without a verdict change

Published.

- A security scheme is selected through a `oneOf` over per-scheme definitions in one order.
- `multipleOf` is typed `["integer", "number"]`.
- `links` items are a `oneOf` of the published definitions `link_element` and `icon_link_element`.
- `additionalResponses` items are inlined.
- The data schema leaves `additionalProperties` unset.
- The definitions `thing-context-td-uri-temp` and `form` are not referenced; `form` carries a `$comment` saying it is not used for validation.

Generated.

- The `oneOf` over per-scheme definitions uses other names and another order.
- `multipleOf` is typed `number`, and the data schema `type` enumeration lists the same values in another order.
- `links` items reference one `Link` definition.
- `additionalResponses` items reference a definition.
- The data schema sets `additionalProperties: true`, which has the same meaning as leaving it unset.
- The definition `MultiLanguage` is not referenced.

Effect. No TD, snippet or probe changes verdict because of these differences.

Status. Undecided.

## Part 2: Defects in the published schema

### Context arrays

Published. Two branches of the context schema use `prefixItems`, which draft-07 does not define, and rely on `additionalItems`, which draft-07 ignores when `items` is not an array. The first branch has no `minItems`.

Generated. The generated schema rejects `[]` (Part 1) but accepts the three non-empty arrays listed under Effect.

Effect. The ignored keywords leave the third branch requiring only two items, one of them the TD 1.1 URI, and the fourth requiring only that the TD 1.0 URI appear somewhere.
`["https://www.w3.org/2022/wot/td/v1.1", "https://www.w3.org/2019/wot/td/v1"]` is accepted, although the first branch explicitly excludes the TD 1.0 URI after the TD 1.1 URI.
`[5, "https://www.w3.org/2022/wot/td/v1.1"]` and `[{"a": "b"}, 5, "https://www.w3.org/2019/wot/td/v1"]` are accepted.
`[]` is accepted through the first branch.
TD 1.1 section 5.3.1.1 Thing states that `@context` must contain the TD 1.1 URI, that where TD 1.0 consumers are possible the TD 1.0 URI must be the first entry and the TD 1.1 URI the second, and that further array elements are of type anyURI or Map.

Status. Published defect.

### OAuth2 `flow` not required

Published. The OAuth2 scheme does not require `flow`.

Generated. `flow` is required, and B with the scheme `{"scheme": "oauth2"}` is rejected; see "Required scheme members: OAuth2 `flow` and API key `in`" in Part 1.

Effect. B with the scheme `{"scheme": "oauth2"}` is accepted.
TD 1.1 section 5.3.3.10 OAuth2SecurityScheme marks `flow` as mandatory.
The schema of `flow` accepts any string through an `anyOf` with `{"type": "string"}`; this matches the section's wording "string (e.g., code, or client)" and is not a defect.

Status. Published defect.

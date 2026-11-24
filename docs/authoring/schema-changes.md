# Schema changes

Each section starts from the [worked example](../getting-started/first-change.md#worked-example-an-optional-property), which adds an optional `firmware` slot to `VersionInfo` in `resources/schemas/thing_description.yaml`.

## Variations

### Required

Add `required: true`. JSON Schema adds the term to the class's list, `"required": ["instance", "firmware"]`, the table cell reads `mandatory`, and the CSV row ends in `mandatory string`. SHACL gains `sh:minCount 1`.

### Default values

Two keys look related and do different things. `ifabsent: string(1.0.0)` changes only the SHACL shapes, which gain `sh:defaultValue "1.0.0"`, and the merged `linkml/linkml.yaml`. JSON Schema gets no `default`, and the table still says `optional`.

`spec_default: true` under `annotations` changes the table cell to `<a href="#sec-default-values">with default</a>` and the CSV row to `... with default string`. It carries no value. The values themselves are rows in a hand-written table in `resources/index.template.html`, such as `<tr class="rfc2119-default-assertion" id="td-default-observable">`. Add your row there.

Neither key produces a JSON Schema `default` keyword. No schema in the generated `jsonschema.json` has one. The only `default` in the file is the name of a `DataSchema` property.

### Enumeration

Define the values at schema level and use the enum as the range:

```yaml
enums:
  FirmwareChannel:
    description: Release channel of the firmware.
    permissible_values:
      stable:
        description: Released firmware.
      beta:
        description: Pre-release firmware.
```

With `range: FirmwareChannel`, JSON Schema has `"type": "string", "enum": ["stable", "beta"]`, the table type reads `string (e.g., <code>stable</code>, or <code>beta</code>)`, and SHACL has `sh:in ( "stable" "beta" )`. OWL does not change. The term stays an `owl:DatatypeProperty` with range `xsd:string`, and `FirmwareChannel` does not appear in `td.ttl`.

### Multivalued

Add `multivalued: true`. JSON Schema becomes `"items": {"type": "string"}, "type": "array"`, `td-context.jsonld` adds `"@container": "@set"`, the table type reads `Array of string`, and SHACL drops `sh:maxCount 1`.

### Class range and `identifier`

To give firmware structure, make its range a class (see the next section for the class). With `range: Firmware`, JSON Schema has `"$ref": "#/$defs/Firmware"`, the table type links to the class table, and OWL turns `td:firmware` into an `owl:ObjectProperty` with range `td:Firmware`.

Mark `firmwareVersion` with `identifier: true` and several things change at once:

- The `firmware` slot now holds a reference. JSON Schema becomes `{"type": "string"}`, the context gets `"@type": "@id"`, and the SHACL node kind becomes `sh:IRI`.
- `firmwareVersion` disappears from the `properties` and `required` of `$defs.Firmware`.
- The context maps `"firmwareVersion": "@id"`. In JSON-LD, `{"firmwareVersion": "2.1.0"}` then names the node with the IRI `2.1.0`, resolved against the base. No `td:firmwareVersion` triple is produced.

Add `inlined: true` to the slot and the `$ref` comes back. The context keeps `"@type": "@id"` and SHACL keeps `sh:IRI`.

The rules behind these shapes are in [naming conventions §10](../reference/naming-conventions.md#10-inlined-true--embedding-vs-map-vs-array) and [§11](../reference/naming-conventions.md#11-identifier-true--map-keys-in-linkml).

### One of several shapes

`exactly_one_of` lists alternative branches. Here firmware is either one object or an array of them, with `Firmware` carrying an identifier:

```yaml
      firmware:
        slot_uri: td:firmware
        domain: VersionInfo
        range: Firmware
        exactly_one_of:
          - range: Firmware
            inlined: true
          - range: Firmware
            multivalued: true
            inlined_as_list: true
```

In JSON Schema:

```json
"oneOf": [{"$ref": "#/$defs/Firmware"}, {"items": {"$ref": "#/$defs/Firmware"}, "type": "array"}]
```

The table type reads `Firmware or Array of Firmware`. Both forms validate. SHACL keeps `sh:maxCount 1` on `td:firmware`.

The inlining keys go on each branch. Leave them out and the branches fall back to the identifier, `"oneOf": [{"type": "string"}, {"items": {"type": "string"}, "type": "array"}]`. Both `{"firmwareVersion": "2.1.0"}` and `[{"firmwareVersion": "2.1.0"}]` then fail with `is not valid under any of the given schemas`. Use `inlined_as_list: true` on the multivalued branch. With plain `inlined: true` there, the branch becomes an object keyed by identifier, `{"additionalProperties": {"$ref": "#/$defs/Firmware"}, "type": "object"}`, instead of an array.

If the class has no identifier, the schema keeps an extra `"$ref": "#/$defs/Firmware"` next to the `oneOf`, and an array fails with `is not of type 'object'`. Dropping the outer `range` fixes JSON Schema, but OWL then makes the term an `owl:DatatypeProperty` with no range, and SHACL gains `sh:datatype xsd:string`. The one existing use of `exactly_one_of` with a class range is `ArraySchema.items`, whose range `DataSchema` has the identifier `name`.

## A new class

Add the class next to the others in `thing_description.yaml`:

```yaml
  Firmware:
    class_uri: td:Firmware
    description: >-
      Describes the firmware running on the device that the Thing represents.
    annotations:
      spec_description: >-
        Describes the firmware running on the device that the Thing represents.
    attributes:
      firmwareVersion:
        description: Version string of the firmware.
        slot_uri: td:firmwareVersion
        domain: Firmware
        range: string
        required: true
        annotations:
          spec_description: Version string of the firmware (e.g., `2.1.0`).
```

OWL gains `td:Firmware` as an `owl:Class`. The specification gets a `Firmware` section with a table captioned "Vocabulary Terms in Firmware Level", placed in schema order, and the CSV gets `td-vocab-firmwareVersion--Firmware`. JSON Schema adds `$defs.Firmware` with `"required": ["firmwareVersion"]` and `"additionalProperties": true`.

## A new schema file

To keep firmware terms in their own vocabulary, move the class into `resources/schemas/firmware.yaml`:

```yaml
id: https://www.w3.org/2019/wot/firmware
name: firmware
title: Firmware
version: "td-next"
prefixes:
  linkml: https://w3id.org/linkml/
  fw: https://www.w3.org/2019/wot/firmware#
default_prefix: fw
default_range: string
imports:
  - linkml:types
```

Put the class under `classes:`, use `fw:` in its `class_uri` and in each `slot_uri`, and add `- firmware` to the `imports` of `thing_description.yaml`. With only the import, JSON Schema, SHACL, the CSV and `context.jsonld` include the terms, and the class table appears in the core vocabulary section. No ontology declares `fw:Firmware`. `td.ttl` names it only as the range of `td:firmware`.

To get an ontology, a context and a diagram, add a module to `wot-toolchain.yaml`:

```yaml
  - schema: resources/schemas/firmware.yaml
    prefix: fw
    ontology: [fw.ttl]
    context: firmware-context.jsonld
    diagram: fw.svg
```

This writes `owl/fw.ttl` with an ontology header (`dcterms:title "Firmware Ontology"@en`, `owl:versionInfo "td-next"`), `jsonldcontext/firmware-context.jsonld` and `visualization/fw.svg`.

To give the vocabulary its own specification section, add it to `generators.spec.sections`:

```yaml
    - id: sec-firmware-vocabulary-definition
      schema: resources/schemas/firmware.yaml
```

Generation then fails until the template has a matching marker:

```
ERROR: Section id(s) ['sec-firmware-vocabulary-definition'] in spec.sections have no %section()% marker in specification template .../resources/index.template.html
```

Add a `<section id="sec-firmware-vocabulary-definition">` with a heading to `resources/index.template.html`, and put `%section('sec-firmware-vocabulary-definition')%` inside it.

## A snippet

Write the example as a complete TD in `resources/snippets/version-firmware.json`:

```json
{
    "@context": "https://www.w3.org/ns/wot-next/td",
    "id": "urn:uuid:0804d572-cce8-422a-bb7c-4412fcd56f06",
    "title": "MyLampThing",
    "version": { "instance": "1.2.1", "firmware": { "firmwareVersion": "2.1.0", "vendor": "ACME" } },
    "securityDefinitions": { "nosec_sc": { "scheme": "nosec" } },
    "security": "nosec_sc",
    "properties": {}
}
```

Register it under `snippets:` in `_snippets.yaml`:

```yaml
  version-firmware:
    id: version-firmware-sample
    title: Version information with firmware
    hide_paths:
    - '@context'
    - id
    - securityDefinitions
    - security
```

Put `%snippet('version-firmware')%` where the example belongs in the template. It renders as `<aside class="example" id="version-firmware-sample" ...>` with the hidden paths shown as `// ...`.

Generation validates the snippet. A missing `instance` fails the run:

```
ERROR: 1 spec snippet(s) in .../resources/snippets are invalid:
version-firmware.json: version — 'instance' is a required property [schema: properties/version/required]
```

The validator is the static schema under `resources/upstream/schemas/` named in `generators.spec.snippet_validation_schemas`, not the generated `jsonschema.json`. A snippet with `"firmware": 42` passes generation even though the generated schema rejects it. A marker for an unregistered snippet fails with `ERROR: Snippet 'missing-snippet' not found in _snippets.yaml`.

For layouts, groups and path options, see [Snippets](snippets.md).

When the change is written, check it as described in [Checking a change](checking-a-change.md).

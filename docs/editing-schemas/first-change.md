# Your first schema change

This guide is for people who work in the [Thing Description repository](https://github.com/w3c/wot-thing-description) and want to change the td-next vocabulary. You edit LinkML schema files in YAML, and the toolchain generates every published artifact from them. You do not need to know LinkML before you start.

!!! note
    The schemas move to `linkml/` in `w3c/wot-thing-description` when the toolchain is adopted there. These pages already use that layout.

## Set up

Install the toolchain as described in [Getting started](../getting-started.md#install), then run it from the root of your Thing Description checkout:

```bash
wot-toolchain generate-wot-resources
```

It reads `wot-toolchain.yaml` and writes the artifacts into the directory its `output_dir` names. Do not edit the generated files; they are overwritten on every run. Each run prints `WARNING` lines about slots left out of the `hctl`, `wotsec` and `jsonschema` diagrams; they are expected.

## What the toolchain produces

From the schemas, one command writes a JSON Schema for TD instances, JSON-LD contexts, the specification HTML with its vocabulary tables, an assertion CSV, OWL ontologies, SHACL shapes, and class diagrams.

The JSON Schema, the JSON-LD context, and the specification HTML with its assertion inventory are the release targets. The OWL, SHACL and diagram outputs are experimental.

## How the pieces fit

The vocabulary lives in `linkml/*.yaml`. `linkml/thing_description.yaml` is the root schema and imports `hypermedia`, `wot_security` and `jsonschema`.

`wot-toolchain.yaml` at the repository root is the config file. Its `vocabularies` list says which schema gets its own ontology, context and diagram file. Its `generators.spec.sections` list says which schema fills which section of the specification template `index.template.html`.

JSON examples for the specification live in `linkml/snippets/`. Each one is registered in `linkml/snippets/_snippets.yaml` and placed in the template with a `%snippet('name')%` marker.

## Worked example: an optional property

Suppose you want `version` to carry the firmware version of the device. The range of `version` is the class `VersionInfo`, so you add a `firmware` slot to that class. In `linkml/thing_description.yaml`, find `VersionInfo` and add this under its `attributes:`, after `model`:

```yaml
      firmware:
        description: >-
          Provides the version of the firmware running on the device that the Thing represents.
        slot_uri: td:firmware
        domain: VersionInfo
        range: string
        annotations:
          spec_description: >-
            Provides the version of the firmware running on the device that the Thing represents
            (e.g., `2.1.0`).
```

Regenerate. In `jsonschema.json`, `$defs.VersionInfo.properties` gains `firmware` with the `description` and `"type": "string"`. In `jsonldcontext/td-context.jsonld` it becomes `"firmware": {"@id": "firmware"}`.

In `index.html`, the `VersionInfo` table gains a row:

```html
     </td></tr><tr class="rfc2119-table-assertion" id="td-vocab-firmware--VersionInfo">
      <td><code>firmware</code>
      </td><td>Provides the version of the firmware running on the device that the Thing represents (e.g., <code>2.1.0</code>).
      </td><td>optional
      </td><td><a href="https://www.w3.org/TR/2012/REC-xmlschema11-2-20120405/#string"><code>string</code></a>
```

The row id is the assertion id, built as `td-vocab-<term>--<Class>`. `assertions/assertions.csv` gets a row with the same id and the cell texts, ending in `optional string`. In `owl/td.ttl`, `td:firmware` is an `owl:DatatypeProperty` with `rdfs:domain td:VersionInfo` and `rdfs:range xsd:string`.

Each key has a visible effect:

- `description` becomes the JSON Schema `description` and the OWL `skos:definition`.
- `annotations: spec_description` is the text of the specification table cell and the CSV row. Backticks become `<code>` in HTML.
- `slot_uri` puts `td:firmware` into OWL and the module context. Without it, `firmware` is missing from `owl/td.ttl` and `td-context.jsonld`. JSON Schema, the merged `context.jsonld` and SHACL still contain it.
- `domain` produces the `rdfs:domain` line in OWL.
- `range` sets the type in JSON Schema, the table and OWL.

## Next steps

- [Schema changes](schema-changes.md): required terms, defaults, enumerations, class ranges, new classes, new schema files and snippets.
- [OWL ontologies](owl.md): how to write a schema so its OWL ontology comes out right.
- [Checking a change](checking-a-change.md): reading the generation output, comparing it with the previous output, and reviewing the specification.

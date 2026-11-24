# Your first schema change

This guide is for people who know the Thing Description and want to change the td-next vocabulary. You edit LinkML schema files in YAML, and the toolchain generates every published artifact from them. You do not need to know LinkML before you start.

Install the toolchain first; see [Install](install.md).

## What the toolchain produces

From the schemas, one command writes a JSON Schema for TD instances, JSON-LD contexts, the specification HTML with its vocabulary tables, an assertion CSV, OWL ontologies, SHACL shapes, and class diagrams.

The README names the JSON Schema, the JSON-LD context, and the specification HTML with its assertion inventory as the release targets, and calls the OWL, SHACL and visualization outputs experimental.

## How the pieces fit

The vocabulary lives in `resources/schemas/*.yaml`. `thing_description.yaml` is the root schema and imports `hypermedia`, `wot_security` and `jsonschema`.

`wot-toolchain.yaml` at the repository root is the config file. Its `vocabularies` list says which schema gets its own ontology, context and diagram file. Its `generators.spec.sections` list says which schema fills which section of the specification template `resources/index.template.html`.

JSON examples for the specification live in `resources/snippets`. Each one is registered in `resources/snippets/_snippets.yaml` and placed in the template with a `%snippet('name')%` marker.

## Worked example: an optional property

Suppose you want `version` to carry the firmware version of the device. The range of `version` is the class `VersionInfo`, so you add a `firmware` slot to that class. In `thing_description.yaml`, find `VersionInfo` and add this under its `attributes:`, after `model`:

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

- [Schema changes](../authoring/schema-changes.md): required terms, defaults, enumerations, class ranges, new classes, new schema files and snippets.
- [Checking a change](../authoring/checking-a-change.md): reading the generation output, comparing with the snapshots and running the tests.

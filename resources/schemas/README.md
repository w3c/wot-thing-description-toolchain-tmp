# WoT Schemas

The WoT Schemas contains the single, main source of data for all the officially provided WoT resources.

The WoT Schema provides YAML files in [LinkML](https://linkml.io) format as its primary information source, which contain specific classes with their attributes
and respective information like attributes' datatypes or cardinalities.

These YAML files are then used to create the necessary WoT resource files.

## Schema Annotations

The schemas use custom annotations to control how vocabulary terms appear in the generated specification. These are the primary way to shape the final HTML output.

### `spec_description`

Override a slot's base `description` with specification-specific text. Supports `[[RFC3986]]`-style bibliography references.

```yaml
id:
  annotations:
    spec_description: >-
      Identifier of the Thing in form of a URI [[RFC3986]]
      (e.g., stable URI, temporary and mutable URI, URN, etc.).
```

### `spec_default`

Flag a slot as having a default value. Triggers default-value assertion rendering in the vocabulary table.

```yaml
observable:
  annotations:
    spec_default: true
```

### `spec_exclude`

Exclude a slot from the generated specification tables entirely.

```yaml
internal_field:
  annotations:
    spec_exclude: true
```

### `spec_content`

Add rich content blocks (notes, paragraphs, lists, enum tables) after a class's vocabulary table. Each block has a `type` and content fields.

```yaml
Thing:
  annotations:
    spec_content:
      value:
        - type: note
          text: |
            This is an informative note about the Thing class.
        - type: paragraph
          segments:
            - text: |
                General paragraph text.
            - id: td-context-requirement
              text: |
                This segment becomes a testable assertion.
        - type: list
          items:
            - id: td-context-rule-1
              text: First rule about context handling.
            - id: td-context-rule-2
              text: Second rule about context handling.
```

Segment `id` values generate assertion anchors (`rfc2119-assertion` or `rfc2119-table-assertion`) in the HTML output.

### `spec_intro_content`

Same structure as `spec_content`, but rendered *before* the vocabulary table as introductory prose.

### `spec_subsections`

Define subsections that appear after a class's main content, each with its own heading.

```yaml
Form:
  annotations:
    spec_subsections:
      value:
        - id: mapping-op-values
          title: Mapping op Values to Data Schemas
          class: informative
          content:
            - type: markdown
              text: |
                Explanation of how op values map to schemas...
```

### `spec_type_values`

Specify allowed or example values for a slot's type column in the vocabulary table.

```yaml
op:
  annotations:
    spec_type_values:
      value:
        mode: one_of       # or "examples"
        values:
          - readproperty
          - writeproperty
          - invokeaction
```
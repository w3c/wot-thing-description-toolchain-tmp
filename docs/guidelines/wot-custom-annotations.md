# WoT Custom Annotations

**Author:** Mahda Noura (mahda.noura@siemens.com)
**Date:** 29.10.2026

---

## Why Custom Annotations Exist

LinkML is a general-purpose schema language — it generates JSON Schema, OWL, SHACL, and JSON-LD from schema definitions. But the WoT Toolchain has requirements that LinkML generators do not cover natively:

1. **HTML specification rendering.** The generated `index.html` must produce W3C ReSpec vocabulary tables, testable assertions, rich prose blocks, and enum value tables — none of which are part of LinkML's generation targets. The `spec_*` annotation family drives this custom rendering pipeline.

2. **JSON Schema structural patterns.** The W3C TD specification defines JSON Schema patterns (discriminated unions, flat type hierarchies, operation-specific form variants) that the LinkML JSON Schema generator cannot express. The `jsonschema_*` annotation family instructs the postprocessor to transform the raw generator output into the required shapes.

Custom annotations are **workarounds, not features.** Each one exists because native LinkML cannot express a specific WoT requirement. When an upstream fix lands, the corresponding annotation should be retired.

For the catalog of known LinkML limitations, see [Known LinkML Gaps](../known-linkml-gaps.md).

---

## Decision Principle

Before reaching for an annotation:

1. **Can native LinkML express this?** Prefer `exactly_one_of`, `rules`, `minimum_value`, `multivalued`, etc. See [Native LinkML Features for JSON Schema](#native-linkml-features-for-json-schema) below.
2. **Is the gap already documented?** Check [Known LinkML Gaps](../known-linkml-gaps.md) — a workaround may already exist.
3. **Is this a spec rendering concern or a schema concern?** Use `spec_*` for HTML output. Use `jsonschema_*` for JSON Schema output. Never mix them.

---

## Native LinkML Features for JSON Schema

Before reaching for a `jsonschema_*` annotation, verify that native LinkML constructs cannot produce the required output. The following patterns generate correct JSON Schema without custom postprocessing.

**Inheritance and composition:**

- `mixins` — mixin slots are included in the class properties. Example: `PropertyAffordance` inherits `DataSchema` slots.
- `rules` with `preconditions`/`postconditions` — generates `if`/`then` conditional schemas. Example: a `Link` with `rel: "icon"` requires `sizes`.

**Cardinality and value constraints:**

- `exactly_one_of` with two range branches — generates a `oneOf` with single-value and array variants. Example: `@type` accepts a string or an array of strings.
- `minimum_cardinality: 1` on a multivalued branch — generates `minItems: 1` in the array variant.
- `minimum_value: N` — generates `minimum: N`.
- `minimum_value: 0` combined with `none_of: [{equals_number: 0}]` — generates `exclusiveMinimum: 0` after postprocessor simplification. Example: `multipleOf` must be > 0.

**Extensibility and maps:**

- `extra_slots: allowed: true` — generates `additionalProperties: true`. Used on all schema classes to allow extension.
- Multivalued inlined slots with identifier keys — generates the `additionalProperties` map pattern. Example: `securityDefinitions`, `properties`, `actions`, `events`.

**Enumerations:**

- `enum` definitions with `permissible_values` — generates inlined `{"type": "string", "enum": [...]}`. Example: `DataSchemaType`, `contentEncodingList`.

---

## Spec Rendering Annotations (`spec_*`)

These annotations control how classes and slots appear in the generated HTML specification (`index.html`). They have **no effect** on JSON Schema, JSON-LD, SHACL, or OWL output. They are consumed by the ReSpec generator (`src/wotis/generators/respec.py`) and the vocabulary table builder (`src/wotis/specgen/tables.py`).

---

### `spec_description`

**What it does:** overrides a slot's `description` text in the HTML vocabulary table with specification-specific markup. Supports ReSpec bibliography references (`[[RFC3986]]`), backtick code formatting, and `<a>` links that plain-text `description` cannot carry.

**What you need to do:**

- Add `spec_description` only when the spec text needs markup that `description` cannot hold.
- Keep `description` in sync — it must contain the same text minus markup, because OWL and SHACL generators read `description`, not `spec_description`.
- Never put `[[RFC####]]` or backtick markup in `description` — it renders as literal brackets in `rdfs:comment`.

```yaml
id:
  description: >-
    Identifier of the Thing in form of a URI
    (e.g., stable URI, temporary and mutable URI, URN, etc.).
  annotations:
    spec_description: >-
      Identifier of the Thing in form of a URI [[RFC3986]]
      (e.g., stable URI, temporary and mutable URI, URN, etc.).
```

**When NOT to use:** the spec text is identical to `description`. Do not duplicate content.

---

### `spec_default`

**What it does:** marks a slot as having a normative default value in the W3C spec. The vocabulary table renders a "Default value" assertion for this slot.

**What you need to do:**

- Set `spec_default` to the default value (typically `true`, `false`, or a string).
- This is a **spec-level** default for the vocabulary table, not a schema-level default. Do not confuse with LinkML `ifabsent` or `equals_expression` (those are runtime defaults for schema validation).

```yaml
observable:
  annotations:
    spec_default: true
```

---

### `spec_exclude`

**What it does:** hides a slot from the HTML vocabulary table entirely. The slot still exists in all generated schemas (JSON Schema, OWL, SHACL).

**What you need to do:**

- Add `spec_exclude: true` on structural slots that are JSON serialization keys, not W3C vocabulary terms.
- Typical candidates: `identifier: true` slots like `name` and `language_tag` that serve as map keys.

```yaml
name:
  identifier: true
  range: string
  annotations:
    spec_exclude: true
```

**When NOT to use:** to hide a slot you consider unimportant. If the W3C spec defines it as a vocabulary term, it must appear in the table.

---

### `spec_content`

**What it does:** adds structured content blocks **after** a class's vocabulary table in the HTML specification. Supports notes, paragraphs with testable assertions, ordered/unordered lists, enum tables, and raw markdown.

**What you need to do:**

- Add a `value` list where each item has a `type` field determining the content block kind.
- For testable assertions, give segments an `id` field — this becomes an `rfc2119-assertion` anchor in the HTML. **Never change or delete an existing `id`** — external W3C implementations reference them.

Available block types:

| Type | Purpose | Key fields |
|------|---------|------------|
| `note` | Informative note box | `text`, optional `title` |
| `paragraph` | Prose with optional assertion segments | `segments[].id`, `segments[].text` |
| `list` | Ordered/unordered list of assertions | `items[].id`, `items[].text` |
| `enum_table` | Table of enumeration values | `enum`, `columns` |
| `markdown` | Raw markdown (no assertions) | `text` |

#### `markdown`

Plain prose. Processed for cross-references, RFC keywords, and term links, then wrapped in `<p>`. Use when no assertion IDs are needed.

```yaml
- type: markdown
  text: |
    A Thing Description *MUST* include a valid context.
    See [[JSON-LD11]] for details.
```

Renders as: `<p>A Thing Description <em>MUST</em> include a valid context. See [[JSON-LD11]] for details.</p>`

#### `paragraph`

A structured paragraph composed of **segments**. All segments concatenate into a single `<p>`. Any segment with an `id` becomes an assertion `<span>`.

Use `paragraph` instead of `markdown` only when you need to attach an `id` to a specific segment. Both process text identically.

```yaml
- type: paragraph
  segments:
    - text: Introductory sentence.
    - id: td-my-assertion
      text: TD Processors *MUST* do something specific.
    - text: Closing sentence.
```

Renders as: `<p>Introductory sentence. <span class="rfc2119-assertion" id="td-my-assertion">TD Processors <em>MUST</em> do something specific.</span> Closing sentence.</p>`

#### `list`

Unordered list. Each item can optionally carry an assertion ID.

```yaml
- type: list
  items:
    - text: Plain list item.
    - id: td-some-assertion
      text: A Thing Description *MUST* satisfy this requirement.
```

#### `note`

A ReSpec note block. The HTML structure differs based on whether `title` is present:

- **Untitled** → `<div class="note"><p>text</p></div>` — ReSpec needs the block-level `<div>`.
- **Titled** → `<p class="note" title="...">text</p>` — ReSpec reads the `title` attribute directly.

```yaml
# Untitled
- type: note
  text: This is an informative note.

# Titled
- type: note
  title: Important caveat
  text: This note has a title displayed by ReSpec.
```

#### `enum_table`

Renders a LinkML enum as an HTML table. The toolchain reads the enum definition and generates rows automatically.

```yaml
- type: enum_table
  enum: OperationType
  caption: Well-known types
  table_id: table-op-types
  columns:
    - field: name
      header: Operation
    - field: description
      header: Description
```

Column `field` values:

| Field | Source |
|-------|--------|
| `name` | The permissible value key (e.g., `readproperty`) |
| `description` | The `description` field of the permissible value |
| `comment:<prefix>` | Extracts from the value's `comments` list — finds the first comment starting with `<prefix>`, strips the prefix and ` - ` separator, returns the remainder |

**Comment extraction example** — given an enum value with `comments: ["Thing to Consumer - All fields without writeOnly", "Consumer to Thing - No correlation"]`, using `field: "comment:Consumer to Thing"` produces `No correlation`.

#### Text processing

All text fields go through the same pipeline regardless of block type:

- `*MUST*`, `*SHOULD*`, `*MAY*`, etc. → `<em>MUST</em>` (RFC 2119 keywords)
- `[[SPEC-NAME]]` → ReSpec bibliographic reference (see below)
- Known terms (e.g., `Thing Description`, `TD Processors`) → cross-reference links via the glossary (see below)

No HTML needed in text fields — write plain text with these conventions.

#### Bibliographic references (`[[SPEC-NAME]]`)

ReSpec handles these — write `[[RFC3986]]` or `[[wot-architecture11]]` in any text field and ReSpec auto-generates the bibliography entry and link. The spec database is built into ReSpec; no local configuration needed. Use `[[?SPEC-NAME]]` (with `?`) for informative (non-normative) references.

These are **document-level references** to external specifications. They appear in the "References" section at the end of the generated spec.

#### Glossary — cross-reference term linking

The glossary (`resources/xref/glossary.yaml`) handles **term-level cross-referencing** — linking occurrences of vocabulary terms in spec text to their definitions. Any occurrence of a known term in `spec_description`, `spec_content`, or `spec_intro_content` text becomes a clickable `<a>` link.

The toolchain generates a Bikeshed `<pre class=anchors>` block from the glossary, which Bikeshed/ReSpec uses to resolve term references during spec processing.

**Two entry types — internal and external terms:**

```yaml
terms:
  # Internal term — links to an anchor within this spec
  Thing Description:
    id: dfn-td                 # → <a href="#dfn-td">Thing Description</a>
    aliases: ["TDs", "TD"]     # alternative forms that also get linked

  # External term — links to a definition in another W3C spec
  anyURI:
    href: "https://www.w3.org/TR/2012/REC-xmlschema11-2-20120405/#anyURI"
    aliases: []                # → <a href="https://...#anyURI">anyURI</a>
```

| Field | What it links to |
|-------|------------------|
| `id` | An anchor within this spec (`#id`) — for WoT vocabulary terms, class names, and concepts defined in this document |
| `href` | A full URL to an external spec — for datatypes, concepts, or terms defined elsewhere (e.g., XML Schema datatypes, WoT Architecture terms) |

Both support `aliases` — alternative spellings or plural forms that link to the same target. Matching is case-sensitive against canonical name + aliases.

**When to edit the glossary:**

- Adding a new class or concept to the spec that other sections reference by name → add an `id` entry matching the HTML anchor.
- Referencing an external definition (e.g., an XML Schema datatype, a term from WoT Architecture) → add an `href` entry.
- A term appears unlinked in generated HTML → check if it's missing from the glossary or if the casing doesn't match.

#### Full example

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
            - id: td-context-requirement
              text: |
                This segment becomes a testable assertion.
        - type: list
          items:
            - id: td-context-rule-1
              text: First rule about context handling.
```

---

### `spec_intro_content`

**What it does:** same structure as `spec_content`, but rendered **before** the vocabulary table as introductory prose.

**What you need to do:**

- Use the same block type format as `spec_content`.
- Choose placement by asking: is this introductory context or a consequence of the vocabulary? Before the table = `spec_intro_content`, after = `spec_content`.

Currently used on: `SecurityScheme`, `ComboSecurityScheme`, `BearerSecurityScheme`.

---

### `spec_subsections`

**What it does:** creates sub-headings with their own content blocks after a class's main `spec_content`. Each subsection gets its own HTML `<section>` with a heading.

**What you need to do:**

- Add a `value` list where each item defines `id` (becomes the HTML anchor), `title` (the heading text), optional `class` (`informative` or `normative`), and `content` (same block types as `spec_content`).

```yaml
Form:
  annotations:
    spec_subsections:
      value:
        - id: sec-response-usage
          title: Response-related Terms Usage
          class: informative
          content:
            - type: paragraph
              segments:
                - id: td-expectedResponse-default-contentType
                  text: |
                    If not specified, the default content type...
```

Currently used on: `Form` (one subsection for response-related terms).

---

### `spec_type_values`

**What it does:** controls the "Type" column in the vocabulary table for a specific slot. Instead of showing the raw LinkML range, it shows explicit allowed values or illustrative examples.

**What you need to do:**

- Set on a slot (typically via `slot_usage`), not on a class.
- Choose `mode`:
  - `one_of` — exhaustive list. The values **must** be complete.
  - `examples` — illustrative subset. Use when the full list is too long or open-ended.

```yaml
# Exhaustive — all allowed values listed
Form:
  slot_usage:
    op:
      annotations:
        spec_type_values:
          value:
            mode: one_of
            values:
              - readproperty
              - writeproperty
              - invokeaction

# Illustrative — subset of possible values
BearerSecurityScheme:
  slot_usage:
    alg:
      annotations:
        spec_type_values:
          value:
            mode: examples
            values:
              - ES256
              - ES512-256
```

---

## JSON Schema Annotations (`jsonschema_*`)

These annotations control how the JSON Schema postprocessor (`src/wotis/postprocessors/jsonschema_postprocessor.py`) transforms raw LinkML generator output. They have **no effect** on HTML, OWL, or SHACL output.

The postprocessor reads these annotations via `_read_annotations()` and applies transforms in a fixed pipeline order. Adding an annotation to a class automatically activates the corresponding transform — no Python code changes needed.

---

### `jsonschema_flatten_subclasses`

**What it does:** merges all subclass-specific slots into the parent class definition and removes the individual subclass `$defs`. The result is a single flat JSON Schema definition containing every slot from the parent and all its children.

**Why it exists:** the W3C TD spec defines `DataSchema` as one flat type where type-specific properties (`items`, `properties`, `minItems`, etc.) are all merged together. But LinkML's inheritance model generates separate `$defs` for `ArraySchema`, `ObjectSchema`, `NumberSchema`, etc. ([Known LinkML Gaps](../known-linkml-gaps.md))

**What you need to do:**

- Add `jsonschema_flatten_subclasses: true` on the **parent** class.
- All direct subclasses are automatically merged — you do not list them.

```yaml
DataSchema:
  annotations:
    jsonschema_flatten_subclasses: true
```

**Result in generated JSON Schema:**

```json
"DataSchema": {
  "type": "object",
  "additionalProperties": true,
  "properties": {
    "type": { ... },
    "items": { ... },
    "properties": { ... },
    "minimum": { ... }
  }
}
```

Currently used on: `DataSchema`.

---

### `jsonschema_oneof_dispatch`

**What it does:** generates a discriminated `oneOf` union from a class's subclasses. Each subclass becomes a `$ref` variant with a `const` constraint on the discriminator slot. With `include_unknown: true`, a fallback variant without the discriminator constraint is added.

**Why it exists:** the W3C TD spec uses the `scheme` field value (`"basic"`, `"oauth2"`, etc.) to select which `SecurityScheme` subclass applies. LinkML has no native discriminated-union dispatch. ([Known LinkML Gaps, gap #9](../known-linkml-gaps.md#9-no-oneOf-dispatch-on-a-discriminator-slot))

**What you need to do:**

- Add `jsonschema_oneof_dispatch` on the **parent** class with:
  - `discriminator` — the slot name used as the dispatch key.
  - `include_unknown` — whether to add a fallback variant for unknown values.

```yaml
SecurityScheme:
  annotations:
    jsonschema_oneof_dispatch:
      value:
        discriminator: scheme
        include_unknown: true
```

**Result in generated JSON Schema:**

```json
"SecurityScheme": {
  "oneOf": [
    { "$ref": "#/$defs/APIKeySecurityScheme" },
    { "$ref": "#/$defs/BasicSecurityScheme" },
    { "$ref": "#/$defs/OAuth2SecurityScheme" },
    { "$ref": "#/$defs/UnknownSecurityScheme" }
  ]
}
```

Currently used on: `SecurityScheme`.

---

### `jsonschema_form_variants`

**What it does:** splits a single class into operation-specific variant definitions. Each variant is constrained to a subset of values for the `op` slot. Creates separate `$defs` per variant (e.g., `PropertyForm`, `ActionForm`, `EventForm`) and a top-level `oneOf` referencing them.

**Why it exists:** the W3C TD spec defines different allowed `op` values depending on where a `Form` appears (inside a property, action, event, or at root level). LinkML generates a single `Form` definition. ([Known LinkML Gaps, gap #10](../known-linkml-gaps.md#10-no-form-variants-per-affordance-type))

**What you need to do:**

- Add `jsonschema_form_variants` on the class with:
  - `op_slot` — the slot name whose values determine variants.
  - `variants` — a dict mapping variant names to their allowed `op` values.

```yaml
Form:
  annotations:
    jsonschema_form_variants:
      value:
        op_slot: op
        variants:
          property:
            - readproperty
            - writeproperty
            - observeproperty
            - unobserveproperty
          action:
            - invokeaction
            - queryaction
            - cancelaction
          event:
            - subscribeevent
            - unsubscribeevent
```

Currently used on: `Form`.

---

### `jsonschema_exclude`

**What it does:** removes a class entirely from the generated JSON Schema `$defs`. The class still exists in LinkML and appears in OWL, SHACL, and HTML output.

**What you need to do:**

- Add `jsonschema_exclude: true` on the class.
- Use for classes that exist for LinkML structural or inheritance reasons but have no counterpart in the TD JSON Schema.

```yaml
SomeInternalClass:
  annotations:
    jsonschema_exclude: true
```

Currently not actively used in schemas — available for future needs.

---

### `jsonschema_config`

**What it does:** injects raw JSON Schema properties into a slot's generated definition. This is a last-resort escape hatch for when native LinkML features (`inlined: true`, `identifier: true`, `extra_slots`) and other annotations cannot produce the correct output shape.

**Why it exists:** some dict-valued slots (e.g., `actions`, `events`) require a specific `additionalProperties: { $ref: ... }` map pattern that the generator does not emit correctly despite correct `inlined` + `identifier` settings. ([Known LinkML Gaps](../known-linkml-gaps.md))

**What you need to do:**

- Add `jsonschema_config` on the **slot** (typically in `slot_usage`), not on the class.
- Must cite the corresponding entry in [Known LinkML Gaps](../known-linkml-gaps.md). If no entry exists, add one first.
- Include the `tag: jsonschema_config` field (required for the postprocessor to identify the annotation).

```yaml
Thing:
  slot_usage:
    actions:
      annotations:
        jsonschema_config:
          tag: jsonschema_config
          value:
            type: object
            additionalProperties:
              $ref: "#/$defs/ActionAffordance"
```

Currently not actively used in schemas — documented in `AGENTS.md` as a pattern for when native features fail on dict-valued slots.

---

## Quick Reference

| Annotation | Level | Domain | Purpose |
|-----------|-------|--------|---------|
| `spec_description` | slot | HTML | Spec text with markup (`[[RFC]]`, backticks) |
| `spec_default` | slot | HTML | Normative default value for vocab table |
| `spec_exclude` | slot | HTML | Hide structural slot from vocab table |
| `spec_content` | class | HTML | Rich content blocks after vocab table |
| `spec_intro_content` | class | HTML | Rich content blocks before vocab table |
| `spec_subsections` | class | HTML | Sub-headings after class content |
| `spec_type_values` | slot | HTML | Custom "Type" column in vocab table |
| `jsonschema_flatten_subclasses` | class | JSON Schema | Merge subclass slots into parent |
| `jsonschema_oneof_dispatch` | class | JSON Schema | Discriminated union from subclasses |
| `jsonschema_form_variants` | class | JSON Schema | Operation-specific Form variants |
| `jsonschema_exclude` | class | JSON Schema | Remove class from `$defs` |
| `jsonschema_config` | slot | JSON Schema | Raw JSON Schema escape hatch (last resort) |

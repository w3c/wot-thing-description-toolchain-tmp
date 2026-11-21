# WoT Custom Annotations

**Author:** Mahda Noura (mahda.noura@siemens.com)
**Date:** 29.10.2026

---

## Why Custom Annotations Exist

LinkML is a general-purpose schema language — it generates JSON Schema, OWL, SHACL, and JSON-LD from schema definitions. But the WoT Toolchain has requirements that LinkML generators do not cover natively:

1. **HTML specification rendering.** The generated `index.html` must produce W3C ReSpec vocabulary tables, testable assertions, rich prose blocks, and enum value tables — none of which are part of LinkML's generation targets. The `spec_*` annotation family drives this custom rendering pipeline.

2. **JSON Schema structural patterns.** The W3C TD specification defines JSON Schema patterns (discriminated unions, flat type hierarchies, operation-specific form variants) that the LinkML JSON Schema generator cannot express. The `jsonschema_*` annotation family instructs the postprocessor to transform the raw generator output into the required shapes.

3. **JSON-LD context mappings.** The TD JSON-LD context requires language maps, `@index` predicates for keyed maps, and explicit scoped vocabularies that the LinkML context generator does not emit. The `jsonld_*` annotation family instructs the context postprocessor to add them.

Custom annotations are **workarounds, not features.** Each one exists because native LinkML cannot express a specific WoT requirement. When an upstream fix lands, the corresponding annotation should be retired.

For the catalog of known LinkML limitations, see [Known LinkML Gaps](../known-linkml-gaps.md).

---

## Decision Principle

Before reaching for an annotation:

1. **Can native LinkML express this?** Prefer `exactly_one_of`, `rules`, `minimum_value`, `multivalued`, etc. See [Native LinkML Features for JSON Schema](#native-linkml-features-for-json-schema) below.
2. **Is the gap already documented?** Check [Known LinkML Gaps](../known-linkml-gaps.md) — a workaround may already exist.
3. **Which artifact does the concern affect?** Use `spec_*` for HTML output, `jsonschema_*` for JSON Schema output, and `jsonld_*` for the JSON-LD context. Never mix them.

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

## JSON-LD Context Mappings

Use native LinkML `inlined`, `multivalued`, and
`fix_multivalue_containers=True` for JSON-LD list and dictionary containers.
The annotations below declare only mappings that the current LinkML context
generator cannot express.

### Scoped context inference

The context composer derives a scoped vocabulary from the range class and its
ancestors or mixins. A class is a candidate only when its declared `class_uri`
prefix also owns at least one induced slot. The containing slot's `slot_uri`
prefix is excluded. For example, `DataSchema` owns `jsonschema:` slots, and
`PropertyAffordance` explicitly mixes it in; a TD `properties` value therefore
receives the JSON Schema scoped context.

Inference is accepted only when exactly one external vocabulary remains.
Multiple candidates fail generation rather than selecting one arbitrarily.
This avoids scoping generic classes such as `linkml:Any`, which do not own
vocabulary terms.

### `jsonld_context`

**What it does:** controls the scoped vocabulary for a slot's nested context.
Declared on a slot. Two modes:

1. **Explicit prefix** — selects a scoped vocabulary when it cannot be
   inferred from the range (e.g., a slot whose range is `Any`). The prefix
   must be declared under the schema's `prefixes`; otherwise generation fails.
   No current schema uses this mode; the example below is illustrative.
2. **`none`** — suppresses scoped context generation entirely, even when the
   range class would normally trigger one.

```yaml
# Mode 1: explicit prefix override
external_configuration:
  annotations:
    jsonld_context: example

# Mode 2: suppress scoped context
schemaDefinitions:
  annotations:
    jsonld_context: none
```

The context composer resolves a prefix value through the schema prefixes and
builds the nested context from slots mapped to that namespace. The `none`
value short-circuits inference and emits no `@context` for the slot.

**When to use `none`:** when a slot's range class belongs to a vocabulary
(triggering auto-inference) but the slot semantically should not receive a
scoped context. The canonical case is `schemaDefinitions`: its range is
`DataSchema` (jsonschema prefix), but upstream W3C merge.js deliberately
excludes it from scoped context assignment because schema definitions are
opaque definition containers — their content should not be reinterpreted
through a vocabulary-specific lens.

### `jsonld_index`

**What it does:** declares the RDF predicate represented by keys in an
inlined dictionary-valued slot. LinkML generates `@container: "@index"`
natively but does not currently generate this predicate.
([Known LinkML Gaps, gap #3](../known-linkml-gaps.md#3-json-ld-index-predicates-are-not-generated-for-keyed-maps))

Declared on a slot (top-level slot or `slot_usage`). The value is a CURIE.

```yaml
securityDefinitions:
  slot_uri: td:definesSecurityScheme
  annotations:
    jsonld_index: td:hasInstanceConfiguration
```

Effect on the JSON-LD context:

- The term definition's `@index` field receives the local name of the CURIE
  (`td:name` becomes `"name"`).
- When the slot also receives a scoped context, the postprocessor ensures that
  the scoped context contains a term resolving to the expanded CURIE.
- The identifier slot of the range class (the map key) is remapped from `@id`
  to its `slot_uri`, or removed from the context when it has none.
- `jsonld_index` has no effect on a slot that also declares `jsonld_container`.

Currently used on: `properties`, `actions`, `events`, `securityDefinitions`,
`schemaDefinitions`, `uriVariables` (TD module) and the `properties` slot usage
of `ObjectSchema` in the JSON Schema module.

### `jsonld_container`

**What it does:** overrides the `@container` value of a slot's JSON-LD term
definition. LinkML emits only `@index` or `@set` containers and cannot express
language maps.
([Known LinkML Gaps, gap #1](../known-linkml-gaps.md#1-no-container-language-support-in-json-ld-context-generator))

Declared on a slot. The value is a JSON-LD container keyword string.

```yaml
titles:
  slot_uri: td:titleInLanguage
  annotations:
    jsonld_container: "@language"
  inlined: true
  multivalued: true
  range: MultiLanguage
```

The postprocessor writes the value to the term's `@container` and generates
neither an `@index` predicate nor a scoped context for the slot. For the value
`"@language"` it also removes `@index` and `@type` from the term definition.

Currently used on: `titles`, `descriptions`.

The fixed TD JSON-LD members `@context`, `@type`, and `id` are handled by the
context composer rather than custom schema annotations. `id` maps to `@id` and
must remain optional in generated JSON Schema; do not use `identifier: true`.
The security parameter member uses the native `alias: name`; its private map
key has a distinct internal name and is suppressed structurally from generated
public artifacts.

---

## Spec Rendering Annotations (`spec_*`)

These annotations control how classes and slots appear in the generated HTML specification (`index.html`). They have **no effect** on JSON Schema, JSON-LD, SHACL, or OWL output. They are consumed by the ReSpec generator (`src/wot_toolchain/generators/respec.py`) and the vocabulary table builder (`src/wot_toolchain/specgen/tables.py`).

---

### `spec_description`

**What it does:** overrides a slot's `description` text in the HTML vocabulary table with specification-specific markup. On a class, it overrides the class description rendered above the vocabulary table, unless the class declares `spec_intro_content`. For a slot, an annotation in the class's `slot_usage` takes precedence over one in the class's `attributes`, which takes precedence over one on the slot definition. Supports ReSpec bibliography references (`[[RFC3986]]`), backtick code formatting, and `<a>` links that plain-text `description` cannot carry.

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

**What it does:** marks a slot as having a normative default value in the W3C spec. The vocabulary table renders `with default` in the slot's assignment column instead of `mandatory` or `optional`, linked to the default-values section when the spec manifest defines its anchor.

**What you need to do:**

- Set `spec_default: true` on the slot definition, the class's `slot_usage`, or the class's `attributes`. Any boolean `true`, the strings `true`, `yes`, `1`, or `with default`, or any other non-string, non-boolean value counts as set. The value is not rendered.
- This is a **spec-level** default for the vocabulary table, not a schema-level default. Do not confuse with LinkML `ifabsent` or `equals_expression` (those are runtime defaults for schema validation).

```yaml
observable:
  annotations:
    spec_default: true
```

---

### `spec_exclude`

**What it does:** hides a slot from the HTML vocabulary table entirely, or, on a class, skips rendering the class section. The slot or class still exists in all generated schemas (JSON Schema, OWL, SHACL).

**What you need to do:**

- Add `spec_exclude: true` on structural slots that are JSON serialization keys, not W3C vocabulary terms. The annotation is read from the slot definition or the class's `attributes`, not from `slot_usage`.
- Typical candidates: `identifier: true` slots like `name` and `language_tag` that serve as map keys.

```yaml
language_tag:
  identifier: true
  range: string
  required: true
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

**What it does:** same structure as `spec_content`, but rendered **before** the vocabulary table as introductory prose. It replaces the class description: when present, neither `description` nor `spec_description` of the class is rendered.

**What you need to do:**

- Use the same block type format as `spec_content`.
- Choose placement by asking: is this introductory context or a consequence of the vocabulary? Before the table = `spec_intro_content`, after = `spec_content`.

Currently used on: `SecurityScheme`, `ComboSecurityScheme`, `BearerSecurityScheme`.

---

### `spec_subsections`

**What it does:** creates sub-headings with their own content blocks after a class's main `spec_content`. Each subsection gets its own HTML `<section>` with an `<h4>` heading.

**What you need to do:**

- Add a `value` list where each item defines `id` (becomes the HTML anchor), `title` (the heading text), optional `class` (`informative` or `normative`), and `content` (same block types as `spec_content`).

The example below is illustrative.

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

Currently not used in any schema.

---

### `spec_type_values`

**What it does:** controls the "Type" column in the vocabulary table for a specific slot. Instead of showing the raw LinkML range, it shows explicit allowed values or illustrative examples.

**What you need to do:**

- Set on a slot (typically via `slot_usage`), not on a class.
- Choose `mode`:
  - `one_of` — exhaustive list. The values **must** be complete.
  - `examples` — illustrative subset. Use when the full list is too long or open-ended. This is the default when `mode` is omitted.
- The table renders the range followed by `(one of ...)` or `(e.g., ...)`. An annotation in `slot_usage` takes precedence over one in `attributes`, which takes precedence over one on the slot definition.

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

These annotations control how the JSON Schema postprocessor (`src/wot_toolchain/postprocessors/jsonschema_postprocessor.py`) transforms raw LinkML generator output. They have **no effect** on HTML, OWL, or SHACL output.

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

**What it does:** replaces a class's definition with a `oneOf` of `$ref`s to its direct subclasses (`is_a`) that have a definition in `$defs`, sorted by reference. With `include_unknown: true`, a final object variant is appended that requires the discriminator slot and constrains it to a prefixed value (pattern `.+:.*`), so that unknown schemes do not overlap the known ones.

**Why it exists:** the W3C TD specification uses the `scheme` field value (`"basic"`, `"oauth2"`, etc.) to select which `SecurityScheme` subclass applies, and admits additional schemes with a prefixed `scheme` value. LinkML has no native discriminated-union dispatch. ([Known LinkML Gaps, gap #7](../known-linkml-gaps.md#7-no-oneof-dispatch-on-a-discriminator-slot))

**What you need to do:**

- Add `jsonschema_oneof_dispatch` on the **parent** class with:
  - `discriminator` — the slot name used as the dispatch key (required).
  - `include_unknown` — whether to add the fallback variant for prefixed values (default `false`).
- The annotation adds no `const` constraint to the subclass variants.

```yaml
SecurityScheme:
  annotations:
    jsonschema_oneof_dispatch:
      value:
        discriminator: scheme
        include_unknown: true
```

**Result in generated JSON Schema (abridged):**

```json
"SecurityScheme": {
  "oneOf": [
    { "$ref": "#/$defs/APIKeySecurityScheme" },
    { "$ref": "#/$defs/BasicSecurityScheme" },
    { "$ref": "#/$defs/OAuth2SecurityScheme" },
    {
      "type": "object",
      "description": "Additional SecurityScheme not covered by known subclasses",
      "properties": { "scheme": { "type": "string", "pattern": ".+:.*" } },
      "required": ["scheme"]
    }
  ]
}
```

Currently used on: `SecurityScheme`.

---

### `jsonschema_enum_subset_partition`

**What it does:** splits a class definition into one variant per LinkML subset of an enum. The partition reads the `in_subset` membership of each permissible value of the enum; each subset becomes a variant whose enum-typed slot accepts only that subset's values. The postprocessor generates:

- `<Class>_element_base` — the original properties without the partitioned slot, with the original `required` list and `additionalProperties`.
- `<Class>_element_<subset>` — an `allOf` of the base and a constraint on the partitioned slot: one of the subset's values, or an array of them.
- `<Class>` — a `oneOf` of `$ref`s to all subset variants.

**Why it exists:** the W3C TD specification restricts the allowed `op` values of a `Form` by where it appears (Thing level, property, action, event). LinkML generates a single `Form` definition. ([Known LinkML Gaps, gap #8](../known-linkml-gaps.md#8-no-form-variants-per-affordance-type))

**What you need to do:**

- Add `jsonschema_enum_subset_partition` on the class with:
  - `slot` — the name of the enum-typed slot to partition.
  - `enum` — the name of the enum whose permissible values carry `in_subset`.
- Declare the subsets under the schema's `subsets` and assign each permissible value with `in_subset`. Values without `in_subset` belong to no variant.

```yaml
Form:
  class_uri: hctl:Form
  annotations:
    jsonschema_enum_subset_partition:
      value:
        slot: op
        enum: OperationType
```

```yaml
OperationType:
  permissible_values:
    readproperty:
      meaning: td:readProperty
      in_subset:
        - property_ops
```

Currently used on: `Form` (subsets `property_ops`, `action_ops`, `event_ops`, `root_ops`).

---

### `jsonschema_form_subset`

**What it does:** narrows the array `items` of a slot to one subset variant produced by `jsonschema_enum_subset_partition`. The `items` of the slot in the class definition are replaced with a `$ref` to `<PartitionClass>_element_<subset>`. When the class is the schema's `tree_root`, the slot is also narrowed in the top-level `properties`. The slot is left unchanged when it is not an array property, when no partition defines the subset, or when the variant definitions do not exist.

**What you need to do:**

- Add `jsonschema_form_subset` in the class's `slot_usage` for the slot (top-level slot annotations are not read).
- Set the value to the name of a subset used by a `jsonschema_enum_subset_partition` enum.

```yaml
PropertyAffordance:
  slot_usage:
    forms:
      annotations:
        jsonschema_form_subset:
          value: property_ops
```

Currently used on: the `forms` slot usage of `Thing` (`root_ops`), `PropertyAffordance` (`property_ops`), `ActionAffordance` (`action_ops`), and `EventAffordance` (`event_ops`).

---

### `jsonschema_exclude`

**What it does:** removes a class's definition from the generated JSON Schema `$defs`. The class still exists in LinkML and appears in OWL, SHACL, and HTML output.

**What you need to do:**

- Add `jsonschema_exclude: true` on the class.
- Use for classes that exist for LinkML structural or inheritance reasons but have no counterpart in the TD JSON Schema.

```yaml
SomeInternalClass:
  annotations:
    jsonschema_exclude: true
```

Currently not used in any schema; the example above is illustrative.

---

## Quick Reference

| Annotation | Level | Domain | Purpose |
|-----------|-------|--------|---------|
| `jsonld_context` | slot | JSON-LD | Explicit scoped vocabulary prefix, or `none` |
| `jsonld_index` | slot | JSON-LD | `@index` predicate for a keyed map |
| `jsonld_container` | slot | JSON-LD | `@container` override (e.g. `@language`) |
| `spec_description` | class, slot | HTML | Spec text with markup (`[[RFC]]`, backticks) |
| `spec_default` | slot | HTML | `with default` assignment in vocab table |
| `spec_exclude` | class, slot | HTML | Hide class section or structural slot |
| `spec_content` | class | HTML | Rich content blocks after vocab table |
| `spec_intro_content` | class | HTML | Rich content blocks before vocab table |
| `spec_subsections` | class | HTML | Sub-headings after class content |
| `spec_type_values` | slot | HTML | Custom "Type" column in vocab table |
| `jsonschema_flatten_subclasses` | class | JSON Schema | Merge subclass slots into parent |
| `jsonschema_oneof_dispatch` | class | JSON Schema | Discriminated union from subclasses |
| `jsonschema_enum_subset_partition` | class | JSON Schema | One variant per enum subset |
| `jsonschema_form_subset` | slot usage | JSON Schema | Narrow array items to one subset variant |
| `jsonschema_exclude` | class | JSON Schema | Remove class from `$defs` |

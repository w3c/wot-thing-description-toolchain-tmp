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
- `minimum_value: 0` combined with `none_of: [{equals_number: 0}]` — generates `exclusiveMinimum: 0` (the toolchain's JSON Schema generator rewrites the `minimum` + `not` pair). Example: `multipleOf` must be > 0.

**Extensibility and maps:**

- `extra_slots: allowed: true` — generates `additionalProperties: true`. Used on all schema classes to allow extension.
- Multivalued inlined slots with identifier keys — generates the `additionalProperties` map pattern. Example: `securityDefinitions`, `properties`, `actions`, `events`.

**Enumerations:**

- `enum` definitions with `permissible_values` — generates inlined `{"type": "string", "enum": [...]}`. Example: `DataSchemaType`, `contentEncodingList`.

---

## Spec Rendering Annotations (`spec_*`)

These annotations control how classes and slots appear in the generated HTML specification (`index.html`). They have **no effect** on JSON Schema, JSON-LD, SHACL, or OWL output. They are consumed by the ReSpec generator (`src/wot_toolchain/generators/respec.py`) and the vocabulary table builder (`src/wot_toolchain/specgen/tables.py`).

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

### Section prose files (not an annotation)

The prose of a class section is not kept in the schema. It lives in one file per class in the directory named by `generators.spec.prose` in `wot-toolchain.yaml` (`resources/spec/sections/`):

- `<Class>.html` is placed **after** the vocabulary table of the class.
- `<Class>.intro.html` is placed **before** the table, in place of the class description.

A file holds the HTML fragment handed to Bikeshed: plain HTML plus the usual shorthands (`` `code` ``, `[[RFC8259]]`, Markdown links). RFC 2119 keywords are written as bare words (`MUST`); ReSpec marks them up. Assertions are written as `<span class="rfc2119-assertion" id="...">`. **Never change or delete an existing `id`** — external W3C implementations reference them.

The rows of a table that lists an enum come from the schema through an include marker inside `<tbody>`, for example `%enum_rows('OperationType', 'name', 'description')%`. A column is `name`, `description` or `comment:<prefix>` (the text of the enum value comment that starts with `<prefix>:`).

Generation fails (exit 5) for a file whose class has no section in the specification, a file that cannot be read, and an unknown or invalid include marker.

#### Text processing

Text in section prose files follows these conventions:

- RFC 2119 keywords (`MUST`, `SHOULD`, `MAY`, etc.) are written as bare words; ReSpec marks them up. Do not write `*MUST*`: it renders as nested `<em>`.
- `[[SPEC-NAME]]` → ReSpec bibliographic reference (see below)
- Known terms (e.g., `Thing Description`, `TD Processors`) → cross-reference links via the glossary (see below)

#### Bibliographic references (`[[SPEC-NAME]]`)

ReSpec handles these — write `[[RFC3986]]` or `[[wot-architecture11]]` in any text field and ReSpec auto-generates the bibliography entry and link. The spec database is built into ReSpec; no local configuration needed. Use `[[?SPEC-NAME]]` (with `?`) for informative (non-normative) references.

These are **document-level references** to external specifications. They appear in the "References" section at the end of the generated spec.

#### Glossary — cross-reference term linking

The glossary (`resources/xref/glossary.yaml`) handles **term-level cross-referencing** — linking occurrences of vocabulary terms in spec text to their definitions. Any occurrence of a known term in `spec_description` text or in a section prose file becomes a clickable `<a>` link.

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

These annotations control how the toolchain's JSON Schema generator (`src/wot_toolchain/artifacts/jsonschema/generator.py`) changes the output of the upstream LinkML generator. They have **no effect** on HTML, OWL, or SHACL output.

The generator hooks read these annotations while the schema is generated. Adding an annotation to a class automatically activates the corresponding rule — no Python code changes needed.

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

## Quick Reference

| Annotation | Level | Domain | Purpose |
|-----------|-------|--------|---------|
| `spec_description` | slot | HTML | Spec text with markup (`[[RFC]]`, backticks) |
| `spec_default` | slot | HTML | Normative default value for vocab table |
| `spec_exclude` | slot | HTML | Hide structural slot from vocab table |
| `spec_type_values` | slot | HTML | Custom "Type" column in vocab table |
| `jsonschema_flatten_subclasses` | class | JSON Schema | Merge subclass slots into parent |
| `jsonschema_oneof_dispatch` | class | JSON Schema | Discriminated union from subclasses |

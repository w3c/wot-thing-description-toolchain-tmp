# Specification annotations (`spec_*`)

These annotations are listed with the other annotations in [WoT custom annotations](annotations.md).

These annotations control how classes and slots appear in the generated HTML specification (`index.html`). They have **no effect** on JSON Schema, JSON-LD, SHACL, or OWL output. They are consumed by the ReSpec generator (`src/wot_toolchain/generators/respec.py`) and the vocabulary table builder (`src/wot_toolchain/specgen/tables.py`).


## `spec_description`

**What it does:** overrides a slot's `description` text in the HTML vocabulary table with specification-specific markup. On a class, it overrides the class description rendered above the vocabulary table, unless the class declares `spec_intro_content`. For a slot, an annotation in the class's `slot_usage` takes precedence over one in the class's `attributes`, which takes precedence over one on the slot definition. Supports ReSpec bibliography references (`[[RFC3986]]`), backtick code formatting, and `<a>` links that plain-text `description` cannot carry.

**What you need to do:**

- Add `spec_description` only when the spec text needs markup that `description` cannot hold.
- Keep `description` in sync — it must contain the same text minus markup, because OWL and SHACL generators read `description`, not `spec_description`.
- Never put `[[RFC####]]` or backtick markup in `description` — it renders as literal brackets in the OWL `skos:definition`.

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

## `spec_default`

**What it does:** marks a slot as having a normative default value in the W3C spec. The vocabulary table renders `with default` in the slot's assignment column instead of `mandatory` or `optional`, linked to the default-values section when the config file defines its anchor.

**What you need to do:**

- Set `spec_default: true` on the slot definition, the class's `slot_usage`, or the class's `attributes`. Any boolean `true`, the strings `true`, `yes`, `1`, or `with default`, or any other non-string, non-boolean value counts as set. The value is not rendered.
- This is a **spec-level** default for the vocabulary table, not a schema-level default. Do not confuse with LinkML `ifabsent` or `equals_expression` (those are runtime defaults for schema validation).

```yaml
observable:
  annotations:
    spec_default: true
```

---

## `spec_exclude`

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

## `spec_content`

**What it does:** adds structured content blocks **after** a class's vocabulary table in the HTML specification. Supports notes, paragraphs with testable assertions, ordered/unordered lists, enum tables, and raw markdown.

**What you need to do:**

- Add a `value` list where each item has a `type` field determining the content block kind.
- For testable assertions, give segments an `id` field — this becomes an `rfc2119-assertion` anchor in the HTML. **Never change or delete an existing `id`** — external W3C implementations reference them.

Available block types:

| Type | Purpose | Key fields |
|------|---------|------------|
| `note` | Informative note box | `text`, optional `title` |
| `paragraph` | Prose with optional assertion segments | `segments[].id`, `segments[].text` |
| `list` | Unordered list of assertions | `items[].id`, `items[].text` |
| `enum_table` | Table of enumeration values | `enum`, `columns` |
| `markdown` | Raw markdown (no assertions) | `text` |

## `markdown`

Plain prose. Processed for cross-references, RFC keywords, and term links, then wrapped in `<p>`. Use when no assertion IDs are needed.

```yaml
- type: markdown
  text: |
    A Thing Description *MUST* include a valid context.
    See [[JSON-LD11]] for details.
```

Renders as: `<p>A Thing Description <em>MUST</em> include a valid context. See [[JSON-LD11]] for details.</p>`

## `paragraph`

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

## `list`

Unordered list. Each item can optionally carry an assertion ID.

```yaml
- type: list
  items:
    - text: Plain list item.
    - id: td-some-assertion
      text: A Thing Description *MUST* satisfy this requirement.
```

## `note`

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

## `enum_table`

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

## Text processing

All text fields go through the same pipeline regardless of block type:

- `*MUST*`, `*SHOULD*`, `*MAY*`, etc. → `<em>MUST</em>` (RFC 2119 keywords)
- `[[SPEC-NAME]]` → ReSpec bibliographic reference (see below)
- Known terms (e.g., `Thing Description`, `TD Processors`) → cross-reference links via the glossary (see below)

No HTML needed in text fields — write plain text with these conventions.

## Bibliographic references (`[[SPEC-NAME]]`)

ReSpec handles these — write `[[RFC3986]]` or `[[wot-architecture11]]` in any text field and ReSpec auto-generates the bibliography entry and link. The spec database is built into ReSpec; no local configuration needed. Use `[[?SPEC-NAME]]` (with `?`) for informative (non-normative) references.

These are **document-level references** to external specifications. They appear in the "References" section at the end of the generated spec.

## Glossary — cross-reference term linking

The glossary (the file that `generators.spec.glossary` in `wot-toolchain.yaml` names) handles **term-level cross-referencing** — linking occurrences of vocabulary terms in spec text to their definitions. Any occurrence of a known term in `spec_description`, `spec_content`, or `spec_intro_content` text becomes a clickable `<a>` link.

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

## Full example

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

## `spec_intro_content`

**What it does:** same structure as `spec_content`, but rendered **before** the vocabulary table as introductory prose. It replaces the class description: when present, neither `description` nor `spec_description` of the class is rendered.

**What you need to do:**

- Use the same block type format as `spec_content`.
- Choose placement by asking: is this introductory context or a consequence of the vocabulary? Before the table = `spec_intro_content`, after = `spec_content`.

Currently used on: `SecurityScheme`, `ComboSecurityScheme`, `BearerSecurityScheme`.

---

## `spec_subsections`

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

## `spec_type_values`

**What it does:** controls the "Type" column in the vocabulary table for a specific slot. Instead of showing the raw LinkML range, it shows explicit allowed values or illustrative examples.

**What you need to do:**

- Set on a slot (typically via `slot_usage`), not on a class.
- Choose `mode`:
  - `one_of` — exhaustive list. The values **must** be complete.
  - `examples` — illustrative subset. Use when the full list is too long or open-ended. This is the default when `mode` is omitted.
- The table renders the range followed by `(one of ...)` or `(e.g., ...)`. An annotation in `attributes` takes precedence over one in `slot_usage`, which takes precedence over one on the slot definition.

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

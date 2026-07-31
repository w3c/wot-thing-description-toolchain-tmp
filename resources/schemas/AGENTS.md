# Schema Authoring Rules

This directory contains the LinkML schemas that are the **single source of truth** for all generated WoT artifacts. Every class, slot, and annotation here drives HTML, JSON Schema, JSON-LD context, SHACL, OWL, Mermaid Diagrams, and assertion CSV output simultaneously. A change in the wrong place breaks all artifacts at once.

Read this file and `README.md` before touching any `.yaml` file.

---

## File Responsibility

| File | Vocabulary | W3C spec namespace |
|---|---|---|
| `thing_description.yaml` | Thing, affordances (Property/Action/Event), VersionInfo, MultiLanguage | `td:` |
| `hypermedia.yaml` | Form, Link, OperationType, ExpectedResponse | `hctl:` |
| `wot_security.yaml` | SecurityScheme and all scheme subclasses | `wotsec:` |
| `jsonschema.yaml` | DataSchema, ArraySchema, ObjectSchema, etc. | `jsonschema:` |

`thing_description.yaml` imports the others. Do not create cross-imports in the other direction.

---

## Class and Slot Order Is Normative

**The order of classes in each YAML file directly controls the order of vocabulary tables in the generated HTML spec.** The current order is synchronized with the W3C WoT Thing Description specification. Do not reorder classes or slots without an explicit decision to change the spec table order.

Rule: new classes go at the end of the relevant file unless spec ordering requires otherwise. Document the reason if inserting mid-file.

Similarly, the order of slots within a class controls the order of rows in that class's vocabulary table. Slot order must match the spec.

---

## Semantic Annotations (OWL / RDF)

Every class and slot that corresponds to a WoT ontology concept **must** carry a URI annotation. These drive OWL ontology and SHACL shape generation.

### `class_uri`

Binds a LinkML class to its OWL class IRI. Required on every class that has a corresponding WoT ontology class.

```yaml
Thing:
  class_uri: td:Thing
  ...

InteractionAffordance:
  class_uri: td:InteractionAffordance
  ...
```

Without `class_uri`, the class generates a blank-node OWL class — wrong for any published ontology term.

### `slot_uri`

Binds a slot to its OWL object/datatype property IRI. Required on every slot that maps to a published WoT ontology property.

```yaml
properties:
  slot_uri: td:hasPropertyAffordance
  ...

title:
  slot_uri: td:title
  ...
```

Slots without `slot_uri` generate a local property not linked to the WoT ontology — only acceptable for internal/structural slots.

### `see_also`

Link a slot or class to the relevant W3C spec section URL or related ontology term. Not required, but strongly encouraged.

```yaml
supportContact:
  slot_uri: td:supportContact
  see_also: schema:contactPoint
```

---

## `tree_root`

Exactly one class per schema must carry `tree_root: true`. This marks the root of the JSON document — the JSON Schema validator uses it as the entry point, and the HTML spec renders it first.

In `thing_description.yaml`: `Thing` is `tree_root: true`. Do not add `tree_root` to any other class in any file. Do not remove it from `Thing`.

```yaml
Thing:
  class_uri: td:Thing
  tree_root: true
```

---

## Slot Definitions: Top-Level vs. Class-Level

LinkML has two places to define a slot:

1. **Top-level `slots:` section** — shared slots reused across multiple classes. Changes here affect every class that uses the slot.
2. **`attributes:` block inside a class** — slot local to that class only. Preferred when the slot is specific to one class.

Rule: if a slot appears in only one class, define it in `attributes:`. If it is shared (e.g., `title`, `description`, `forms`), define it at top level and reference from classes.

---

## `slot_usage` — Per-Class Overrides of Shared Slots

`slot_usage:` inside a class block overrides properties of a top-level slot **only for that class**. It does not redefine the slot globally. This is the primary mechanism for making a shared slot behave differently in different classes — changing cardinality, narrowing the range, tightening the pattern, or overriding the description/annotation.

### When to use `slot_usage`

- **Make a shared optional slot required in one class only.**
  `title` is optional on `InteractionAffordance` but REQUIRED on `Thing`:
  ```yaml
  Thing:
    slot_usage:
      title:
        required: true
  ```

- **Narrow the range for a specific class.**
  `items` is a generic slot but ArraySchema needs it to range over `DataSchema` specifically:
  ```yaml
  ArraySchema:
    slot_usage:
      items:
        slot_uri: jsonschema:items
        description: Used to define the characteristics of an array
        range: DataSchema
        exactly_one_of:
          - range: DataSchema
          - range: DataSchema
            multivalued: true
  ```

- **Tighten a pattern for a subclass.**
  Security scheme subclasses each lock the `scheme` slot to their own fixed value:
  ```yaml
  NoSecurityScheme:
    slot_usage:
      scheme:
        pattern: ^nosec$

  AutoSecurityScheme:
    slot_usage:
      scheme:
        pattern: ^auto$
  ```

- **Override `spec_description` or annotations for one class without changing the global slot.**
  `forms` is required in `InteractionAffordance` but has a different spec description than at top level:
  ```yaml
  InteractionAffordance:
    slot_usage:
      forms:
        annotations:
          spec_description: >-
            Set of form hypermedia controls that describe how an operation can be performed.
            Forms are serializations of Protocol Bindings. The array cannot be empty.
        required: true
  ```

- **Assign a `slot_uri` to a shared slot for a specific class context.**
  The top-level `properties` slot gets a WoT-specific URI only in the `Thing` context:
  ```yaml
  Thing:
    slot_usage:
      properties:
        slot_uri: td:hasPropertyAffordance
        range: PropertyAffordance
  ```

### What `slot_usage` cannot do

- Cannot add a slot to a class that did not declare the slot in `slots:` — use `attributes:` for that.
- Cannot change `multivalued` from `false` to `true` in all generators reliably — test artifact output after such a change.
- Cannot introduce a completely new `slot_uri` that conflicts with the top-level slot's OWL property — this creates a mapping ambiguity in the OWL generator.

### Rules

- Every `slot_usage` override must have a comment (YAML `#`) explaining the reason — either the W3C spec requirement that forces the override or the structural constraint being applied.
- If the override changes `required`, verify the HTML vocabulary table shows the correct REQUIRED/OPTIONAL status after regeneration.
- If the override changes `range`, run `/verify` — both JSON Schema `$defs` and the JSON-LD context must reflect the narrowed range correctly.
- Do not duplicate the top-level slot's `description` verbatim in `slot_usage` — only include what actually differs.

---

## `inlined: true` — Embedding vs. Map vs. Array

`inlined: true` on a slot means instances of the range class are **embedded** in the JSON output rather than referenced by IRI. Combined with `multivalued: true`, the actual JSON shape depends on whether the range class has an `identifier: true` slot.

### Three serialization patterns

| `inlined` | `multivalued` | Range class has `identifier: true` | JSON output |
|---|---|---|---|
| `true` | `true` | Yes | **Dict/map** — identifier value is the JSON key, object is the value |
| `true` | `true` | No | **Array** of embedded objects |
| `false` / absent | `true` | — | **Array** of URIs or scalar references |

### Pattern 1 — Dict/map (inlined + identifier)

`properties`, `actions`, `events` in `Thing` are all dict-valued in TD JSON. The affordance name (e.g., `"temperature"`) becomes the JSON key:

```json
"properties": {
  "temperature": { "type": "number", "readOnly": true }
}
```

This works because:
1. The slot has `inlined: true` and `multivalued: true`.
2. The range class (`PropertyAffordance`, `ActionAffordance`, `EventAffordance`) inherits from `InteractionAffordance`, which has a `name` slot with `identifier: true`.

```yaml
# In InteractionAffordance (thing_description.yaml)
attributes:
  name:
    identifier: true
    spec_exclude: true   # structural slot — hidden from vocabulary tables
    range: string
```

The `identifier: true` slot becomes the map key and is **not** emitted as a field inside the object — it is consumed as the key. Mark it `spec_exclude: true` so it does not appear in HTML vocabulary tables (it is structural, not semantic).

### Pattern 2 — Array of embedded objects (inlined, no identifier)

`forms` has `multivalued: true` and `inlined: true` but `Form` has no `identifier: true` slot. Result: plain array of embedded Form objects.

```json
"forms": [
  { "href": "https://...", "op": "readproperty" }
]
```

### Pattern 3 — Array without inlining

Slots without `inlined: true` emit references or scalar values. For class-range slots, this means `$ref` links in JSON Schema, not embedded objects.

### `identifier: true` rules

- Only one slot per class may carry `identifier: true`.
- Always pair with `spec_exclude: true` — the identifier slot is a structural key, not a vocabulary term.
- Do not add `slot_uri` or `spec_description` to an identifier slot.
- Changing or removing an identifier slot changes the JSON serialization shape — runs through full artifact generation and all golden files must be updated.

Real examples in the schema:

| Class | Identifier slot | Used in |
|---|---|---|
| `InteractionAffordance` | `name` | `properties`, `actions`, `events`, `uriVariables` slots |
| `MultiLanguage` | `language_tag` | `titles`, `descriptions` slots on affordances |

### `jsonschema_config` annotation — postprocessor workaround

For some dict-valued slots (e.g., `actions`, `events` in `Thing.slot_usage`), the LinkML JSON Schema generator does not emit the correct `additionalProperties: $ref` map shape even when `inlined: true` + `identifier: true` are set. The `jsonschema_config` annotation is the postprocessor hook to force the correct output:

```yaml
Thing:
  slot_usage:
    actions:
      range: ActionAffordance
      multivalued: true
      inlined: true
      annotations:
        jsonschema_config:
          tag: jsonschema_config
          value:
            type: object
            additionalProperties:
              $ref: "#/$defs/ActionAffordance"
```

This annotation is a **last resort** — check `KNOWN_LINKML_GAPS.md` before adding one. If the map shape generates correctly without it, do not add it.

---

## Required Annotations on Every Class and Slot

| Field | Required | Notes |
|---|---|---|
| `description` | Yes | Plain text, no markup. Must match the W3C spec's normative definition. |
| `spec_description` | When different from `description` | Use `[[RFC####]]` syntax for bibliography refs; backticks for inline code. |
| `class_uri` / `slot_uri` | Yes, for published WoT terms | See Semantic Annotations above. |
| `range` | Yes on every slot | Omitting range inherits `default_range: string` — make it explicit. |
| `required` (in class) | When normative | A REQUIRED slot in the spec must be listed in the class `required:` list. |

When `spec_description` is added or changed, update the base `description` to match (minus markup). They must stay in sync — `description` is used by generators that do not read annotations.

---

## Inheritance (`is_a`) and Mixins

- `is_a` = single-inheritance parent class. The child inherits all parent slots.
- `mixins` = structural composition without inheritance semantics. Use sparingly — LinkML does not emit mixin semantics in all generators.

Current hierarchy:
```
InteractionAffordance
  ├── PropertyAffordance
  ├── ActionAffordance
  └── EventAffordance
```

Do not introduce new base classes without a corresponding WoT ontology class to bind them to.

---

## Adding a New Class

Checklist:
1. Place the class at the correct position in the file (spec table order).
2. Add `class_uri` pointing to the WoT ontology IRI (or the correct namespace if a new term).
3. Add `description` (plain text, spec-accurate).
4. Add `spec_description` if the HTML version needs markup or RFC refs.
5. Add all slots with explicit `range`, `required` list, and `slot_uri` where applicable.
6. If the class appears as a range on another slot, verify the other slot has `inlined: true` if instances are embedded (not referenced by URI).
7. Run `/verify` — all artifacts must regenerate cleanly.

---

## Adding a New Slot

Checklist:
1. Decide: top-level or class-level attribute (see Slot Definitions above).
2. Set `slot_uri` if this maps to a WoT ontology property.
3. Set `range` explicitly (never rely on `default_range` implicitly).
4. Set `multivalued: true` if the slot can hold more than one value.
5. Set `inlined: true` if the range is a class and instances are embedded (not referenced by IRI).
6. Add to the class `required:` list if normative.
7. Write both `description` and `spec_description` (if different).
8. Run `/verify` — JSON Schema, context, and HTML must all be correct.

---

## Spec Content Annotations (`spec_content`, `spec_intro_content`, `spec_subsections`)

See `README.md` for syntax. Key constraints:

- Segment `id` values inside `spec_content` / `spec_intro_content` become normative assertion anchors in the HTML (`td-{kebab-case}`). **Never change or delete an existing `id`** — assertion anchors are normative identifiers used by external implementations.
- New segment IDs must be globally unique across all schema files.
- `spec_type_values` with `mode: one_of` must be exhaustive — it drives both the HTML table and the JSON Schema enum.

---

## What NOT to Do

- **Do not edit `resources/gens/` directly.** Generated on every run.
- **Do not reorder classes or slots** without explicit justification and spec alignment.
- **Do not add `tree_root: true`** to any class other than `Thing`.
- **Do not omit `class_uri` / `slot_uri`** on any term that has a published WoT ontology counterpart.
- **Do not use bare URLs** in `spec_description` — use `[[RFC####]]` or `<a>` Respec syntax.
- **Do not rename a slot** that is already referenced in generated artifacts (JSON Schema `$defs`, assertion anchors) without updating all cross-references and running `/verify`.
- **Do not mix vocabulary between files** — `td:` terms only in `thing_description.yaml`, `hctl:` only in `hypermedia.yaml`, etc.

---

## After Any Schema Change

Run `/verify` (calls `uv sync` → regenerate → snippet validation → tests). Do not open a PR without a clean `/verify` run.

Check `KNOWN_LINKML_GAPS.md` if any generated artifact looks wrong before writing a postprocessor — the gap may already be documented.

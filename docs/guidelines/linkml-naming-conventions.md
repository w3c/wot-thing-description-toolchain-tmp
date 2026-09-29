# LinkML Naming Conventions

**Author:** Mahda Noura (mahda.noura@siemens.com)
**Date:** 29.10.2026

---

Naming and structural conventions for the WoT LinkML schemas under `resources/schemas/`.

For the complete annotation API, see [WoT Custom Annotations](wot-custom-annotations.md). For postprocessor conventions, see [Postprocessor Conventions](postprocessor-conventions.md).

---

## 1. Class Naming

**Rule: use PascalCase matching the W3C ontology term exactly.**

Rationale: class names drive JSON Schema `$defs` keys, OWL class IRIs, and HTML vocabulary table headings. A mismatch creates inconsistency across all generated artifacts.

```yaml
Thing:              # correct — matches td:Thing
InteractionAffordance:  # correct — matches td:InteractionAffordance
```

**Rule: every class that has a published WoT ontology counterpart must carry `class_uri`.**

Rationale: without `class_uri`, OWL and SHACL generators produce blank-node classes not linked to the WoT ontology.

```yaml
Thing:
  class_uri: td:Thing
  tree_root: true
  description: >-
    An abstraction of a physical or a virtual entity whose metadata
    and interfaces are described by a WoT Thing Description.
```

**Rule: only `Thing` carries `tree_root: true`.**

Rationale: `tree_root` determines the JSON Schema entry point and the first HTML vocabulary table. Multiple tree roots cause ambiguous validator behavior.

---

## 2. Slot Naming

**Rule: use camelCase for slot names, matching the TD JSON property name directly.**

Rationale: slot names in this project use camelCase (e.g., `securityDefinitions`, `schemaDefinitions`, `uriVariables`) to match the W3C TD representation. This differs from the general LinkML convention of snake_case but is aligned with TD 1.1. terms.

```yaml
slots:
  securityDefinitions:
    slot_uri: td:definesSecurityScheme
    description: >-
      Set of named security scheme definitions.
    range: SecurityScheme
```

**Rule: every slot that maps to a published WoT ontology property must carry `slot_uri`.**

Rationale: without `slot_uri`, the slot generates a local property not linked to the WoT ontology — only acceptable for internal/structural slots like `name` (identifier keys).

**Rule: always set `range` explicitly.**

Rationale: omitting `range` silently inherits `default_range: string`. An implicit range is a latent bug — when someone changes `default_range`, every rangeless slot changes with it.

```yaml
# Wrong — relies on default_range
observable:
  slot_uri: td:isObservable

# Correct — explicit range
observable:
  slot_uri: td:isObservable
  range: boolean
```

---

## 3. Enum Naming

**Rule: PascalCase for enum type names.**

Rationale: enums occupy the same namespace as classes in JSON Schema `$defs`. Consistent casing avoids collisions and confusion.

```yaml
enums:
  OperationType:
    description: Well-known operation types for WoT interactions.
    permissible_values:
      readproperty:
        description: Identifies the read operation on Property Affordances.
      writeproperty:
        description: Identifies the write operation on Property Affordances.
```

**Rule: permissible value keys use the exact string from the W3C spec.**

Rationale: these keys become `"enum"` values in JSON Schema. Renaming them breaks TD instance validation. Use the spec-defined casing (typically lowercase).

**Rule: every permissible value should have a `description`.**

Rationale: descriptions drive generated HTML enum tables. Missing descriptions produce empty table cells in the spec.

---

## 4. Prefix and Namespace Rules

**Rule: each schema file owns one W3C namespace prefix.**

| File | Owns prefix |
|------|------------|
| `thing_description.yaml` | `td:` |
| `hypermedia.yaml` | `hctl:` |
| `wot_security.yaml` | `wotsec:` |
| `jsonschema.yaml` | `jsonschema:` |

Rationale: namespace ownership prevents vocabulary bleeding across files. A `td:` term in `hypermedia.yaml` creates confusing provenance in the generated ontology.

**Rule: `thing_description.yaml` imports the other three. No reverse imports.**

Rationale: a single import direction keeps the dependency graph acyclic and prevents circular generation.

```yaml
# thing_description.yaml
imports:
  - linkml:types
  - hypermedia
  - wot_security
  - jsonschema
```

**Rule: terms must not cross namespace boundaries.**

A slot with `slot_uri: td:hasPropertyAffordance` belongs in `thing_description.yaml`, not in `hypermedia.yaml`. If a slot needs to reference a term from another namespace, define it in the owning file and use `slot_usage` in the consuming class.

---

## 5. File Organization

**Rule: class and slot order is normative — it controls the generated HTML spec table order.**

Rationale: the order of classes in each YAML file directly maps to the order of vocabulary tables in the generated specification (index.html). Reordering classes reorders the spec.

- New classes go at the end unless spec ordering requires insertion mid-file.
- Slot order within a class controls row order in that class's vocabulary table.
- Document the reason if inserting mid-file.

**Rule: structural slots (identifier keys) carry `spec_exclude: true`.**

Rationale: identifier slots like `name` and `language_tag` are JSON serialization keys, not vocabulary terms. They must not appear in HTML vocabulary tables.

```yaml
attributes:
  name:
    identifier: true
    range: string
    annotations:
      spec_exclude: true
```

---

## 6. `slot_usage` Conventions

**Rule: every `slot_usage` override must have a YAML comment explaining the reason.**

Rationale: without a comment, future maintainers cannot distinguish an intentional override from a copy-paste artifact.

```yaml
Thing:
  slot_usage:
    # W3C spec requires title on Thing (optional on other affordances)
    title:
      required: true
```

**Rule: do not duplicate the top-level slot's `description` verbatim in `slot_usage`.**

Rationale: duplicated descriptions drift out of sync. Only include what actually differs from the top-level definition.

**Rule: after changing `required` or `range` in `slot_usage`, verify generated artifacts.**

Regenerate and check: (1) JSON Schema reflects the correct `required` array, (2) HTML vocabulary table shows correct REQUIRED/OPTIONAL status, and (3) JSON-LD context reflects any narrowed range.

---

## 7. `description` and `spec_description` Sync

**Rule: when `spec_description` is present, `description` must contain the same text minus markup.**

Rationale: `description` is used by generators that do not read annotations (OWL, SHACL). If they diverge, the ontology says one thing and the HTML spec says another.

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

**Rule: `[[RFC####]]` and backtick markup belong only in `spec_description`, never in `description`.**

Rationale: `description` is plain text. Markup in `description` renders as literal brackets in OWL `rdfs:comment` values.

---

## 8. `see_also` — Linking to Related Terms

**Rule: use `see_also` to link a slot or class to its W3C spec section URL or a related ontology term.**

Rationale: `see_also` provides discoverability without affecting generated output. Maintainers can trace schema terms back to the spec.

```yaml
supportContact:
  slot_uri: td:supportContact
  see_also: schema:contactPoint
```

---

## 9. Slot Definitions: Top-Level vs. Class-Level

**Rule: if a slot appears in only one class, define it in `attributes:`. If shared, define at top level.**

Rationale: top-level slots are global — changes affect every class that uses them. Class-level `attributes:` slots are scoped to one class, reducing accidental side effects.

| Location | When to use |
|----------|------------|
| Top-level `slots:` | Shared across multiple classes (e.g., `title`, `description`, `forms`) |
| `attributes:` inside a class | Specific to one class only |

---

## 10. `inlined: true` — Embedding vs. Map vs. Array

`inlined: true` on a slot means instances of the range class are **embedded** in the JSON output rather than referenced by IRI. Combined with `multivalued: true`, the actual JSON shape depends on whether the range class has an `identifier: true` slot.

### Three serialization patterns

| `inlined` | `multivalued` | Range has `identifier: true` | JSON output |
|-----------|---------------|------------------------------|-------------|
| `true` | `true` | Yes | **Dict/map** — identifier value is the JSON key |
| `true` | `true` | No | **Array** of embedded objects |
| `false` / absent | `true` | — | **Array** of URIs or scalar references |

**Pattern 1 — Dict/map (inlined + identifier):**

`properties`, `actions`, `events` in `Thing` are all dict-valued in TD JSON. The affordance name becomes the JSON key. Generated JSON Schema output for `properties`:

```json
{
  "additionalProperties": {
    "$ref": "#/$defs/PropertyAffordance"
  },
  "description": "All Property-based Interaction Affordances of the Thing.",
  "type": "object"
}
```

This works because the slot has `inlined: true` and `multivalued: true`, and the range class has a `name` slot with `identifier: true`.

**Pattern 2 — Array of embedded objects (inlined, no identifier):**

`forms` has `multivalued: true` and `inlined: true` but `Form` has no `identifier: true` slot. Result: plain array. Generated JSON Schema output:

```json
{
  "description": "Set of form hypermedia controls that describe how an operation can be performed. ...",
  "items": {
    "$ref": "#/$defs/Form"
  },
  "type": "array"
}
```

**Pattern 3 — Array without inlining:**

Slots without `inlined: true` emit references or scalar values. Generated JSON Schema output for `security`:

```json
{
  "description": "Set of security definition names, chosen from those defined in securityDefinitions. ...",
  "oneOf": [
    {
      "type": "string"
    },
    {
      "items": {
        "type": "string"
      },
      "minItems": 1,
      "type": "array"
    }
  ]
}
```

---

## 11. `identifier: true` — Map Keys in LinkML

`identifier: true` on a slot tells LinkML that the slot's value is the **key** in a JSON map (dict), not a regular property of the object. When a parent slot has `inlined: true` + `multivalued: true` and the range class has an `identifier: true` slot, LinkML generates an `additionalProperties` map instead of an array (see Pattern 1 in section 10).

The identifier slot is **consumed** as the map key — it does not appear as a property inside the object. For example, `InteractionAffordance.name` with `identifier: true` means affordance names become JSON keys (`"temperature": {...}`) rather than a `"name"` field inside each object.

**Rule: only one slot per class may carry `identifier: true`.**

LinkML uses exactly one slot as the map key. Multiple identifier slots on the same class is an error.

**Rule: always pair `identifier: true` with `spec_exclude: true`.**

Since the identifier slot is a structural artifact of JSON serialization (the map key), it is not a vocabulary term defined in the W3C spec. Adding `spec_exclude: true` hides it from the generated HTML vocabulary tables, where it would be meaningless.

**Current identifier slots in the schema:**

| Class | Identifier slot | Effect | Parent slots that become maps |
|-------|----------------|--------|-------------------------------|
| `InteractionAffordance` | `name` | Affordance name = JSON map key | `properties`, `actions`, `events`, `uriVariables` |
| `MultiLanguage` | `language_tag` | Language tag = JSON map key | `titles`, `descriptions` |

---

## 12. Adding a New Class — Checklist

1. Place at the correct position in the file (spec table order).
2. Add `class_uri` pointing to the WoT ontology IRI.
3. Add `description` (plain text, spec-accurate).
4. Add `spec_description` if HTML version needs markup or RFC refs.
5. Add all slots with explicit `range`, `required` list, and `slot_uri` where applicable.
6. If the class appears as a range on another slot, verify the other slot has `inlined: true` if instances are embedded.
7. Run `/verify`.

---

## 13. Adding a New Slot — Checklist

1. Decide: top-level or class-level attribute (see section 9).
2. Set `slot_uri` if this maps to a WoT ontology property.
3. Set `range` explicitly (never rely on `default_range` implicitly).
4. Set `multivalued: true` if the slot can hold more than one value.
5. Set `inlined: true` if the range is a class and instances are embedded.
6. Add to the class `required:` list if normative.
7. Write both `description` and `spec_description` (if different).
8. Run `/verify`.

---

## 14. Required Annotations on Every Class and Slot

| Field | Required | Notes |
|-------|----------|-------|
| `description` | Yes | Plain text, no markup. Must match W3C spec normative definition. |
| `spec_description` | When different from `description` | Use `[[RFC####]]` for bibliography refs; backticks for inline code. |
| `class_uri` / `slot_uri` | Yes, for published WoT terms | See sections 1 and 2. |
| `range` | Yes on every slot | Omitting range inherits `default_range: string` — make it explicit. |
| `required` (in class) | When normative | A REQUIRED slot in the spec must be listed in the class `required:` list. |

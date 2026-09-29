# LinkML Cheatsheet

**Author:** Mahda Noura (mahda.noura@siemens.com)
**Date:** 29.10.2026

---

Quick reference for LinkML features used in WoT schemas. For detailed conventions, see [docs/guidelines/](guidelines/index.md).

---

## Schema Structure

| Keyword | What it does | JSON Schema effect |
|---|---|---|
| `classes` | Define a class | `$defs/<ClassName>` object |
| `slots` | Shared slot (used by multiple classes) | property on every class that lists it |
| `attributes` | Class-local slot (one class only) | same as `slots`, but scoped |
| `types` | Custom scalar types | `type` + `format` or `pattern` |
| `enums` | Enum definitions | `{"type": "string", "enum": [...]}` |
| `imports` | Pull in another schema module | definitions merged into output |
| `prefixes` / `default_prefix` | Namespace declarations | RDF/OWL only — no JSON Schema effect |
| `default_range` | Fallback `range` when none set | avoid relying on this — always set `range` explicitly |

Use `attributes` when a slot belongs to exactly one class. Use `slots` when shared. See [naming conventions §9](guidelines/linkml-naming-conventions.md#9-slot-definitions-top-level-vs-class-level).

---

## Class Keywords

| Keyword | What it does | JSON Schema effect |
|---|---|---|
| `is_a` | Single inheritance | parent properties merged into subclass |
| `mixins` | Inject slots from mixin class(es) | mixin properties merged in |
| `mixin: true` | Mark class as mixin (not standalone) | no `$defs` entry emitted |
| `abstract: true` | Base class only — cannot appear as instance in data | class may or may not appear in `$defs` depending on postprocessors (e.g., `InteractionAffordance` is removed by `jsonschema_flatten_subclasses`) |
| `tree_root: true` | Entry point for JSON Schema validation | becomes root schema object — only `Thing` has this |
| `slot_usage` | Override slot constraints per-class | overrides property constraints in that class's `$defs` entry |
| `extra_slots: allowed: true` | Allow unknown properties | `additionalProperties: true` |
| `class_uri` | RDF class IRI (e.g., `td:Thing`) | no JSON Schema effect — required for OWL/SHACL |
| `rules` | Conditional constraints | `if`/`then` blocks (see Rules section) |

---

## Slot Keywords

| Keyword | What it does | JSON Schema effect |
|---|---|---|
| `range` | Value type — class, type, or enum | `$ref`, `type`, or inline enum |
| `multivalued: true` | Accepts multiple values | `type: array, items: ...` |
| `required: true` | Mandatory field | added to parent's `required: [...]` |
| `inlined: true` | Embed objects instead of referencing by IRI | see Inlining below |
| `inlined_as_list: true` | Force array even when `identifier: true` exists on range | `type: array` instead of dict/map |
| `identifier: true` | Slot value becomes JSON map key | consumed as key — does not appear as a property in generated schema |
| `minimum_value` / `maximum_value` | Numeric bounds | `minimum` / `maximum` |
| `minimum_cardinality` / `maximum_cardinality` | Array length bounds | `minItems` / `maxItems` |
| `pattern` | Regex constraint | `pattern: "..."` |
| `slot_uri` | RDF predicate IRI (e.g., `td:hasPropertyAffordance`) | no JSON Schema effect — required for OWL/SHACL |
| `ifabsent` | Default value expression | no JSON Schema effect |
| `any_of` | OR — matches at least one branch | `anyOf: [...]` |
| `exactly_one_of` | XOR — matches exactly one branch | `oneOf: [...]` |
| `none_of` | NOT — must not match any branch | `not: {anyOf: [...]}` |

---

## Inlining — What Shape Does the JSON Take?

The combination of `inlined`, `multivalued`, and `identifier` determines the JSON output shape. This is the most common source of confusion.

| `inlined` | `multivalued` | Range has `identifier: true` | JSON shape |
|---|---|---|---|
| `true` | `true` | yes | **Dict/map** — identifier value is the key |
| `true` | `true` | no | **Array** of embedded objects |
| `true` | `true` | yes + `inlined_as_list: true` | **Array** of objects (forced, overrides dict) |
| absent | `true` | — | **Array** of URIs or scalars |

Example: `properties` slot → dict because `PropertyAffordance` has `name` with `identifier: true`.
Example: `forms` slot → array because `Form` has no identifier slot.

Full details with generated JSON Schema output: [naming conventions §10](guidelines/linkml-naming-conventions.md#10-inlined-true--embedding-vs-map-vs-array).

---

## Rules (Conditional Constraints)

Used on `Link` class in `hypermedia.yaml`: when `rel` equals `"icon"`, `sizes` becomes required.

```yaml
rules:
  - preconditions:
      slot_conditions:
        rel:
          equals_string: "icon"
    postconditions:
      slot_conditions:
        sizes:
          required: true
```

| Keyword | Where | JSON Schema effect |
|---|---|---|
| `preconditions` | inside a rule | `if: {...}` |
| `postconditions` | inside a rule | `then: {...}` |
| `slot_conditions` | inside pre/postconditions | property-level constraint |
| `equals_string` | inside slot_conditions | `const: "..."` |
| `equals_string_in` | inside slot_conditions | `enum: [...]` |

---

## Enum Keywords

| Keyword | What it does |
|---|---|
| `permissible_values` | Enum members — keys become `"enum"` values in JSON Schema |
| `description` on a value | Appears in generated HTML enum tables |
| `comments` on a value | Internal metadata; extractable via `comment:<prefix>` in `enum_table` content blocks |

Permissible value keys must match the W3C spec exactly (typically lowercase). See [naming conventions §3](guidelines/linkml-naming-conventions.md#3-enum-naming).

---

## Informational Keywords (No JSON Schema Effect)

| Keyword | Where it matters |
|---|---|
| `description` | Spec tables, OWL `rdfs:comment`, SHACL — plain text only |
| `spec_description` | Spec tables only — supports `[[RFC####]]`, backticks, term links |
| `comments` | Internal notes (e.g., cardinality reminders) |
| `todos` | Unresolved questions — greppable |
| `see_also` | Related IRIs — discoverability for maintainers |
| `deprecated` | Marks obsolete terms |

`description` and `spec_description` must stay in sync (same meaning, different markup). See [naming conventions §7](guidelines/linkml-naming-conventions.md#7-description-and-spec_description-sync).

For the full annotation API (`spec_content`, `spec_subsections`, `jsonschema_*`, etc.), see [custom annotations](guidelines/wot-custom-annotations.md).

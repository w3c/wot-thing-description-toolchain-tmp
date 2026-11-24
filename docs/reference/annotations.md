# WoT Custom Annotations

## Why Custom Annotations Exist

LinkML is a general-purpose schema language — it generates JSON Schema, OWL, SHACL, and JSON-LD from schema definitions. But the WoT Toolchain has requirements that LinkML generators do not cover natively:

1. **HTML specification rendering.** The generated `index.html` must produce W3C ReSpec vocabulary tables, testable assertions, rich prose blocks, and enum value tables — none of which are part of LinkML's generation targets. The `spec_*` annotation family drives this custom rendering pipeline; it is described in [Specification annotations](annotations-spec.md).

2. **JSON Schema structural patterns.** The W3C TD specification defines JSON Schema patterns (discriminated unions, flat type hierarchies, operation-specific form variants) that the LinkML JSON Schema generator cannot express. The `jsonschema_*` annotation family instructs the postprocessor to transform the raw generator output into the required shapes.

3. **JSON-LD context mappings.** The TD JSON-LD context requires language maps, `@index` predicates for keyed maps, and explicit scoped vocabularies that the LinkML context generator does not emit. The `jsonld_*` annotation family instructs the context postprocessor to add them.

Custom annotations are **workarounds, not features.** Each one exists because native LinkML cannot express a specific WoT requirement. When an upstream fix lands, the corresponding annotation should be retired.

For the catalog of known LinkML limitations, see [LinkML gaps](../status/linkml-gaps.md).

## Quick Reference

| Annotation | Level | Artifact | Purpose |
|-----------|-------|--------|---------|
| [`jsonld_context`](#jsonld_context) | slot | JSON-LD | Explicit scoped vocabulary prefix, or `none` |
| [`jsonld_index`](#jsonld_index) | slot | JSON-LD | `@index` predicate for a keyed map |
| [`jsonld_container`](#jsonld_container) | slot | JSON-LD | `@container` override (`@language`, `@id`) |
| [`jsonschema_flatten_subclasses`](#jsonschema_flatten_subclasses) | class | JSON Schema | Merge subclass slots into parent |
| [`jsonschema_oneof_dispatch`](#jsonschema_oneof_dispatch) | class | JSON Schema | Discriminated union from subclasses |
| [`jsonschema_enum_subset_partition`](#jsonschema_enum_subset_partition) | class | JSON Schema | One variant per enum subset |
| [`jsonschema_form_subset`](#jsonschema_form_subset) | slot usage | JSON Schema | Narrow array items to one subset variant |
| [`jsonschema_exclude`](#jsonschema_exclude) | class | JSON Schema | Remove class from `$defs` |
| [`dcterms:publisher`](#dctermspublisher) | schema | OWL | The Working Group as a structured publisher |
| [`spec_description`](annotations-spec.md#spec_description) | class, slot | HTML | Spec text with markup (`[[RFC]]`, backticks) |
| [`spec_default`](annotations-spec.md#spec_default) | slot | HTML | `with default` assignment in vocab table |
| [`spec_exclude`](annotations-spec.md#spec_exclude) | class, slot | HTML | Hide class section or structural slot |
| [`spec_content`](annotations-spec.md#spec_content) | class | HTML | Rich content blocks after vocab table |
| [`spec_intro_content`](annotations-spec.md#spec_intro_content) | class | HTML | Rich content blocks before vocab table |
| [`spec_subsections`](annotations-spec.md#spec_subsections) | class | HTML | Sub-headings after class content |
| [`spec_type_values`](annotations-spec.md#spec_type_values) | slot | HTML | Custom "Type" column in vocab table |

## When an Annotation Can Go

An annotation stays only while it expresses semantic metadata, a verified generator gap, or a target-artifact policy.
The right column names what would let it go; the linked [LinkML gaps](../status/linkml-gaps.md) entries describe the gap itself.

| Annotation | Why it is needed | Removable when |
|-----------|------------------|----------------|
| `jsonld_index` | LinkML emits `@container: @index` but not the predicate of the key. `identifier` describes the key field of the value object, not the predicate asserted for the key, and `instantiates` describes a metamodel extension, not an RDF mapping. | LinkML can state a keyed-map predicate ([JSON-LD containers and indexes](../status/linkml-gaps.md#json-ld-containers-and-indexes)). |
| `jsonld_container` | LinkML emits only `@index` and `@set`, not language maps or id maps. | LinkML has a slot-level container setting (same gap). |
| `jsonld_context` | `schemaDefinitions` must get no scoped context although its range would infer one; a slot cannot have a scope per containing class. | LinkML can vary a slot's scope by location ([Location-dependent terms](../status/linkml-gaps.md#location-dependent-terms)). |
| `jsonschema_flatten_subclasses` | The TD Data Schema definition is flat. Flattening every hierarchy by rule would also change unrelated ones, such as security schemes. | Not expected: it is a JSON Schema output choice. |
| `jsonschema_oneof_dispatch` | `designates_type` identifies a LinkML class, while `scheme` values such as `basic` are vocabulary values, and the unknown-scheme fallback is a separate TD rule. | LinkML type designators can state an open extension branch ([Discriminated unions](../status/linkml-gaps.md#discriminated-unions)). |
| `jsonschema_enum_subset_partition`, `jsonschema_form_subset` | One `Form` class carries every `op` value, so which values apply at each location is not derivable from the class graph. | LinkML links subsets to locations ([Enum subsets per location](../status/linkml-gaps.md#enum-subsets-per-location)), or the model gets Form subtypes, which would change every artifact. |
| `jsonschema_exclude` | Not used. | — |
| `dcterms:publisher` | LinkML has `contributors` but no publisher metaslot, and a contributor is not a publisher. | LinkML can model a publisher with a name and URL. |
| `spec_*` | ReSpec placement, formatting, table visibility, assertion anchors and value presentation are editorial requirements, not facts about the model. | Not expected. |

## Decision Principle

Before introducing or keeping an annotation:

1. **Can native LinkML express this, and does the target generator read it?** Prefer `exactly_one_of`, `rules`, `minimum_value`, `multivalued`, etc. See [Native LinkML Features for JSON Schema](#native-linkml-features-for-json-schema) below.
2. **Does a deterministic rule over the resolved schema graph give the result for every current use?** Then derive it instead.
3. **Is the gap already documented?** Check [LinkML gaps](../status/linkml-gaps.md) — a workaround may already exist.
4. **Which artifact does the concern affect?** Use `spec_*` for HTML output, `jsonschema_*` for JSON Schema output, and `jsonld_*` for the JSON-LD context. Never mix them.
5. **Add a focused regression test** before removing an annotation or replacing it with inference.

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

- `extra_slots: allowed: true` — generates `additionalProperties: true`. Used on every vocabulary class except `Any` and `ThingModel`.
- Multivalued inlined slots with identifier keys — generates the `additionalProperties` map pattern. Example: `securityDefinitions`, `properties`, `actions`, `events`.

**Enumerations:**

- `enum` definitions with `permissible_values` — generates inlined `{"type": "string", "enum": [...]}`. Example: `DataSchemaType`, `contentEncodingList`.

## JSON-LD Context Mappings

Use native LinkML `inlined`, `multivalued`, and
`fix_multivalue_containers=True` for JSON-LD list and dictionary containers.
The annotations below declare only mappings that the current LinkML context
generator cannot express.

A slot's scoped vocabulary is normally inferred from its range class; the rule is described in
[JSON-LD context, Scoped Vocabulary Algorithm](../internals/jsonld-context.md#scoped-vocabulary-algorithm).
`jsonld_context` overrides it.

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
`DataSchema` (jsonschema prefix), but upstream W3C merge.js
excludes it from scoped context assignment because schema definitions are
opaque definition containers — their content should not be reinterpreted
through a vocabulary-specific lens.

### `jsonld_index`

**What it does:** declares the RDF predicate represented by keys in an
inlined dictionary-valued slot. LinkML generates `@container: "@index"`
natively but does not currently generate this predicate.
([LinkML gaps, Index maps](../status/linkml-gaps.md#index-maps))

Declared on a slot (top-level slot or `slot_usage`). The value is a CURIE.

```yaml
properties:
  slot_uri: td:hasPropertyAffordance
  annotations:
    jsonld_index: td:name
```

Effect on the JSON-LD context:

- The term definition's `@index` field receives the local name of the CURIE
  (`td:name` becomes `"name"`).
- When the slot also receives a scoped context, the postprocessor ensures that
  the scoped context contains a term resolving to the expanded CURIE.
- The identifier slot of the range class (the map key) is remapped from `@id`
  to its `slot_uri`, or removed from the context when it has none.
- `jsonld_index` has no effect on a slot that also declares
  `jsonld_container: "@language"`.

Currently used on: `properties`, `actions`, `events`, `uriVariables` (TD
module, all with `td:name`) and the `properties` slot usage of `ObjectSchema`
in the JSON Schema module (`jsonschema:propertyName`).

### `jsonld_container`

**What it does:** overrides the `@container` value of a slot's JSON-LD term
definition. LinkML emits only `@index` or `@set` containers and cannot express
language maps or id maps.
([LinkML gaps, Language maps](../status/linkml-gaps.md#language-maps))

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

The postprocessor writes the value to the term's `@container`.

- For `"@language"` it removes `@index` and `@type` from the term definition
  and generates neither an `@index` predicate nor a scoped context.
  Currently used on: `titles`, `descriptions`.
- For `"@id"` each key of the map becomes the IRI of the node it holds,
  resolved against the document base. The slot is treated as a keyed map: it
  receives a scoped context under the same rules as a `jsonld_index` slot, and
  the identifier slot of the range class is remapped from `@id` to its
  `slot_uri`, or removed from the context when it has none. A term that refers
  to such a node by name (`security`, `schema`) is coerced with `@type: @id`
  and resolves to the same IRI.
  Currently used on: `securityDefinitions`, `schemaDefinitions`.

```yaml
securityDefinitions:
  slot_uri: td:definesSecurityScheme
  annotations:
    jsonld_container: "@id"
```

The fixed TD JSON-LD members `@context`, `@type`, and `id` are handled by the
context composer rather than custom schema annotations. `id` maps to `@id` and
must remain optional in generated JSON Schema; do not use `identifier: true`.
The security parameter member uses the native `alias: name`; its private map
key has a distinct internal name and is suppressed structurally from generated
public artifacts.

## JSON Schema Annotations (`jsonschema_*`)

These annotations control how the JSON Schema postprocessor (`src/wot_toolchain/artifacts/jsonschema/postprocess.py`) transforms raw LinkML generator output. They have **no effect** on HTML, OWL, or SHACL output.

The postprocessor reads these annotations via `read_annotations()` and applies transforms in a fixed pipeline order. Adding an annotation to a class automatically activates the corresponding transform — no Python code changes needed.

---

### `jsonschema_flatten_subclasses`

**What it does:** merges all subclass-specific slots into the parent class definition and removes the individual subclass `$defs`. The result is a single flat JSON Schema definition containing every slot from the parent and all its children.

**Why it exists:** the W3C TD spec defines `DataSchema` as one flat type where type-specific properties (`items`, `properties`, `minItems`, etc.) are all merged together. But LinkML's inheritance model generates separate `$defs` for `ArraySchema`, `ObjectSchema`, `NumberSchema`, etc. ([LinkML gaps](../status/linkml-gaps.md))

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

**Why it exists:** the W3C TD specification uses the `scheme` field value (`"basic"`, `"oauth2"`, etc.) to select which `SecurityScheme` subclass applies, and admits additional schemes with a prefixed `scheme` value. LinkML has no native discriminated-union dispatch. ([LinkML gaps, Discriminated unions](../status/linkml-gaps.md#discriminated-unions))

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

**Why it exists:** the W3C TD specification restricts the allowed `op` values of a `Form` by where it appears (Thing level, property, action, event). LinkML generates a single `Form` definition. ([LinkML gaps, Form variants per affordance](../status/linkml-gaps.md#form-variants-per-affordance))

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

## `dcterms:publisher`

Appears once in each schema module and expresses the W3C Working Group as a structured RDF organization in the generated OWL.

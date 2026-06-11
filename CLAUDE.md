# CLAUDE.md — WoTIS Toolchain

## Project Overview

WoTIS (Web of Things Integrated Schemas) is a Python CLI tool that generates W3C WoT Thing Description 2.0 specification artifacts from LinkML YAML schemas.

**Pipeline:** LinkML YAML schemas → generators (JSON Schema, SHACL, JSON-LD Context, OWL, visualization) → spec HTML (ReSpec-based)

## Repository Structure

```
src/wotis/
├── cli.py                  # Click CLI entry point (`wotis` command)
├── __init__.py             # Constants, paths, config
├── generators/             # LinkML-based resource generators
│   ├── __init__.py         # run_pipeline() orchestrator
│   ├── respec.py           # Spec document generator (calls specgen)
│   └── visualization.py    # Mermaid diagram generator
├── specgen/                # Spec generation internals
│   ├── config.py           # Config dataclass (paths, placeholders)
│   ├── respec.py           # Jinja env setup, template assembly
│   ├── tables.py           # Vocabulary table rendering (slot_type_text, etc.)
│   ├── assertions.py       # RFC 2119 assertion extraction → CSV
│   └── bikeshed_processor.py  # Bikeshed BYOS fragment processing
├── postprocessors/         # Per-format output postprocessing
└── preprocessing/          # Input preprocessing (JSON-LD context)

resources/
├── schemas/                # LinkML YAML schemas (the source of truth)
├── index.template.html     # ReSpec template with %s placeholders
├── jinja_templates/        # Jinja2 templates for vocab sections
└── xref/glossary.yaml      # Term definitions for autolinking

tests/                      # Golden-file and structural tests
```

## Key Commands

```bash
uv sync                                    # Install dependencies
uv run wotis generate-wot-resources         # Generate resources only
uv run wotis generate-wot-resources -d      # Generate resources + spec HTML
uv run wotis generate-wot-resources -d --assertions-csv resources/gens/assertions.csv # Generate resources + spec HTML + Respec assertions from HTML spec
```

## Build System

- **Package manager:** uv
- **Build backend:** hatchling
- **Python:** >=3.14
- **Entry point:** `src.wotis.cli:main`

## Architecture Notes

- The spec document is assembled by injecting 4 vocabulary section fragments into `index.template.html` via `%s` placeholders
- ReSpec renders the final document client-side (boilerplate, ToC, bibliography)
- LinkML YAML schemas use custom annotations (`spec_description`, `spec_content`, `spec_subsections`, etc.) to drive spec rendering — see `resources/schemas/README.md`
- Glossary terms in `resources/xref/glossary.yaml` define autolinking targets

## JSON Schema Generation

  The postprocessor (`src/wotis/postprocessors/jsonschema_postprocessor.py`) reads `jsonschema_*` annotations from LinkML schemas and applies transforms to produce spec-compliant JSON Schema. Native LinkML
  features are used wherever possible; annotations exist only for transforms LinkML can't express natively.

  ### Custom Annotations (`jsonschema_*`)

  - **`jsonschema_flatten_subclasses`** (class-level, boolean) — Merge all subclass slots into the parent and remove subclass `$defs`. Used on `DataSchema`.
  - **`jsonschema_oneof_dispatch`** (class-level) — Discriminated `oneOf` union from subclasses. Keys: `discriminator`, `include_unknown`.
  - **`jsonschema_form_variants`** (class-level) — Split a class into operation-specific variants by `op` values.
  - **`jsonschema_exclude`** (class-level, boolean) — Exclude a class from JSON Schema `$defs`.

  ### Native LinkML → JSON Schema Patterns

  - `mixins` → mixin slots included in class properties (replaces previous custom annotation`jsonschema_merge_from`)
  - `rules` with `preconditions`/`postconditions` → `if`/`then` (replaces previous custom annotation `jsonschema_link_discrimination`)
  - Multivalued inlined slots with identifier keys → `additionalProperties` (replaces custom previous annotation`jsonschema_dict_style`)
  - `exactly_one_of` → `oneOf` (use for "single value OR array" patterns)
  - `extra_slots: allowed: true` → `additionalProperties: true`
  - `minimum_value` + `none_of: [{equals_number: 0}]` → `exclusiveMinimum: 0`
  - `minimum_cardinality: 1` on multivalued branch → `minItems: 1`
  - `minimum_value` on slots → `minimum` constraint
  - Enums → inlined as `{"type": "string", "enum": [...]}` by the postprocessor

  ### Postprocessor Pipeline Order

  1. `_apply_additional_properties` 2. `_flatten_subclasses` 3. `_build_oneof_dispatch` 4. `_build_form_variants` 5. `_normalize_types` 6. `_simplify_exclusive_minimum` 7.
  `_remove_identifier_slots` 8. `_remove_excluded_defs` 9. `_resolve_refs` 10. `_clean_metadata`

## Snippets

- Snippets: `resources/snippets/*.jsonc` — JSONC files injected into spec via `{{ snippet('name') }}` in `index.template.html`
- Snippet groups (tabbed examples): `resources/snippets/groups/*.yaml` — injected via `{{ snippet_group('name') }}`
- Ground-truth schemas for snippet validation: `resources/ground-truth-schemas/` — not generated, stored manually
- `validate: false` in frontmatter skips JSON Schema validation (use for partial/placeholder snippets)
- `// @hide-start` / `// @hide-end` hides boilerplate lines from rendered output (replaced with `// ...`)
- Validation errors → `ERROR` log, pipeline continues. Parse failures on `validate:true` snippets → `ERROR`.
- Common fix: "Failed to parse JSON in snippet" → snippet has `// ...` or `{{PLACEHOLDER}}`, add `validate: false`
- Full reference: `docs/snippets.md`

## Spec Generator Custom Annotations (LinkML → HTML)

- `spec_description` — richer prose for spec (markdown, cross-refs, RFC keywords); overrides `description` in spec output only
- `spec_content` — content blocks rendered after the class property table
- `spec_subsections` — nested `<section>` elements after `spec_content`
- Block types: `markdown`, `paragraph` (with assertion `id`s), `list`, `note`, `enum_table`
- Full reference: `docs/spec-content-blocks.md`

### `spec_description` Markup Rules

- Cross-references to spec terms: `[=TermName=]` (Bikeshed dfn syntax) → renders as a link to the term's section
  - **NOT** `*TermName*` — that produces `<em>TermName</em>`, not a link
- RFC 2119 keywords in description prose: plain text (`SHOULD`, `MUST`, `MAY`)
  - **NOT** `*SHOULD*` — that produces `<em>SHOULD</em>`
- Code spans: `` `term` `` → `<code>term</code>`
- Bikeshed bibliography refs: `[[RFC2045]]` → rendered by Bikeshed

### Spec Table Generator Type Column Rules (`tables.py:slot_type_text`)

| LinkML slot flags | Spec table renders as |
|---|---|
| scalar (no multivalued) | `TypeName` |
| `inlined: true` only (scalar) | `TypeName` — inlined used only for JSON Schema `$ref`, not a map |
| `inlined: true` + `multivalued: true` | `Map of TypeName` — identifier-keyed map |
| `multivalued: true` (no inlined) | `Array of TypeName` |
| `inlined_as_list: true` + `multivalued: true` | `Array of TypeName` |
| `exactly_one_of` branches | each branch rendered individually, joined with ` or ` |

## Key File Roles

| File/Dir | Role |
|---|---|
| `resources/schemas/` | LinkML YAML — single source of truth |
| `resources/index.template.html` | Jinja2 spec template — insert `{{ snippet() }}` calls here |
| `resources/snippets/` | JSONC code examples for the spec |
| `resources/snippets/groups/` | YAML definitions for tabbed snippet groups |
| `resources/ground-truth-schemas/` | TD/TM JSON Schemas used only for snippet validation |
| `resources/xref/glossary.yaml` | Autolink term definitions |
| `src/wotis/postprocessors/jsonschema_postprocessor.py` | Transforms LinkML-generated JSON Schema |
| `src/wotis/specgen/snippets.py` | Snippet parsing, validation, rendering |
| `docs/` | Developer documentation (snippets, spec blocks, LinkML cheatsheet) |

## Git Rules

- **NEVER add Co-Authored-By, Signed-off-by, or any attribution to Claude/Anthropic in commits.** No exceptions.
- Commit author must always be the user's configured git identity.
- Do not force push without explicit user approval.

## CI/CD

- `.github/workflows/main.yaml` — PR checks (resource + spec generation)
- `.github/workflows/deploy-docs.yaml` — Deploy spec to GitHub Pages on push to main
- `.github/workflows/pypi-publish.yaml` — Publish to PyPI on release

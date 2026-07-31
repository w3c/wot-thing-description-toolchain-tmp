# WOTIS — Agent & Contributor Guide

## Project Overview

**WoT Integrated Schemas (WOTIS)** replaces the [W3C WoT Thing Description toolchain](https://github.com/w3c/wot-thing-description/). The old toolchain is partially automated: SPARQL Template Language (STTL) queries over SHACL shape descriptions populate `%`-placeholders in `resources/index.template.html` to generate the vocabulary tables in the spec. What is written entirely by hand — and drifts — is: the JSON-LD context, the ontologies (td, hctl, tm, wotsec), the SHACL shapes, the JSON Schema, and the TypeScript types derived from the JSON Schema. Inconsistencies between these hand-authored artifacts (e.g., a field typed `string` in one file and `integer` in another) are the core problem this toolchain solves.

This toolchain uses **one LinkML schema as the single source of truth** and generates all official W3C artifacts from it. Consistency is structural and semantic.

**One LinkML schema → generate all artifacts:**

| Artifact | Path |
|---|---|
| W3C TD Specification (HTML) | `resources/gens/index.html` |
| TD/TM JSON Schema | `resources/gens/jsonschema/jsonschema.json` |
| JSON-LD Context | `resources/gens/jsonldcontext/context.jsonld` |
| SHACL Shapes | `resources/gens/shacl/shapes.shacl.ttl` |
| OWL Ontology | `resources/gens/owl/ontology.owl.ttl` |
| Assertion CSVs | `resources/gens/assertions/` |

## Codebase Layout

```
resources/schemas/          ← SOURCE OF TRUTH (edit here, not in gens/)
  thing_description.yaml    ← main TD schema; imports the others
  hypermedia.yaml           ← HCTL vocabulary
  wot_security.yaml         ← security vocabulary
  jsonschema.yaml           ← JSON Schema vocabulary
  README.md                 ← annotation rules (read before touching annotations)

src/wotis/
  cli.py                    ← entry point: wotis generate-wot-resources [-d]
  generators/               ← LinkML → raw artifacts
  postprocessors/           ← adjust raw LinkML output to meet W3C WoT TD requirements
    json_schema_postprocessor.py
    jsonld_context_postprocessor.py
    shacl_postprocessor.py
  specgen/                  ← HTML spec generation
    respec.py / bikeshed_processor.py
    tables.py               ← vocabulary tables
    snippets.py             ← code example rendering
    assertions.py           ← assertion CSV output

resources/snippets/         ← TD/TM code examples shown in the spec
  *.jsonc                   ← individual snippet files
  groups/*.yaml             ← tabbed example groups
  TEMPLATE.jsonc            ← copy this when adding a snippet

tests/
  manual_goldens/           ← authoritative hand-verified reference outputs
  data/td11/                ← TD 1.1 instance files (valid + invalid)
  data/td20/                ← TD 2.0 instance files (valid + invalid)
```

## Setup

After cloning, run once:

```bash
uv sync
pre-commit install
```

`pre-commit install` activates the hooks in `.pre-commit-config.yaml`. On every commit:
- **ruff** lints and auto-fixes Python files
- **linkml-lint** validates all four schema YAML files (only when any `resources/schemas/*.yaml` changed)

If `pre-commit` is not installed: `uv tool install pre-commit` or `pip install pre-commit`.

---

## The Postprocessor Pattern

Postprocessors in `postprocessors/` exist **only** for aspects that LinkML cannot currently model. They are not the default solution — they are the last resort.

**Before writing a postprocessor:**
1. Check `KNOWN_LINKML_GAPS.md` — if the gap is already documented, use the existing workaround pattern.
2. If not documented: run `/check-linkml <feature>` to search docs and GitHub issues.
3. If LinkML supports it natively, model it in the schema — no postprocessor.
4. Only if LinkML genuinely cannot express it: write a postprocessor, add a comment citing the LinkML limitation (link to the issue/PR), add a `TODO: remove when LinkML #NNNN is merged` note, and add the gap to `KNOWN_LINKML_GAPS.md`.

**When a postprocessor is justified:**
- Add it to the relevant file in `postprocessors/`.
- Comment must cite: the W3C requirement satisfied AND the LinkML gap that forces this approach.
- Test the postprocessor directly, not only via the full pipeline.

Never edit files under `resources/gens/` directly — they are overwritten on every run.

## Custom LinkML Annotations

Annotations in `annotations:` blocks within the schema YAML files drive HTML spec generation. Full examples are in `resources/schemas/README.md`.

| Annotation | Scope | Purpose |
|---|---|---|
| `spec_description` | slot | Overrides `description` in spec vocabulary tables |
| `spec_default` | slot | Marks slot as having a default value |
| `spec_exclude` | slot | Hides slot from spec tables (internal fields only) |
| `spec_content` | class | Rich content blocks (notes, paragraphs, lists) after vocabulary table |
| `spec_intro_content` | class | Same as `spec_content`, rendered before the table |
| `spec_subsections` | class | Subsections after class content |
| `spec_type_values` | slot | Allowed/example values in the type column |

**Annotation rules:**
- `spec_description`: use `[[RFC####]]` for bibliography refs (not bare URLs); use backticks for inline code.
- Segment `id` values inside `spec_content` / `spec_intro_content` become assertion anchors — follow pattern `td-{kebab-case}`, must be unique per file.
- `spec_type_values` with `mode: one_of` must be exhaustive.
- A slot with `spec_exclude: true` must not carry any other `spec_*` annotation.
- When `spec_description` is added, update the base `description` to match (minus markup).

## Testing and Quality


### Running Tests

```bash
# Full pipeline — verify it exits cleanly
uv run wotis generate-wot-resources -d 2>&1 | grep -E "ERROR|WARNING"

# All tests (on main branch)
uv run pytest tests/ -v

# Spec HTML structure tests (exist on main)
uv run pytest tests/test_spec_content_rendering.py tests/test_golden_form_structure.py -v
```

**Note:** `test_td_instance_gate.py`, `test_golden_diff.py`, and `td_gate_known_failures_*.txt` do not exist on `main` yet — they are added by PR #63. Once merged, the full test command set expands.

### Test Suite State on `main`

Known pre-existing failures on `main` as of 2026-07 — do not investigate, do not try to fix unless specifically assigned:

| Test | Failure | Root cause |
|---|---|---|
| `test_golden_form_structure.py` — 21 failures | `Form section not found` in generated HTML | `Form` class subsections not emitted correctly by HTML generator; added by PR #58 as a regression baseline |

These failures exist in CI on `main`. A PR that does not touch the Form class or HTML generation must not introduce new failures in this file.

### Generation Error Taxonomy

`uv run wotis generate-wot-resources -d` output signals:

| Pattern | Action |
|---|---|
| `DeprecationWarning` from `owlgen.py` lines 244/247/250 | **Ignore** — known LinkML 1.10.0 noise; issues #3190/#3191 |
| `WARNING:linkml.generators.owlgen: Multiple owl types` | **Ignore** — known OWL gen behavior, not a bug |
| `WARNING: Failed to parse JSON in snippet: *.jsonc` | **Investigate** — snippet has invalid JSONC syntax |
| `ERROR:root:Snippet validation error: FILE: PATH — MESSAGE` | **Fix** — snippet fails JSON Schema validation; pipeline aborts |
| Any other `ERROR:` line | **Fix** — generation failed |

The pipeline aborts on any snippet validation ERROR. Fix before declaring the change complete.

### Known-Failures Baseline

Valid TD instances that the generated JSON Schema currently rejects (known fidelity gaps) are tracked in baseline files added by PR #63. Rules (apply once those files exist on `main`):
- List only valid TD files (`*-valid.jsonld`), never invalid ones.
- Each entry must correspond to a tracked issue.
- Fixing a gap removes its entry — the list can only shrink.
- An xfail turning into an XPASS breaks CI — remove the entry from the baseline file.

### Golden Files

Two categories with different update policies:

| Directory | Type | Update policy |
|---|---|---|
| `tests/manual_goldens/` | Hand-verified, authoritative | Require explicit maintainer approval in PR description; never auto-update |
| `tests/goldens/` (PR #63+) | Machine-updatable snapshots | Update via `--update-goldens` flag when an intentional change is verified |

**When a golden diff CI job fails:**
1. Read the diff — is it expected from the schema change?
2. If expected: run `uv run pytest tests/test_golden_diff.py --update-goldens`, commit the updated snapshot, explain in PR description.
3. If unexpected: the change has a side-effect — investigate before updating.
4. Never update `manual_goldens/` via `--update-goldens` — these require human review.

### What "Correct" Means

A change is complete when all of these hold:

1. `uv run wotis generate-wot-resources -d` exits without ERROR.
2. `uv run pytest tests/ -v` passes (xfail acceptable, no new unexpected failures).
3. Snippets in `resources/snippets/` validate against the generated JSON Schema — run `/validate-snippets`. Every `.jsonc` linked to a changed class or slot must pass; `validate: false` is only acceptable for non-TD/TM examples.
4. HTML output is correct — see below.

#### HTML Correctness

`resources/gens/index.html` is produced by rendering `resources/index.template.html`. The template is mostly hand-written; the `%`-placeholders are replaced by the auto-generated parts (vocabulary tables, assertion anchors, etc.). Only the auto-generated parts need to be verified — the hand-written prose is not in scope unless the schema changes affect it.

Check the auto-generated sections for:

- **Vocabulary tables** — every term in the table must match the LinkML schema: name, description, type column, and optionality (REQUIRED / OPTIONAL). Cross-check against `tests/manual_goldens/html/` for any change.
- **Assertion anchors** — every normative statement that should be an assertion must have a Respec `<span id="td-...">` anchor. If a normative statement lacks an anchor, it is a gap. Anchor IDs must follow the `td-{kebab-case}` convention and be globally unique in the document.
- **Respec cross-references** — terms referenced inside the spec must use `<a>` with the correct definition link or `[[RFC####]]` bibliography syntax. Bare URLs are not acceptable for normative references.
- **Class names** — class names in the vocabulary tables must match the LinkML class names exactly (no renaming, no abbreviation).
- **Type column accuracy** — the type shown for each slot must match the LinkML range: if range is a class, the type should name that class; if range is a scalar, the JSON Schema primitive must be correct. `spec_type_values` overrides must be verified for exhaustiveness when `mode: one_of`.
- **Optional/mandatory** — a slot marked `required` in LinkML must appear as REQUIRED in the table. A slot not in `required` must appear as OPTIONAL. Mismatches are blocking errors.

When reviewing HTML changes, do not evaluate the entire document — scope the check to the `%`-replaced sections and any `spec_content` / `spec_intro_content` blocks that changed.

### CI Pipeline (GitHub Actions)

Four jobs in sequence: `static-analysis` → `build` → [`test-gates` ∥ `golden-diff`].

| Job | What it checks |
|---|---|
| `static-analysis` | Ruff lint; LinkML schema lint (non-blocking) |
| `build` | Full artifact generation; all output files non-empty; package builds |
| `test-gates` | TD instance gate; W3C cross-check; HTML structure tests |
| `golden-diff` | Generated JSON Schema + context vs committed snapshots |

## Language Style

### Python

**Architecture:**
- YAGNI first — no abstractions, generic wrappers, or future-proofing. Write minimum code for the current requirement.
- Prefer pure functions over classes unless managing complex state.
- Composition over inheritance — no deep class hierarchies.
- Keep POC features isolated and deletable, not entangled with core logic.
- Decouple business logic from IO and global state.

**Pythonic style:**
- Standard library first: exhaust `pathlib`, `itertools`, `collections`, `functools` before adding external dependencies.
- Use `dataclasses` for data containers; `set` for membership testing; `dict.get()` / `defaultdict` for missing keys.
- Use `enumerate()`, `zip()`, comprehensions. Never `range(len())`.
- Type hints mandatory on all function signatures and class attributes (PEP 484).
- Prefer `TypedDict` over plain `dict` or `Mapping` for structured data.
- Implement `__repr__` and `__str__` where the class appears in logs or error output.

**Naming:**
- Names must reflect content and intent — no `val`, `data`, `temp`, `item`.
- Booleans prefixed with `is_`, `has_`, or `should_`.
- `snake_case` for variables/functions, `PascalCase` for classes.

**Bloat control:**
- Guard clauses — return early, keep nesting depth < 3.
- Extract into a new function if the current one exceeds 20 lines.
- No `from module import *`. No magic strings — use `enum.Enum`.
- Prefer `try...except` (EAFP) over pre-checking `if` conditions.
- Before writing complex logic, search for an idiomatic stdlib or well-maintained library solution.

**Logging:**
- No `print()` — `logging` module only.
- `debug` for granular execution, `info` for lifecycle events, `warning` for handled issues, `error` for failures (with `exc_info=True`).
- Configure logging in `cli.py` only — never inside library modules.

### YAML / LinkML

- Snake_case for slot names, PascalCase for class names.
- Always include `description` on every slot and class.
- `spec_description` and base `description` must stay in sync.
- Use `see_also` to link to relevant W3C spec sections.

### Snippets (`.jsonc`)

- Every snippet must be a complete, valid TD or TM.
- Use `// @hide-start` / `// @hide-end` to hide boilerplate (e.g., `securityDefinitions`).
- The JSONC front-matter `id` must be unique across all snippets.
- Set `validate: false` only for non-TD/TM snippets (e.g., partial JSON Schema examples).

## General Project Conventions

- **Never edit `resources/gens/`** — generated on every run.
- **Schema is authoritative.** If a generated artifact looks wrong, fix the schema or the postprocessor.
- **Postprocessors patch generator gaps** — document the W3C requirement the fix satisfies.
- **Golden files in `tests/manual_goldens/`** are authoritative and require maintainer approval to update.
- **PRs target `main` directly** (fork → branch → PR to main).
- **W3C compliance is a hard constraint**, not a preference. Spec text must use RFC 2119 (MUST/SHOULD/MAY) where normative, and bibliography refs must use Respec `[[RFC####]]` syntax.

## Conflict Zones

Files with high concurrent-edit risk. Check for in-progress PRs before touching.

| File | Why it's a conflict zone | Rule |
|---|---|---|
| `resources/schemas/thing_description.yaml` | Main schema — almost every PR touches it | Always branch from a fresh `main`; rebase before opening PR |
| `resources/index.template.html` | Hand-written spec prose — merge conflicts are semantic | Coordinate with maintainer before large structural edits |
| `tests/manual_goldens/` | Authoritative reference outputs | Never update without maintainer sign-off; see Golden Files above |

**Branching strategy:**
- Fork the repo; branch from `main` (not from another contributor's branch).
- Keep branches focused — one logical change per PR.
- Before opening a PR, rebase on latest `main` and re-run generation to ensure clean output.

## Current Priorities (2026-07)

1. JSON Schema correctness — all td11 + td20 instance validations pass.
2. HTML spec correctness — structure and vocabulary tables match `tests/manual_goldens/html/`.
3. Snippet validity — all `.jsonc` files validate against the generated JSON Schema.
4. Assertion CSVs — assertions match anchors in `index.html`.

Out of scope for now: automated ontology/SHACL consistency (manual_goldens exist as reference only).

## Available Claude Code Skills

| Skill | When to use |
|---|---|
| `/verify` | Full closed-loop check after any schema/postprocessor change: sync deps, generate, validate snippets, run tests |
| `/generate` | Run full pipeline, surface only errors/warnings |
| `/schema-diff` | Show what changed in LinkML schemas |
| `/validate-snippets` | Check snippet validation errors only |
| `/validate-consistency` | After schema change: detect cross-artifact drift |
| `/check-linkml <feature>` | Check if LinkML supports a feature natively before writing a postprocessor |
| `/review-pr <number>` | Review a PR against all project rules |

**Before running any pipeline command**, ensure deps are current:
```bash
uv sync
```

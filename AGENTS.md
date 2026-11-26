# wot-toolchain — Agent & Contributor Guide

## Project Overview

**wot-toolchain** replaces the [W3C WoT Thing Description toolchain](https://github.com/w3c/wot-thing-description/). The old toolchain is partially automated: SPARQL Template Language (STTL) queries over SHACL shape descriptions populate `%`-placeholders in `resources/index.template.html` to generate the vocabulary tables in the spec. What is written entirely by hand — and drifts — is: the JSON-LD context, the ontologies (td, hctl, tm, wotsec), the SHACL shapes, the JSON Schema, and the TypeScript types derived from the JSON Schema. Inconsistencies between these hand-authored artifacts (e.g., a field typed `string` in one file and `integer` in another) are the core problem this toolchain solves.

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
  README.md                 ← points to docs/guidelines/ (read before touching schemas)

src/wot_toolchain/
  cli.py                    ← entry point: wot-toolchain generate-wot-resources (generators listed in wot-toolchain.yaml)
  pipeline.py               ← runs the LinkML generators and the postprocessors
  generators/               ← respec.py (specification HTML), visualization.py (diagrams)
  artifacts/                ← adjust raw LinkML output to meet W3C WoT TD requirements
    transforms.py           ← Transform (name, kind, reason) and run_transforms
    jsonschema/              ← postprocess.py (transform list, entry point) and one module per group of transforms
    shacl/postprocess.py
  specgen/                  ← HTML spec generation
    respec.py / bikeshed_processor.py
    tables.py               ← vocabulary tables
    snippets.py             ← code example rendering
    assertions.py           ← assertion CSV output

resources/snippets/         ← TD/TM code examples shown in the spec
  *.json                    ← individual snippet files
  _snippets.yaml            ← snippet metadata (id, title, hide_paths, etc.)

tests/
  unit/                     ← tests that run without generated files
  conformance/              ← TD instances validated against the generated JSON Schema
  goldens/                  ← generated output compared with snapshots and upstream files
  resources/td/<topic>/     ← td-next TD instance files in valid/ and invalid/
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

See [Postprocessor Conventions](docs/guidelines/postprocessor-conventions.md) for when and how to write postprocessors. See [Known LinkML Gaps](docs/known-linkml-gaps.md) for documented generator limitations.

Never edit files under `resources/gens/` directly — they are overwritten on every run.

## Custom LinkML Annotations

See [WoT Custom Annotations](docs/guidelines/wot-custom-annotations.md) for the full annotation API, examples, and decision principles. See [LinkML Naming Conventions](docs/guidelines/linkml-naming-conventions.md) for schema structural rules, `inlined`/`identifier` patterns, and checklists.

## Testing and Quality


### Running Tests

```bash
# Generate the artifacts; the tests in conformance/ and goldens/ read them
uv run wot-toolchain generate-wot-resources

# All tests
uv run pytest
```

CI runs the same `uv run pytest` call. Every test must pass; the suite has no
known failures. `tests/README.md` lists what each test file checks.

### Generation Error Taxonomy

`uv run wot-toolchain generate-wot-resources` output signals:

| Pattern | Action |
|---|---|
| `DeprecationWarning` from `owlgen.py` lines 244/247/250 | **Ignore** — known LinkML 1.10.0 noise; issues #3190/#3191 |
| `WARNING:linkml.generators.owlgen: Multiple owl types` | **Ignore** — known OWL gen behavior, not a bug |
| `WARNING: Failed to parse JSON in snippet: *.json` | **Investigate** — snippet has invalid JSON syntax |
| `ERROR:root:Snippet validation error: FILE: PATH — MESSAGE` | **Fix** — snippet fails JSON Schema validation; pipeline aborts |
| Any other `ERROR:` line | **Fix** — generation failed |

The pipeline aborts on any snippet validation ERROR. Fix before declaring the change complete.

### Failure Policy

The suite has no accepted failures. A generated-schema rejection of a valid
sample, a generated-versus-upstream schema mismatch, or an HTML-structure
regression fails the relevant test directly.

### Golden Files

| Directory | Content | Update policy |
|---|---|---|
| `resources/upstream/` | W3C reference files: td-next JSON Schema, `assertions.csv`, `html/index.html` | Never updated by a test; change only with maintainer approval in the PR description |
| `tests/resources/snapshots/` | Snapshots of the generated JSON Schema, JSON-LD context and spec sections | Update with `--update-goldens` after reviewing an intended change |

**When `tests/goldens/test_snapshots.py` fails:**
1. Read the diff — is it expected from the schema change?
2. If expected: run `uv run pytest tests/goldens/test_snapshots.py --update-goldens`, commit the updated snapshot, explain in PR description.
3. If unexpected: the change has a side-effect — investigate before updating.

### What "Correct" Means

A change is complete when all of these hold:

1. `uv run wot-toolchain generate-wot-resources` exits without ERROR.
2. `uv run pytest` passes with no failures.
3. Snippets in `resources/snippets/` validate against the generated JSON Schema. Every `.json` linked to a changed class or slot must pass; `validate: false` is only acceptable for non-TD/TM examples.
4. HTML output is correct — see below.

#### HTML Correctness

`resources/gens/index.html` is produced by rendering `resources/index.template.html`. The template is mostly hand-written; the `%`-placeholders are replaced by the auto-generated parts (vocabulary tables, assertion anchors, etc.). Only the auto-generated parts need to be verified — the hand-written prose is not in scope unless the schema changes affect it.

Check the auto-generated sections for:

- **Vocabulary tables** — every term in the table must match the LinkML schema: name, description, type column, and optionality (REQUIRED / OPTIONAL). Cross-check against `resources/upstream/html/index.html` for any change.
- **Assertion anchors** — every normative statement that should be an assertion must have a Respec `<span id="td-...">` anchor. If a normative statement lacks an anchor, it is a gap. Anchor IDs must follow the `td-{kebab-case}` convention and be globally unique in the document.
- **Respec cross-references** — terms referenced inside the spec must use `<a>` with the correct definition link or `[[RFC####]]` bibliography syntax. Bare URLs are not acceptable for normative references.
- **Class names** — class names in the vocabulary tables must match the LinkML class names exactly (no renaming, no abbreviation).
- **Type column accuracy** — the type shown for each slot must match the LinkML range: if range is a class, the type should name that class; if range is a scalar, the JSON Schema primitive must be correct. `spec_type_values` overrides must be verified for exhaustiveness when `mode: one_of`.
- **Optional/mandatory** — a slot marked `required` in LinkML must appear as REQUIRED in the table. A slot not in `required` must appear as OPTIONAL. Mismatches are blocking errors.

When reviewing HTML changes, do not evaluate the entire document — scope the check to the `%`-replaced sections and any section prose files under `resources/spec/sections/` that changed.

### CI Pipeline (GitHub Actions)

`main.yaml` runs the following jobs in sequence: `static-analysis` → `build` → `tests` → `deploy-pages`.

| Job | What it checks |
|---|---|
| `static-analysis` | Ruff lint; LinkML schema lint (non-blocking) |
| `build` | Full artifact generation; all output files non-empty; package builds; uploads `resources/gens/` as the Pages artifact on `main` |
| `tests` | The whole test suite: `uv run pytest` |
| `deploy-pages` | Pushes to `main` only: publishes the tested `resources/gens/` to GitHub Pages once `tests` passes |

The hand-drawn spec figures live in `resources/static/visualization/` (copied from `w3c/wot-thing-description`) and are copied into `resources/gens/visualization/` during `-d` generation.

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

### Snippets (`.json`)

- Every snippet must be a complete, valid TD or TM.
- Metadata (id, title, hide_paths, show_paths) lives in `_snippets.yaml`, not in the JSON file.
- Snippet `id` must be unique across all snippets and not conflict with IDs in `index.template.html`.
- Set `validate: false` only for non-TD/TM snippets (e.g., partial examples).
- See [Snippet Authoring Guide](docs/guidelines/snippet-authoring.md) for worked examples.

## General Project Conventions

- **Never edit `resources/gens/`** — generated on every run.
- **Schema is authoritative.** If a generated artifact looks wrong, fix the schema or the postprocessor.
- **Postprocessors patch generator gaps** — document the W3C requirement the fix satisfies.
- **Reference files in `resources/upstream/`** are authoritative and require maintainer approval to update.
- **PRs target `main` directly** (fork → branch → PR to main).
- **W3C compliance is a hard constraint**, not a preference. Spec text must use RFC 2119 (MUST/SHOULD/MAY) where normative, and bibliography refs must use Respec `[[RFC####]]` syntax.

## Conflict Zones

Files with high concurrent-edit risk. Check for in-progress PRs before touching.

| File | Why it's a conflict zone | Rule |
|---|---|---|
| `resources/schemas/thing_description.yaml` | Main schema — almost every PR touches it | Always branch from a fresh `main`; rebase before opening PR |
| `resources/index.template.html` | Hand-written spec prose — merge conflicts are semantic | Coordinate with maintainer before large structural edits |
| `resources/upstream/` | W3C reference files | Never update without maintainer sign-off; see Golden Files above |

**Branching strategy:**
- Fork the repo; branch from `main` (not from another contributor's branch).
- Keep branches focused — one logical change per PR.
- Before opening a PR, rebase on latest `main` and re-run generation to ensure clean output.

## Current Priorities (2026-07)

1. JSON Schema correctness — all td-next instance validations pass.
2. HTML spec correctness — structure and vocabulary tables match `resources/upstream/html/index.html`.
3. Snippet validity — all `.json` files validate against the generated JSON Schema.
4. Assertion CSVs — assertions match anchors in `index.html`.

Out of scope for now: automated ontology/SHACL consistency.

**Before running any pipeline command**, ensure deps are current:
```bash
uv sync
```

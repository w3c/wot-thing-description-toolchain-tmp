# wot-toolchain — Agent & Contributor Guide

## Project Overview

**wot-toolchain** is intended to replace the [W3C WoT Thing Description toolchain](https://github.com/w3c/wot-thing-description/). The old toolchain is partially automated: SPARQL Template Language (STTL) queries over SHACL shape descriptions populate `%`-placeholders in `resources/index.template.html` to generate the vocabulary tables in the spec. What is written entirely by hand — and drifts — is: the JSON-LD context, the ontologies (td, hctl, tm, wotsec), the SHACL shapes, the JSON Schema, and the TypeScript types derived from the JSON Schema. Inconsistencies between these hand-authored artifacts (e.g., a field typed `string` in one file and `integer` in another) are the core problem this toolchain solves.

This toolchain uses **one LinkML schema as the single source of truth** and generates all official W3C artifacts from it. Consistency is structural and semantic.

**This repository is an installable tool and library consumed by other repositories.** Each consumer keeps its own LinkML schemas and its own `wot-toolchain.yaml` config file and installs a pinned git tag of this package (no PyPI release):

```bash
uv tool install git+https://github.com/w3c/wot-thing-description-toolchain-tmp@<tag>
```

- First consumer: `w3c/wot-thing-description`; its LinkML schemas will live there under `linkml/`.
- Second consumer (later): `w3c/wot-binding-templates`.
- The schemas and test data in this repository target the next TD version, labelled `td-next`.

Rule for agents: **no TD-specific knowledge in Python.** Project-specific configuration (file names, prefixes, labels, sections, paths) goes into the config file — not into new LinkML annotations and not into hard-coded names in `src/wot_toolchain/`.

Release-quality outputs: JSON Schema, spec HTML with assertions CSV, JSON-LD context. Experimental: OWL, SHACL, class diagrams (visualization).

**One LinkML schema → generate all artifacts:**

| Artifact | Path |
|---|---|
| W3C TD Specification (HTML) | `resources/gens/index.html` |
| TD/TM JSON Schema | `resources/gens/jsonschema/jsonschema.json` |
| JSON-LD Context | `resources/gens/jsonldcontext/context.jsonld` |
| SHACL Shapes (experimental) | `resources/gens/shacl/shapes.shacl.ttl` |
| OWL Ontologies (experimental) | `resources/gens/owl/` (`td.ttl`, `tm.ttl`, `hctl.ttl`, `wotsec.ttl`, `jsonschema.ttl`) |
| Class diagrams (experimental) | `resources/gens/visualization/*.svg` |
| Assertion CSV | `resources/gens/assertions/assertions.csv` |
| Merged LinkML schema | `resources/gens/linkml/linkml.yaml` |

Output paths and generators are configured in the project config file `wot-toolchain.yaml`: each generator listed under `generators` writes into `<output_dir>/<generator>/`; the spec HTML and assertions CSV paths come from `generators.spec.output` and `generators.spec.assertions_csv`.

### CLI

Commands and options: [CLI reference](docs/reference/cli.md); config file keys: [config file reference](docs/reference/config-file.md) (generate it with `uv run --group docs python scripts/gen_config_docs.py`). `--output-dir` does not move the spec HTML or the assertions CSV, and `--only` accepts only generators listed in the config file.

## Codebase Layout

```
resources/schemas/          ← SOURCE OF TRUTH
  thing_description.yaml    ← main TD schema; imports the others
  hypermedia.yaml           ← HCTL vocabulary
  wot_security.yaml         ← security vocabulary
  jsonschema.yaml           ← JSON Schema vocabulary
  thing_model.yaml          ← Thing Model vocabulary
  snippet_schema.yaml       ← schema of resources/snippets/_snippets.yaml
  README.md                 ← points to the docs pages to read before touching schemas

src/wot_toolchain/
  cli.py                    ← entry point: wot-toolchain generate-wot-resources | diff-report (see CLI above)
  config.py                 ← project config file loading and validation
  errors.py                 ← WotToolchainError and subclasses (config, schema, generation, external tool)
  pipeline.py               ← run_pipeline; the _gen_* artifact generators and their _DISPATCH table
  diff_report.py            ← JSON structural diff used by diff-report
  schema_utils.py           ← SchemaView loading and annotation helpers
  generators/               ← spec (respec.py) and class-diagram (visualization.py) generators
  artifacts/                ← adjust LinkML generator output to meet W3C WoT TD requirements
    passes.py               ← Pass, PassKind, run_passes
    jsonschema/ jsonld_context/ owl/ shacl/
                            ← per artifact: generator.py (LinkML generator subclass), options.py, passes, postprocess.py
  model/                    ← annotations.py, names.py, resolved.py
  schemas/                  ← config.yaml (LinkML schema of the project config file)
  serializers/              ← wot_turtle.py (Turtle output)
  templates/                ← Jinja templates for the spec HTML
  specgen/                  ← HTML spec generation
    respec.py / bikeshed_processor.py
    tables.py               ← vocabulary tables
    snippets.py             ← code example rendering
    assertions.py           ← assertion CSV output

resources/snippets/         ← TD/TM code examples shown in the spec
  *.json                    ← individual snippet files
  _snippets.yaml            ← snippet metadata (id, title, hide_paths, etc.)

resources/upstream/         ← W3C reference artifacts (schemas, contexts, ontologies, spec HTML, assertions.csv)

tests/
  data/                     ← TD instance files (valid + invalid), tested as TD 1.1 and as td-next
  snapshots/                ← machine-updatable snapshots of generated output
  known_failures/           ← strict expected-failure lists
  approved_divergences/     ← reviewed divergences from upstream text and snippets
```

## Setup

After cloning, run `uv sync` and `uv run pre-commit install`, and restore `resources/upstream/` — without it the config file does not load. Details, including the test prerequisites (jsonld.js, ROBOT), are in [Set up a checkout](docs/contributing/setup.md).

---

## The Postprocessor Pattern

See [Postprocessor Conventions](docs/contributing/postprocessors.md) for when and how to write a workaround for a LinkML limitation. See [LinkML gaps](docs/contributing/linkml-gaps.md) for documented generator limitations. See [OWL differences](docs/differences/owl.md) for the authoritative list of known differences between generated and target OWL ontologies — check it before investigating or reporting any OWL gap.

## Custom LinkML Annotations

See [WoT Custom Annotations](docs/reference/annotations.md) for the full annotation API, examples, and decision principles. See [LinkML Naming Conventions](docs/reference/naming-conventions.md) for schema structural rules, `inlined`/`identifier` patterns, and checklists.

## Testing and Quality


### Running Tests

```bash
# Full pipeline — verify it exits cleanly
uv run wot-toolchain generate-wot-resources 2>&1 | grep -E "ERROR|WARNING"

# All tests
uv run pytest tests/ -v

# Spec HTML structure tests
uv run pytest tests/test_spec_content_rendering.py tests/test_golden_form_structure.py -v

# Generated spec HTML vs the upstream reference (resources/upstream/html/index.html)
uv run pytest tests/test_spec_html_vs_golden.py -v

# Assertion inventory vs upstream
uv run pytest tests/test_assertion_inventory.py -v
```

### Known Failures and Generation Output

The expected-failure lists in `tests/known_failures/` are strict and can only shrink; see [Testing](docs/contributing/testing.md#expected-failures). Which `WARNING` and `ERROR` lines of `generate-wot-resources` are expected, and what to do about the others, is in [Checking a change](docs/editing-schemas/checking-a-change.md#read-the-generation-output). Generation aborts on any snippet validation error; fix it before declaring the change complete.

### Failure Policy

The only accepted failures are the strict entries in `tests/known_failures/`.
Any other generated-schema rejection of a valid sample, generated-versus-upstream
schema mismatch, or HTML-structure regression fails the relevant test directly.

**You are NOT allowed to ignore test failures.** Even if a failure appears pre-existing or unrelated to the current change, investigate it. Every failure must be understood and either fixed or escalated — never dismissed as "not from my change."

### Golden Files

Two categories with different update policies:

| Directory | Type | Update policy |
|---|---|---|
| `resources/upstream/` | W3C reference artifacts, hand-verified, authoritative | Require explicit maintainer approval in PR description; never auto-update |
| `tests/snapshots/` | Machine-updatable snapshots | Update via `--update-goldens` flag, only after explicit maintainer approval |

Snapshots, goldens and known-failure baselines (`tests/known_failures/`, `tests/approved_divergences/`) are never updated without explicit maintainer approval.

**When `tests/test_golden_diff.py` fails:**
1. Read the diff — is it expected from the schema change?
2. If expected: report the diff and get maintainer approval; then run `uv run pytest tests/test_golden_diff.py --update-goldens`, commit the updated snapshot, explain in PR description.
3. If unexpected: the change has a side-effect — investigate before updating.
4. `--update-goldens` only rewrites `tests/snapshots/`; files in `resources/upstream/` require human review.

### What "Correct" Means

A change is complete when all of these hold:

1. `uv run wot-toolchain generate-wot-resources` exits without ERROR.
2. `uv run pytest tests/ -v` passes (xfail acceptable, no new unexpected failures).
3. Snippets in `resources/snippets/` validate against the schemas in the config file's `generators.spec.snippet_validation_schemas` (currently `resources/upstream/schemas/td-next-json-schema-validation.json` and `tm-json-schema-validation.json`) — run `/validate-snippets`. Every `.json` linked to a changed class or slot must pass; `validate: false` is only acceptable for non-TD/TM examples.
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

When reviewing HTML changes, do not evaluate the entire document — scope the check to the `%`-replaced sections and any `spec_content` / `spec_intro_content` blocks that changed.

### CI Pipeline (GitHub Actions)

The jobs of `main.yaml` are described in [Testing](docs/contributing/testing.md#ci).

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
- See [Snippet Authoring Guide](docs/editing-schemas/snippets.md) for worked examples.

## General Project Conventions

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
| `resources/upstream/` | Authoritative reference outputs | Never update without maintainer sign-off; see Golden Files above |

**Branching strategy:**
- Fork the repo; branch from `main` (not from another contributor's branch).
- Keep branches focused — one logical change per PR.
- Before opening a PR, rebase on latest `main` and re-run generation to ensure clean output.

## Current Priorities (2026-11)

Everything in this section is **PLANNED and not yet implemented** unless stated otherwise.

1. **Generators as modules (PLANNED).** Current state: the artifact generators are private `_gen_*` functions in `src/wot_toolchain/pipeline.py`, registered in its `ARTIFACT_REGISTRY`; the `Artifact` enum in `artifacts/registry.py` defines the generator names that `config.py` accepts; `--only` filters the config file's `generators`; each generator writes to `<output_dir>/<name>/`. Planned: each generator becomes its own module under `src/wot_toolchain/generators/` with the contract `(project, sv, output_dir) -> None`, and one registry feeds both `--only` and the output directory mapping. This is a pure move: zero change in generated output.
2. **Consumer rollout (PLANNED), in this order:** this toolchain repository first; then a release tag; then a branch in `w3c/wot-thing-description` with the schemas under `linkml/`, its own config file and a preview workflow, opened as a side-by-side draft PR; then instance-based tests there.
3. Snapshots, goldens and known-failure baselines change only with explicit maintainer approval (current rule; see Golden Files).

Out of scope for now: automated ontology/SHACL consistency (the reference ontologies in `resources/upstream/ontology/` are used for reference only).

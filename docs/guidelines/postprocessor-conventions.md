# Postprocessor Conventions

**Author:** Mahda Noura (mahda.noura@siemens.com)
**Date:** 29.10.2026

---

Conventions for writing and maintaining postprocessors — the Python functions in [`src/wot_toolchain/artifacts/`](../../src/wot_toolchain/artifacts/) that transform raw LinkML generator output into spec-compliant artifacts.

For the catalog of known LinkML limitations that motivate postprocessors, see [Known LinkML Gaps](../known-linkml-gaps.md).

---

## 1. When to Write a Postprocessor

**Rule: exhaust native LinkML features first.**

Rationale: a postprocessor is maintenance burden. Native LinkML features are upstream-maintained, tested, and documented. A postprocessor is a workaround that must be removed when the upstream gap is closed.

Decision sequence:

1. Can LinkML express this natively? (`exactly_one_of`, `rules`, `minimum_value`, `inlined`, etc.) → Use native feature.
2. Is the gap already in [Known LinkML Gaps](../known-linkml-gaps.md) with an existing workaround? → Use the existing postprocessor path.
3. Neither? → Write a new postprocessor function **and** add the gap to `docs/known-linkml-gaps.md`.

**Rule: never write a postprocessor for something LinkML supports natively.**

If you suspect LinkML cannot express a requirement, verify by testing with the generator first. Assumptions about generator limitations are frequently wrong.

---

## 2. File Organization

**Rule: one postprocessor package per artifact type, with `postprocess.py` as its entry module.**

| Module | Artifact |
|--------|----------|
| `artifacts/jsonschema/postprocess.py` | JSON Schema |
| `artifacts/shacl/postprocess.py` | SHACL Shapes |

Most JSON Schema rules are not postprocessors: they are in the hooks of `WotJsonSchemaGenerator` (`artifacts/jsonschema/generator.py`), which overrides the upstream LinkML generator and states each rule while the schema is generated. Two post-steps remain in `postprocess.py`, because they need the finished set of defs.

| Module | Content |
|--------|---------|
| `generator.py` | `WotJsonSchemaGenerator` and its hooks (e.g. `get_subschema_for_slot`, `after_generate_class`, `after_generate_schema`) |
| `refs.py` | `resolve_refs`, called from `after_generate_class` |
| `annotations.py` | `TransformConfig` and `read_annotations` |
| `traversal.py` | `walk_schema` |
| `pruning.py` | `remove_excluded_defs`, `remove_unreferenced_candidate_defs` (the two post-steps) |
| `postprocess.py` | `JSONSCHEMA_TRANSFORMS` and the entry point |

**Rule: put a new JSON Schema rule in a generator hook. Add a post-step only when no hook can see what the rule needs.**

Rationale: a rule in a hook does not depend on the position in a list of passes. The generation pipeline calls one entry point per artifact for the post-steps that remain.

**Rule: each `postprocess.py` has one public entry point at the bottom.**

```python
def post_process_jsonschema(raw_schema: dict, schema_view: SchemaView, top_class: str | None = None) -> dict:
    schema = copy.deepcopy(raw_schema)
    config = read_annotations(schema_view)
    config.top_class = top_class
    run_transforms(JSONSCHEMA_TRANSFORMS, schema, schema_view, config)
    ...
    return schema
```

A new post-step is a function plus one `Transform` entry in the module's list (`JSONSCHEMA_TRANSFORMS`, `SHACL_TRANSFORMS`). The list order is the run order. Each entry has a `name`, a `kind` (`LINKML_BUG`, `LINKML_GAP`, `WOT_SHAPING`, `COSMETIC`) and a `reason` that says what the transform changes and why. A transform that needs another one to run first names it in `after`; a list that breaks this is rejected with a `GenerationError` before any transform runs. `Transform` and `run_transforms` are defined in `artifacts/transforms.py`; a transform that raises ends the run with a `GenerationError` that names it.

---

## 3. Naming Conventions

**Rule: transform functions and generator helper methods use `verb_noun` naming.**

The function name describes what the transform does, not the bug it fixes or the spec requirement it satisfies.

```python
remove_excluded_defs()         # good — describes the transformation
_state_oneof_dispatch()        # good
_fix_issue_47()                # wrong — names the ticket, not the action
_workaround_linkml_bug()       # wrong — too vague
```

---

## 4. Annotation-Driven Pattern

**Rule: prefer reading transform configuration from schema annotations over hardcoding class names.**

Rationale: annotation-driven rules decouple the Python code from specific schema content. Adding a new `jsonschema_flatten_subclasses` annotation to a class automatically triggers flattening without changing Python code.

```python
FLATTEN_SUBCLASSES = "jsonschema_flatten_subclasses"

@staticmethod
def _flattens_subclasses(class_name: str | None, sv: SchemaView) -> bool:
    return class_name is not None and bool(annotation_tag_value(sv.get_class(class_name), FLATTEN_SUBCLASSES))
```

**Anti-pattern:** hardcoding class names in the rule.

```python
# Wrong — breaks if the class is renamed or a second class needs flattening
def _flattens_subclasses(class_name):
    return class_name == "DataSchema"  # hardcoded
```

---

## 5. Documentation Requirements

**Rule: every postprocessor function must document (a) the W3C requirement it satisfies and (b) the LinkML gap that forces the workaround.**

Rationale: when the upstream gap is closed, maintainers need to know which postprocessor functions can be removed and which spec requirements they served.

A one-line docstring or comment is sufficient:

```python
def aliased_slot_name(self, slot: str | SlotDefinition) -> str:
    """Name a slot condition by the alias of the slot it constrains (docs/known-linkml-gaps.md #14)."""
```

**Rule: add a `TODO: remove when LinkML #NNNN is merged` comment when an upstream fix is expected.**

**Rule: add the gap to [Known LinkML Gaps](../known-linkml-gaps.md) with symptom, affected artifact, workaround, and issue link.**

---

## 6. Testing

**Rule: postprocessor output is validated through golden file comparison.**

The test suite (`tests/goldens/test_snapshots.py`) compares full generated output — including postprocessor transforms — against snapshots. After modifying a postprocessor:

1. Regenerate: `uv run wot-toolchain generate-wot-resources`
2. Review the diff in `resources/gens/`
3. Update goldens: `uv run pytest tests/goldens/test_snapshots.py --update-goldens`
4. Run full suite: `uv run pytest tests/ -v`

**Rule: the entry point function must be pure — `deepcopy` the input, return a new dict.**

Rationale: the pipeline may use the raw schema for other generators. Mutating the input causes cross-artifact contamination.

```python
def post_process_jsonschema(raw_schema: dict, schema_view: SchemaView) -> dict:
    schema = copy.deepcopy(raw_schema)  # always copy
    ...
    return schema
```

---

## 7. Anti-Patterns

- **Hardcoded class or slot names** — use annotations or `SchemaView` queries instead.
- **Editing `resources/gens/` directly** — postprocessors run in the pipeline, not as manual patches.
- **Postprocessor for a native LinkML feature** — if `exactly_one_of`, `rules`, or `minimum_value` can express it, use the native construct.
- **No `docs/known-linkml-gaps.md` entry** — every postprocessor must trace back to a documented gap. Undocumented workarounds accumulate silently and never get removed.
- **Mutating the input schema** — always `deepcopy` first.

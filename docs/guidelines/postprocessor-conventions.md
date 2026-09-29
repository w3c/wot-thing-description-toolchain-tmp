# Postprocessor Conventions

**Author:** Mahda Noura (mahda.noura@siemens.com)
**Date:** 29.10.2026

---

Conventions for writing and maintaining postprocessors — the Python functions in [`src/wotis/postprocessors/`](../../src/wotis/postprocessors/) that transform raw LinkML generator output into spec-compliant artifacts.

For the catalog of known LinkML limitations that motivate postprocessors, see [Known LinkML Gaps](../known-linkml-gaps.md).

---

## 1. When to Write a Postprocessor

**Rule: exhaust native LinkML features first.**

Rationale: a postprocessor is maintenance burden. Native LinkML features are upstream-maintained, tested, and documented. A postprocessor is a workaround that must be removed when the upstream gap is closed.

Decision sequence:

1. Can LinkML express this natively? (`exactly_one_of`, `rules`, `minimum_value`, `inlined`, etc.) → Use native feature.
2. Is the gap already in [Known LinkML Gaps](../known-linkml-gaps.md) with an existing workaround? → Use the existing postprocessor path.
3. Neither? → Write a new postprocessor function **and** add the gap to `KNOWN_LINKML_GAPS.md`.

**Rule: never write a postprocessor for something LinkML supports natively.**

If you suspect LinkML cannot express a requirement, verify by testing with the generator first. Assumptions about generator limitations are frequently wrong.

---

## 2. File Organization

**Rule: one postprocessor module per artifact type.**

| Module | Artifact |
|--------|----------|
| `jsonschema_postprocessor.py` | JSON Schema |
| `jsonld_context_postprocessor.py` | JSON-LD Context |
| `shacl_postprocessor.py` | SHACL Shapes |

**Rule: add new transform functions to the existing module. Do not create new files.**

Rationale: the generation pipeline calls one entry point per artifact. Splitting logic across files creates import complexity with no benefit.

**Rule: each module has one public entry point at the bottom.**

```python
def post_process_jsonschema(raw_schema: dict, schema_view: SchemaView) -> dict:
    schema = copy.deepcopy(raw_schema)
    config = _read_annotations(schema_view)
    _flatten_subclasses(schema, schema_view, config)
    _build_oneof_dispatch(schema, schema_view, config)
    # ... each transform in sequence ...
    return schema
```

New transforms are added as private functions and called from the entry point in the correct order.

---

## 3. Naming Conventions

**Rule: private transform functions use `_verb_noun` naming.**

The function name describes what the transform does, not the bug it fixes or the spec requirement it satisfies.

```python
_flatten_subclasses()          # good — describes the transformation
_build_oneof_dispatch()        # good
_fix_issue_47()                # wrong — names the ticket, not the action
_workaround_linkml_bug()       # wrong — too vague
```

**Rule: dataclass configs for annotation-driven transforms use `PascalCase` + `Config` suffix.**

```python
@dataclass
class OneOfDispatchConfig:
    class_name: str
    discriminator: str
    include_unknown: bool

@dataclass
class FormVariantsConfig:
    class_name: str
    op_slot: str
    variants: dict[str, list[str]]
```

---

## 4. Annotation-Driven Pattern

**Rule: prefer reading transform configuration from schema annotations over hardcoding class names.**

Rationale: annotation-driven transforms decouple postprocessor logic from specific schema content. Adding a new `jsonschema_flatten_subclasses` annotation to a class automatically triggers flattening without changing Python code.

```python
def _read_annotations(sv: SchemaView) -> TransformConfig:
    flatten_parents = []
    for cls in sv.all_classes():
        val = _get_annotation_value(cls, "jsonschema_flatten_subclasses")
        if val:
            flatten_parents.append(cls.name)
    # ... read other annotations ...
    return TransformConfig(flatten_subclass_parents=flatten_parents, ...)
```

**Anti-pattern:** hardcoding class names in the transform function.

```python
# Wrong — breaks if the class is renamed or a second class needs flattening
def _flatten_subclasses(schema):
    ds = schema["$defs"]["DataSchema"]  # hardcoded
    ...
```

---

## 5. Documentation Requirements

**Rule: every postprocessor function must document (a) the W3C requirement it satisfies and (b) the LinkML gap that forces the workaround.**

Rationale: when the upstream gap is closed, maintainers need to know which postprocessor functions can be removed and which spec requirements they served.

A one-line comment before the function is sufficient:

```python
# W3C TD spec requires flat DataSchema; LinkML generates separate subclass $defs (gap #3).
def _flatten_subclasses(schema: dict, sv: SchemaView, config: TransformConfig) -> None:
    ...
```

**Rule: add a `TODO: remove when LinkML #NNNN is merged` comment when an upstream fix is expected.**

**Rule: add the gap to [Known LinkML Gaps](../known-linkml-gaps.md) with symptom, affected artifact, workaround, and issue link.**

---

## 6. Testing

**Rule: postprocessor output is validated through golden file comparison.**

The test suite (`tests/test_golden_diff.py`) compares full generated output — including postprocessor transforms — against snapshots. After modifying a postprocessor:

1. Regenerate: `uv run wotis generate-wot-resources`
2. Review the diff in `resources/gens/`
3. Update goldens: `uv run pytest tests/test_golden_diff.py --update-goldens`
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
- **No `KNOWN_LINKML_GAPS.md` entry** — every postprocessor must trace back to a documented gap. Undocumented workarounds accumulate silently and never get removed.
- **Mutating the input schema** — always `deepcopy` first.

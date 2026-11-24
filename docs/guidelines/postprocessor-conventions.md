# Postprocessor Conventions

Conventions for the code in [`src/wot_toolchain/artifacts/`](https://github.com/w3c/wot-thing-description-toolchain-tmp/tree/main/src/wot_toolchain/artifacts) that adjusts the output of the LinkML generators until it meets the WoT Thing Description requirements.

[LinkML gaps](../linkml-gaps.md) lists the LinkML limitations that this code works around.

## 1. When to write a workaround

**Rule: use a native LinkML feature when one exists.**

A workaround is code this project must maintain and must remove when LinkML closes the gap.

1. LinkML can express the requirement (`exactly_one_of`, `rules`, `minimum_value`, `inlined`, ...): use the native feature.
2. [LinkML gaps](../linkml-gaps.md) already describes the gap and its workaround: extend that workaround.
3. Otherwise: write a new workaround and describe the gap in [LinkML gaps](../linkml-gaps.md).

Before you conclude that LinkML cannot express a requirement, run the generator on a small schema and inspect its output.

## 2. Where a workaround lives

**Rule: a workaround has one home. Choose the first that applies.**

1. **Schema.** The fact is modeling (a type, a cardinality, an enumeration, a description). Fix it in `resources/schemas/`.
2. **Generator subclass.** The LinkML generator emits the wrong thing and offers a method to override. Fix it where the output is emitted.
3. **Pass.** The generated artifact needs a transformation that the generator cannot produce. See [§4](#4-passes).
4. **Serializer.** Ordering and formatting only.

## 3. File organization

One package per artifact:

| Package | Artifact |
|---------|----------|
| `artifacts/jsonschema/` | JSON Schema |
| `artifacts/jsonld_context/` | JSON-LD context |
| `artifacts/owl/` | OWL ontologies |
| `artifacts/shacl/` | SHACL shapes |

Each package has the same parts:

| Part | Content |
|------|---------|
| `generator.py` | Subclass of the LinkML generator: `WotJsonSchemaGenerator`, `WotContextGenerator`, `WotOwlGenerator`, `WotShaclGenerator` |
| `options.py` | Typed options of that subclass |
| Pass tuple | The ordered passes of the artifact (table below) |
| `postprocess.py` | Entry point that runs the passes |

| Artifact | Pass tuple | Entry point |
|----------|------------|-------------|
| JSON Schema | `JSONSCHEMA_PASSES` in `jsonschema/postprocess.py` | `post_process_jsonschema` |
| JSON-LD context | `PRE_SCOPING_PASSES`, `POST_SCOPING_PASSES` in `jsonld_context/passes.py` | `post_process_jsonld_context` |
| OWL | `OWL_PRE_PASSES` in `owl/pre_passes.py` (before generation) | `preprocess_for_gen_owl` |
| OWL | `OWL_PASSES` in `owl/passes.py` (after generation) | `postprocess_owl` |
| SHACL | `SHACL_PASSES` in `shacl/passes.py` | `post_process_shacl` |

## 4. Passes

[`artifacts/passes.py`](https://github.com/w3c/wot-thing-description-toolchain-tmp/blob/main/src/wot_toolchain/artifacts/passes.py) defines the contract:

```python
class PassKind(StrEnum):
    UPSTREAM_BUG = auto()
    UPSTREAM_GAP = auto()
    WOT_SHAPING = auto()
    COSMETIC = auto()


@dataclass(frozen=True, slots=True)
class Pass:
    name: str
    kind: PassKind
    reason: str
    apply: Callable[..., None]
```

| Kind | Use it when |
|------|-------------|
| `UPSTREAM_BUG` | The LinkML generator emits incorrect output. |
| `UPSTREAM_GAP` | LinkML has no way to express the requirement. |
| `WOT_SHAPING` | The output is correct LinkML output but the TD specification requires a different form. |
| `COSMETIC` | The change removes or tidies content without changing what the artifact means. |

- A pass changes the artifact in place and returns nothing.
- `reason` states why the pass is needed. A blank `name` or `reason` raises `ValueError`.
- `run_passes(passes, *args)` applies the passes in tuple order and passes `*args` to each one.

**Rule: add a pass to the tuple of its artifact, at the position where its input is ready.**

**Rule: when a pass depends on the position of another pass, pin the order in a test.** The tests `tests/test_artifacts_<artifact>_passes.py` assert the order of each tuple.

**Failure policy:**

- A pass that cannot do its job raises a `WotToolchainError` subclass (`GenerationError`, `SchemaError`) with a message that names the problem. `run_passes` re-raises it unchanged.
- `run_passes` wraps any other exception in a `GenerationError` that names the pass.
- A pass that finds nothing to change returns without error.

## 5. Naming

**Rule: name a pass and its function after the transformation, in `verb_noun` form.**

```python
flatten_subclasses       # good: describes the transformation
build_oneof_dispatch     # good
fix_issue_47             # wrong: names the ticket
workaround_linkml_bug    # wrong: says nothing about the transformation
```

## 6. Annotation-driven passes

**Rule: read class and slot names from schema annotations or from `SchemaView`. Do not write them into a pass.**

A pass with a class name written into it breaks when the class is renamed and cannot serve a second class.

The JSON Schema passes are configured by five schema annotations: `jsonschema_flatten_subclasses`, `jsonschema_oneof_dispatch`, `jsonschema_enum_subset_partition`, `jsonschema_form_subset` and `jsonschema_exclude`. `read_annotations` in [`artifacts/jsonschema/annotations.py`](https://github.com/w3c/wot-thing-description-toolchain-tmp/blob/main/src/wot_toolchain/artifacts/jsonschema/annotations.py) reads them into a `TransformConfig`, which every JSON Schema pass receives. [WoT custom annotations](../reference/wot-custom-annotations.md) describes each annotation.

## 7. Documentation

**Rule: the `reason` of a pass states the TD requirement it serves or the LinkML limitation that forces it.**

**Rule: describe every LinkML limitation in [LinkML gaps](../linkml-gaps.md),** with the symptom and the workaround, in the section of the affected artifact.

## 8. Testing

**Rule: a change to a generator subclass or a pass is checked against the golden files.**

`tests/test_golden_diff.py` compares the generated artifacts in `resources/gens/` with the snapshots in `tests/snapshots/`.

1. Regenerate: `uv run wot-toolchain generate-wot-resources`
2. Run the suite: `uv run pytest`
3. If a golden test fails, review the difference. Update the snapshots only when the new output is the intended output: `uv run pytest tests/test_golden_diff.py --update-goldens`

**Rule: a workaround for a defect in LinkML gets a canary test.** A canary in `tests/test_upstream_canaries.py` asserts the defective LinkML behaviour. It fails when LinkML changes that behaviour, which is the signal to remove the workaround. Name the canary in the [LinkML gaps](../linkml-gaps.md) entry.

**Rule: `post_process_jsonschema` does not modify its input.** It copies the raw schema and returns the copy.

## 9. Anti-patterns

- **A class or slot name written into a pass.** Use annotations or `SchemaView` queries.
- **A pass for something LinkML expresses natively.**
- **A modeling fix in a pass.** Fix the schema.
- **A workaround without an entry in [LinkML gaps](../linkml-gaps.md).**

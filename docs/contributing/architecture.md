# Architecture

How a run of `wot-toolchain generate-wot-resources` turns a config file and LinkML schemas into artifacts. Module paths are relative to `src/wot_toolchain/`.

```
wot-toolchain.yaml ──► config.py ──► Project
                                       │
resources/schemas/*.yaml ──► model/resolved.py ──► merged SchemaView (annotations validated)
                                       │
                         pipeline.py: run_pipeline
                                       │
      ┌──────────────┬─────────────────┼────────────────┬──────────┬──────────────┐
  jsonschema     jsonldcontext        shacl             owl      linkml     visualization
      │              │                 │                 │          │              │
  LinkML generator subclass (artifacts/<artifact>/generator.py)     │   generators/visualization.py
      │              │                 │                 │          │
  passes (artifacts/<artifact>/passes.py, postprocess.py)          LinkmlGenerator
      │              │                 │                 │
      ▼              ▼                 ▼          serializers/wot_turtle.py
  <output_dir>/<generator>/ ...                          ▼
                                                  <output_dir>/owl/*.ttl

  spec (last) ──► generators/respec.py ──► specgen/ (tables, snippets, Bikeshed, assertions) ──► index.html, assertions.csv
```

## 1. Load the project

`cli.py` parses the options and calls `config.load_project`. It validates the project's config file (`wot-toolchain.yaml`) against the config schema `schemas/config.yaml`, a LinkML schema shipped with the package that defines the config format, and returns a `Project` with absolute paths. `--input_schema`, `--output-dir` and `--only` replace fields of that `Project`. The keys are described in the [config file reference](../reference/config-file.md).

## 2. Resolve the schemas

`run_pipeline` in `pipeline.py` first checks for the external programs the run needs (Bikeshed for `spec`, Graphviz `dot` for diagrams), so a missing program fails before anything is written. `model/resolved.py` then loads the root schema with its imports into one merged `SchemaView` and checks the custom annotations (`model/annotations.py`). Every generator reads that view.

## 3. Generate each artifact

`ARTIFACT_REGISTRY` in `pipeline.py` maps each generator name of `artifacts/registry.py` to a `_gen_*` function with the contract `(project, schema_view, output_dir) -> None`. The listed generators run in the order of the `Artifact` enum (`jsonschema`, `shacl`, `jsonldcontext`, `owl`, `linkml`, `visualization`), whatever their order in the config file, and each writes into `<output_dir>/<generator>/`.

The four RDF and JSON artifacts share one layout, one package each under `artifacts/`:

| File | Role |
|---|---|
| `generator.py` | Subclass of the LinkML generator. Fixes output where the generator offers a method to override. |
| `options.py` | The options the pipeline passes to that generator. |
| `passes.py` | Ordered `Pass` objects (`artifacts/passes.py`): a name, a `PassKind` (`UPSTREAM_BUG`, `UPSTREAM_GAP`, `WOT_SHAPING`, `COSMETIC`) and a reason. |
| `postprocess.py` | Runs the passes on the generated artifact. |

OWL also has `preprocess.py` and `pre_passes.py`, which adjust the schema before `gen-owl` reads it, and writes Turtle with the serializer in `serializers/wot_turtle.py`. Where a workaround belongs, and how a pass is written, is described in [Postprocessors](postprocessors.md).

`linkml` writes the merged schema with LinkML's own generator. `visualization` draws one class diagram per vocabulary with Graphviz (`generators/visualization.py`).

## 4. Build the specification

`spec` runs after the others, because its snippet validation can use a JSON Schema generated in the same run. `generators/respec.py` fills the `%section()%` markers of the HTML template with vocabulary tables (`specgen/tables.py`, Jinja templates in `templates/`) and the `%snippet()%` markers with rendered examples (`specgen/snippets.py`), resolves glossary links with Bikeshed (`specgen/bikeshed_processor.py`) and writes the assertion CSV (`specgen/assertions.py`). The `spec_*` annotations that drive it are in [Specification annotations](../reference/annotations-spec.md).

## Errors

Every expected failure raises a subclass of `WotToolchainError` from `errors.py`: `ConfigError`, `SchemaError`, `GenerationError` or `ExternalToolError`. `cli.py` logs it as one `ERROR` line and exits with status 1.

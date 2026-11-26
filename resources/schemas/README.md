# WoT LinkML Schemas

The LinkML schemas in this directory are the single source of truth for all generated WoT artifacts.

`profiles/` holds schemas that import a vocabulary schema and narrow it for one generator only, such as `profiles/td_jsonschema.yaml` for the JSON Schema (`generators.jsonschema.schema` in `wot-toolchain.yaml`).

For schema authoring rules, see the [modeling guidelines](../../docs/guidelines/index.md):

- [LinkML Naming Conventions](../../docs/reference/linkml-naming-conventions.md) — class/slot naming, URIs, `slot_usage`, `inlined`, `identifier`, checklists
- [WoT Custom Annotations](../../docs/reference/wot-custom-annotations.md) — `spec_*`, `jsonschema_*` and `jsonld_*` annotations, native LinkML features
- [Postprocessor Conventions](../../docs/guidelines/postprocessor-conventions.md) — writing and maintaining postprocessors
- [LinkML gaps](../../docs/known-linkml-gaps.md) — confirmed generator limitations and workarounds

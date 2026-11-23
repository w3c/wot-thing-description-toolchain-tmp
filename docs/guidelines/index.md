# WoT Toolchain Guidelines

Guidelines for authoring and maintaining the WoT Thing Description Toolchain.

## Guidelines

| Guide | Description |
|-------|-------------|
| [LinkML Naming Conventions](../reference/linkml-naming-conventions.md) | Class/slot naming, URIs, `slot_usage`, `inlined`, `identifier`, checklists |
| [WoT Custom Annotations](../reference/wot-custom-annotations.md) | `spec_*`, `jsonschema_*` and `jsonld_*` annotations, native LinkML features, decision principle |
| [Custom Annotation Audit](../maintainers/custom-annotation-audit.md) | Classification of every non-`spec_*` annotation and removal criteria |
| [JSON-LD Context Composition](../maintainers/jsonld-context-composition.md) | Context-generation inputs, scoped-vocabulary inference, and RDF expansion contract |
| [Postprocessor Conventions](postprocessor-conventions.md) | Writing and maintaining Python postprocessors for each artifact type |
| [Snippet Authoring](snippet-authoring.md) | JSON snippet creation, metadata, path notation, groups, validation |
| [OWL Enum Modeling](owl-enum-modeling.md) | How LinkML enums appear in the generated OWL ontologies |
| [OWL/RDF Modeling](../maintainers/owl-rdf-modeling.md) | OWL property types, slot-to-IRI mapping, domain declarations, annotation workarounds |

## Supplementary Documents

| Document | Description |
|----------|-------------|
| [LinkML gaps](../linkml-gaps.md) | Catalog of confirmed generator limitations and workarounds |

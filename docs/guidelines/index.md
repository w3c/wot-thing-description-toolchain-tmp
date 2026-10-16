# WoT Toolchain Guidelines

**Author:** Mahda Noura (mahda.noura@siemens.com)
**Date:** 29.10.2026

---

Guidelines for authoring and maintaining the WoT Thing Description Toolchain.

## Guidelines

| Guide | Description |
|-------|-------------|
| [LinkML Naming Conventions](linkml-naming-conventions.md) | Class/slot naming, URIs, `slot_usage`, `inlined`, `identifier`, checklists |
| [WoT Custom Annotations](wot-custom-annotations.md) | `spec_*` and `jsonschema_*` annotations, native LinkML features, decision principle |
| [Custom Annotation Audit](custom-annotation-audit.md) | Classification of every non-`spec_*` annotation and removal criteria |
| [JSON-LD Context Composition](jsonld-context-composition.md) | Context-generation inputs, scoped-vocabulary inference, and RDF expansion contract |
| [Postprocessor Conventions](postprocessor-conventions.md) | Writing and maintaining Python postprocessors for each artifact type |
| [Snippet Authoring](snippet-authoring.md) | JSON snippet creation, metadata, path notation, groups, validation |
| [OWL/RDF Modeling](owl-rdf-modeling.md) | OWL property types, slot-to-IRI mapping, domain declarations, annotation workarounds |

## Supplementary Documents

| Document | Description |
|----------|-------------|
| [Known LinkML Gaps](../known-linkml-gaps.md) | Catalog of confirmed generator limitations and workarounds |

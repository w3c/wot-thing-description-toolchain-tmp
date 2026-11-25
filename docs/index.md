# WoT Toolchain

The WoT Toolchain generates Web of Things (WoT) resources from LinkML schema modules: the JSON Schema, the JSON-LD context, SHACL shapes, OWL ontologies, class-hierarchy diagrams, and the ReSpec Thing Description specification with its assertion inventory.

The JSON Schema, the JSON-LD context and the specification with its assertion inventory are the release targets. The OWL, SHACL and diagram outputs are experimental: they are generated and covered by snapshot and structural tests, but not yet checked for consistency in CI.

The toolchain is a command-line tool. A repository that owns LinkML schemas installs it and runs it to generate these files; the first such repository is meant to be [`w3c/wot-thing-description`](https://github.com/w3c/wot-thing-description).

## Where to start

The navigation bar groups these pages by reader. Pick the section that matches what you want to do.

### Getting started

For anyone who wants to run the toolchain. [Getting started](getting-started.md) is one page: install the toolchain, write a config file for your own LinkML schemas, and run it.

### Editing schemas

For people working in the Thing Description repository who write or change its LinkML schema files, run the toolchain and check what it generates.

- [Your first schema change](editing-schemas/first-change.md): what the toolchain produces, how the files fit together, and a worked example that adds a property to the Thing Description.
- [Schema changes](editing-schemas/schema-changes.md): variations on the worked example: required and multivalued properties, default values, enumerations, class ranges, new classes, new schema files and snippets.
- [Snippets](editing-schemas/snippets.md): writing the TD and TM JSON examples shown in the generated specification.
- [OWL ontologies](editing-schemas/owl.md): how to write a schema so its OWL ontology comes out right.
- [Checking a change](editing-schemas/checking-a-change.md): reading the generation output, comparing it with the previous output, and reviewing the specification.

### Reference

For looking things up while you work.

- [CLI](reference/cli.md): commands and options of `wot-toolchain`.
- [Config file](reference/config-file.md): every key of `wot-toolchain.yaml`.
- [Annotations](reference/annotations.md): the custom annotations the toolchain adds to LinkML, and when to use each one.
- [Specification annotations](reference/annotations-spec.md): the `spec_*` annotations that control how classes and slots appear in the generated specification.
- [Naming conventions](reference/naming-conventions.md): how to name and structure classes, slots and enumerations in the schemas.
- [LinkML cheatsheet](reference/linkml-cheatsheet.md): the LinkML features the schemas use.
- [Glossary](reference/glossary.md): words these pages use with a meaning of their own.

### Differences from TD 1.1

For people who review the generated artifacts. [Differences from TD 1.1](differences/index.md) records how each generated artifact differs from the one published with TD 1.1, and the defects found in the published ones, with pages for [JSON Schema](differences/json-schema.md), [JSON-LD context](differences/jsonld-context.md), [OWL](differences/owl.md) and [SHACL](differences/shacl.md).

### Contribute to the tool

For people who work on this repository: the Python code, the tests and these pages.

- [Set up a checkout](contributing/setup.md): clone, install, restore the reference files, generate and test.
- [Architecture](contributing/architecture.md): how a run turns a config file and schemas into artifacts.
- [Postprocessors](contributing/postprocessors.md): when and how to adjust the output of the LinkML generators.
- [JSON-LD context](contributing/jsonld-context.md): how the JSON-LD context is composed.
- [Testing](contributing/testing.md): the test suite, snapshots, expected failures, and CI.
- [LinkML gaps](contributing/linkml-gaps.md): where the LinkML generators fall short, and what the toolchain does about it.
- [LinkML issue drafts](contributing/linkml-issue-drafts.md): issues not yet filed with LinkML.

## Generated artifacts

A preview of the generated specification and artifacts is published with this site under [gens/](/wot-thing-description-toolchain-tmp/gens/). It is temporary: the artifacts are meant to be published from the repository that owns the schemas.

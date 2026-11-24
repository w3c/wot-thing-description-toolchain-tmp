# WoT Toolchain

The WoT Toolchain generates Web of Things (WoT) resources from LinkML schema modules: the JSON Schema, the JSON-LD context, SHACL shapes, OWL ontologies, class-hierarchy diagrams, and the ReSpec Thing Description specification with its assertion inventory.

The JSON Schema, the JSON-LD context and the specification with its assertion inventory are the release targets. The OWL, SHACL and diagram outputs are experimental: they are generated and covered by snapshot and structural tests, but not yet checked for consistency in CI.

To install and run it, see [Install](getting-started/install.md).

## Where to start

| If you want to | Read |
|---|---|
| Install and run the toolchain | [Install](getting-started/install.md), [CLI](reference/cli.md) |
| Use it for your own schemas | [Use from another repository](getting-started/using-from-another-repo.md), [Config file](reference/config-file.md) |
| Change the td-next vocabulary | [Your first schema change](getting-started/first-change.md), then [Schema changes](authoring/schema-changes.md), [Snippets](authoring/snippets.md) and [Checking a change](authoring/checking-a-change.md) |
| Look up an annotation, naming rule or term | [Annotations](reference/annotations.md), [Naming conventions](reference/naming-conventions.md), [LinkML cheatsheet](reference/linkml-cheatsheet.md), [Glossary](reference/glossary.md) |
| Work on the Python code | [Architecture](internals/architecture.md), [Postprocessors](internals/postprocessors.md), [Testing](internals/testing.md) |
| Understand how an artifact is composed | [JSON-LD context](internals/jsonld-context.md), [OWL](internals/owl.md) |
| Check how the output differs from TD 1.1 | [Differences from TD 1.1](status/differences/index.md) |
| See what LinkML cannot express yet | [LinkML gaps](status/linkml-gaps.md), [LinkML issue drafts](status/linkml-issue-drafts.md) |

## Generated artifacts

A preview of the generated specification and artifacts is published with this site under [gens/](/wot-thing-description-toolchain-tmp/gens/). It is temporary: the artifacts are meant to be published from the repository that owns the schemas.

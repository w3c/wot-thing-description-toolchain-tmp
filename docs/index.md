# WoT Toolchain

---

The WoT Toolchain generates Web of Things (WoT) resources from LinkML schema modules: the JSON Schema, the JSON-LD context, SHACL shapes, OWL ontologies, class-hierarchy diagrams, and the ReSpec Thing Description specification with its assertion inventory. These pages are for contributors who author the schemas or maintain the toolchain.

> This work area is in progress. The toolchain is intended to be integrated into the official [TD](https://github.com/w3c/wot-thing-description/) repository after review and Working Group consensus.

## Getting started

Requirements: Python 3.14, [uv](https://docs.astral.sh/uv/), and [Graphviz](https://graphviz.org/) for the class-hierarchy diagrams.

```bash
git clone https://github.com/w3c/wot-thing-description-toolchain-tmp.git
cd wot-thing-description-toolchain-tmp
uv sync --locked
uv run wot-toolchain generate-wot-resources
uv run pytest tests/ -v
```

The project config file `wot-toolchain.yaml` lists the generators to run, the schemas they read and the files they write. Run `uv run wot-toolchain generate-wot-resources --help` for all options. The [README](https://github.com/w3c/wot-thing-description-toolchain-tmp#readme) covers installing a tagged release in another repository.

## Where to start

| If you want to                           | Read                                                                                                                                                                                    |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Change the td-next vocabulary            | [Authoring td-next with LinkML](authoring-guide.md)                                                                                                                                     |
| Follow the schema and code conventions   | [Guidelines](guidelines/index.md)                                                                                                                                                       |
| Look up an annotation or naming rule     | [WoT Custom Annotations](reference/wot-custom-annotations.md), [LinkML Naming Conventions](reference/linkml-naming-conventions.md), [LinkML Cheatsheet](reference/linkml-cheatsheet.md) |
| Understand how an artifact is composed   | [Maintainers](maintainers/jsonld-context-composition.md)                                                                                                                                |
| Check how the output differs from TD 1.1 | [Differences](differences/README.md)                                                                                                                                                    |
| See what LinkML cannot express yet       | [LinkML gaps](linkml-gaps.md), [Upstream issues](upstream-issues/README.md)                                                                                                             |

## Generated artifacts

A preview of the generated specification and artifacts is published with this site under [gens/](/wot-thing-description-toolchain-tmp/gens/). It is temporary: the artifacts are meant to be published from the repository that owns the schemas.

## Previewing these pages

```bash
uv run --group docs zensical serve
```

This serves the site at <http://127.0.0.1:8000/> and rebuilds on every change under `docs/`.

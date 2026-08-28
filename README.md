# WoTIS - Web of Things Integrated Schemas

WoTIS - work in progress!

The aim of this repository is to simplify the current tooling required for generating the WoT Thing Description (TD) specification and related resources.
WoTIS toolchain is a python-based project designed to automate the generation of:
 1) WoT resources: [SHACL Shapes](https://www.w3.org/TR/shacl/), [JSON Schema](https://json-schema.org/specification), [JSON-LD context](https://www.w3.org/TR/json-ld11/), [RDF](https://www.w3.org/TR/rdf11-concepts/), and Mermaid diagrams
 2) Documentation: TD specification and ontology specifications

This project leverages [LinkML](https://linkml.io/linkml/) for modelling the [Web of Things Thing Description](https://www.w3.org/TR/wot-thing-description11/) information model.

## Process Overview

Below is a simplified overview of the process:

Step 1: Generate WoT resources using WoTIS

Step 2: Generate the final WoT TD specification document using the generated WoT resources along with a static `index.html`

<img title="WoT Toolchain Overview" src="images/toolchain.svg">

## Prerequisites

- Python 3.14. [Download and install Python](https://www.python.org/downloads/).
- The [uv](https://docs.astral.sh/uv/) package manager.
- [Graphviz](https://graphviz.org/download/) — the `dot` command must be on your PATH. Required for generating class-hierarchy diagrams.

## Quick Start

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/w3c/wot-thing-description-toolchain-tmp.git
cd wot-thing-description-toolchain-tmp
uv sync
pre-commit install
```

`pre-commit install` activates commit hooks (ruff linting, LinkML schema lint). If `pre-commit` is not installed: `pip install pre-commit` or `uv tool install pre-commit`.

Install the package or run it by executing:

```bash
uv run wotis
```

## Usage

See the list of all WoTIS commands:

```bash
wotis --help
```

Generate WoT resources (RDF, JSON-LD Context, SHACL Shapes, and JSON Schema) from a default LinkML schema:

```
wotis generate-wot-resources [OPTIONS]

Options:
  -i, --input_schema TEXT  Path to the input schema specified as LinkML yaml.
                           [default: resources/schemas/thing_description.yaml]
  -d, --generate_docs      Boolean for generating the final TD Respec-based
                           HTML specification.
  --assertions-csv FILE    Path for the storing assertion inventory CSV.
                           [default: resources/gens/assertions.csv]
  --extra-asserts FILE     Path to extra-asserts.html with additional testing
                           assertions to merge into the assertion inventory.
  --help                   Show this message and exit.
```

### Examples

Generate all standard WoT resources (JSON-LD, JSON Schema, etc.) using the default schema:

```bash
wotis generate-wot-resources
```

Generate the custom W3C-style TD specification:

```bash
wotis generate-wot-resources -d
```

## Validation

The tests check the generated artifacts. Generate them first, then run pytest:

```bash
uv run wotis generate-wot-resources -d
uv run pytest tests/ -v
```

This validates Thing Description instances against the generated JSON Schema,
compares the verdicts with the W3C schemas, and compares the generated JSON
Schema, JSON-LD context and spec HTML with the reference files. See
[tests/README.md](tests/README.md) for what each test file checks.

## Project Structure

```
resources/
  schemas/                 # LinkML YAML schemas (inputs)
  index.template.html      # ReSpec template with static spec prose
  xref/glossary.yaml       # Term definitions for cross-references
  jinja_templates/         # Jinja2 templates for vocabulary tables
  gens/                    # Generated outputs (not committed)
src/wotis/
  cli.py                   # CLI entry point
  generators/              # Pipeline orchestration and all generators
    __init__.py             # run_pipeline + LinkML resource generators
    respec.py               # ReSpec specification generation
    visualization.py        # Graphviz diagram generation
  specgen/                 # Table rendering, assertions, Bikeshed processing
  postprocessors/          # JSON Schema, JSON-LD, SHACL postprocessing
  preprocessing/           # Schema preprocessing
tests/
```

## Default Paths

- LinkML schema: `resources/schemas/thing_description.yaml`
- Generated WoT resources: `resources/gens`
- Generated full LinkML schema: `resources/gens/linkml`

## Contributing

We welcome contributions! Please fork the repository, create a branch, and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

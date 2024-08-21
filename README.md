
# Temporary WoT TD Tooling

The aim of this repository is to simplify the current WoT TD tooling for generating the specification. WoT TD Tooling is a python project to automate the generation of
 1) WoT resources: [SHACL Shapes](https://www.w3.org/TR/shacl/), [JSON Schema](https://json-schema.org/specification), [JSON-LD context](https://www.w3.org/TR/json-ld11/), and [RDF](https://www.w3.org/TR/rdf11-concepts/)
 2) Documentation: TD specification and ontology specifications

Here is an overview of the process:

<img title="WoT Toolchain Overview" src="images/toolchain.svg">

This project leverages [LinkML](https://linkml.io/linkml/) for modelling the [Web of Things Thing Description](https://www.w3.org/TR/wot-thing-description11/) information model.

## Prerequisites

The [uv](https://docs.astral.sh/uv/) package manager.

## Quick Start
1. Clone the repository and navigate to the project directory:
```
git clone https://github.com/w3c/wot-thing-description-toolchain-tmp.git
cd wot-thing-description-toolchain-tmp
```
2. Run the script using `uv`
```
uv run main.py -h
```

## Usage
The main.py script supports various options:
```
uv run main.py [-h] [-l] [-s]

options:
  -h, --help            show this help message and exit
  -l, --local-docs      Boolean for local documentation generation.
  -s, --serve-docs      Boolean for serving the generated documentation.
```
## Examples
Generate resources using the default schema and configuration:
```
uv run main.py
```

Generate documentation locally and serve it:
`uv run main.py -l -s`

#### Default Paths
* LinkML schema: `resources/schemas/thing_description.yaml`
* Generated WoT resources: `resources/gens`
* Generated full LinkML schema: `resources/gens/linkml`

## Contribution Guidelines
We welcome contributions! Please fork the repository, create a branch, and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

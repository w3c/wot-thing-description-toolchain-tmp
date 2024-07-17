
# Temporary WoT TD Tooling

The aim of this repository is to simplify the current WoT TD tooling for generating the specification. WoT TD Tooling is a python project to automate the generation of
 1) WoT resources: [SHACL Shapes](https://www.w3.org/TR/shacl/), [JSON Schema](https://json-schema.org/specification), [JSON-LD context](https://www.w3.org/TR/json-ld11/), and [RDF](https://www.w3.org/TR/rdf11-concepts/)
 2) Documentation: TD specification and ontology specifications

Here is an overview of the process:

<img title="WoT Toolchain Overview" src="images/toolchain.svg">

This project leverages [LinkML](https://linkml.io/linkml/) for modelling the [Web of Things Thing Description](https://www.w3.org/TR/wot-thing-description11/) information model.

## Prerequisites

*  Python 3.11 or greater. [Download and install Python.](https://www.python.org/downloads/)
* The `poetry` dependency manager. [See the poetry installation documentation for more details.](https://python-poetry.org/docs/#installing-with-pipx)


## Quick Start
1. Clone the repository and navigate to the project directory:
```
git clone https://github.com/w3c/wot-thing-description-toolchain-tmp.git
cd wot-thing-description-toolchain-tmp
```
2. Prepare a clean environment
```
python -m venv .venv
. .venv/bin/activate
```

3. Install project dependencies with `poetry`:
```
poetry install
```

4. View all supported commands:
`python main.py -h`

## Usage
The main.py script supports various options:
```
main.py [-h] [-l] [-s]

options:
  -h, --help            show this help message and exit
  -l, --local-docs      Boolean for local documentation generation.
  -s, --serve-docs      Boolean for serving the generated documentation.
```
## Examples
Generate resources using the default schema and configuration:
```
python main.py
```

Generate documentation locally and serve it:
`python main.py -l -s`

#### Default Paths
* LinkML schema: `resources/schemas/thing_description.yaml`
* Generated WoT resources: `resources/gens`
* Generated full LinkML schema: `resources/gens/linkml`

## Contribution Guidelines
We welcome contributions! Please fork the repository, create a branch, and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

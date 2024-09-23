
# WoTIS - Web of Things Integrated Schemas

WoTIS - work in progress!

The aim of this repository is to simplify the current tooling required for generating the WoT Thing Description (TD) specification and related resources. 
WoTIS toolchain is a python-based project designed to automate the generation of
 1) WoT resources: [SHACL Shapes](https://www.w3.org/TR/shacl/), [JSON Schema](https://json-schema.org/specification), [JSON-LD context](https://www.w3.org/TR/json-ld11/), [RDF](https://www.w3.org/TR/rdf11-concepts/), and visual figures
 2) Documentation: TD specification and ontology specifications

This project leverages [LinkML](https://linkml.io/linkml/) for modelling the [Web of Things Thing Description](https://www.w3.org/TR/wot-thing-description11/) information model.

## Process Overview

Below is a simplified overview of the process:

Step 1: Generate WoT resources using WOTIS

Step 2: Generate the final WoT TD specification document using the generated WoT resources along with a static ```index.html```

<img title="WoT Toolchain Overview" src="images/toolchain.svg">

## Prerequisites
* Python 3.11 or greater. [Download and install Python.](https://www.python.org/downloads/)
* The [uv](https://docs.astral.sh/uv/) package manager.

## Quick Start
1. Clone the repository and navigate to the project directory:
```bash
git clone https://github.com/w3c/wot-thing-description-toolchain-tmp.git
cd wot-thing-description-toolchain-tmp
```
2. Install the package or run it using `uv run wotis`
```bash
uv install
```

## Usage
See the list of all WOTIS commands:
```bash
wotis --help
```

Generate WoT resources (RDF, JSON-LD Context, SHACL Shapes, and JSON Schema) from a default LinkML schema: 
```bash
wotis generate-wot-resources [-i] [-d] [-s] [--help]

options:
  -i, --input_schema       Path to the input schema specified as LinkML yaml.
                           [default: resources/schemas/thing_description.yaml]
                           
  -d, --generate_docs      Boolean for local documentation generation.
  -s, --serve_docs         Boolean for serving the generated documentation.
  --help                   Show this help message and exit.
```

## Examples
Generate documentation using the default schema locally and serve it:
```bash
wotis generate-wot-resources -d -s
```

#### Default Paths
* LinkML schema: `resources/schemas/thing_description.yaml`
* Generated WoT resources: `resources/gens`
* Generated full LinkML schema: `resources/gens/linkml`

## Contribution Guidelines
We welcome contributions! Please fork the repository, create a branch, and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

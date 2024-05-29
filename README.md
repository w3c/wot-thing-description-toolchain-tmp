
# Temporary WoT TD Tooling

The aim of this repository is to simplify the current WoT TD tooling for generating the specification. WoT TD Tooling is a python project to automate the generation of 
 1) WoT resources: SHACL Shapes, JSON Schema, JSON-LD context, and ontology files
 2) Documentation: TD specification and ontology specifications

This project leverages [LinkML](https://linkml.io/linkml/) for modelling the [Web of Things Thing Description](https://www.w3.org/TR/wot-thing-description11/) information model.

## Prerequisites

*  Python 3.9 or greater. [Download and install Python.](https://www.python.org/downloads/)
* The `poetry` dependency manager. [See the poetry installation documentation for more details.](https://python-poetry.org/docs/#installing-with-pipx)


## Quick Start
1. Clone the repository and navigate to the project directory:
```
git clone https://github.com/w3c/wot-thing-description-toolchain-tmp.git
cd /wot-thing-description-toolchain-tmp
```

2. Install project dependencies with `poetry`:
```
poetry install
```

3. View all supported commands:
`python main.py -h`

## Usage
The main.py script supports various options:
```
main.py [-h] [-y YAML] [-c CONFIG_FILE] [-l] [-s]

options:
  -h, --help            show this help message and exit
  -y YAML, --yaml YAML  Path to the LinkML schema formatted as a YAML file.
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        Path to YAML configuration for specifying the required generators.
  -l, --local-docs      Boolean for local documentation generation.
  -s, --serve-docs      Boolean for serving the generated documentation.
```
## Examples
Generate resources using the default schema and configuration:
```
python main.py
```

Specify a custom LinkML schema and configuration file:
```
python main.py -y /path/to/schema.yaml -c /path/to/config.yaml
```

Generate and serve documentation locally:
`python main.py -l -s`

#### Default Paths
LinkML schema: `/resources/thing_description_schema.yaml`
Config file: `/src/linkml/config.yaml`
Generated WoT resources: `/resources/gens`

## Contribution Guidelines
We welcome contributions! Please fork the repository, create a branch, and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

# Temporary WoT TD Tooling

The aim of this repository is to simplify the current WoT TD tooling for generating the specification. WoT TD Tooling is a python project to automate the generation of 
 1) WoT resources (SHACL Shapes, jsonschema, JSON-LD context, and ontology files)
 2) Documentation of specification (TD specification and ontology specification)

This project uses [LinkML](https://linkml.io/linkml/) for modelling the [Web of Things Thing Description](https://www.w3.org/TR/wot-thing-description11/) information model.
For more information on the current process of the WoT TD tooling please refer to the [WoT github repo](https://github.com/w3c/wot-thing-description/tree/main/toolchain).

## Prerequisites

[Make](https://www.gnu.org/software/make)
[Poetry](https://python-poetry.org)

## Quick Start

### 1. Install Dependencies

First, install the necessary dependencies using `poetry`:

```bash
make install

### 2. Generate WoT resources
```bash
make setup

Run the initial setup to generate project files and examples:
1. Ensure you have Make installed [Make](https://www.gnu.org/software/make)
* Install Python 3 (try to upgrade your version if the following steps do not work)
* Install [Poetry](https://python-poetry.org/)
* Run `poetry install` to install dependencies
* Run `make all` create all resources
* When ready, run `make test` to validate the LinkML schema, based on the test data found in `examples` folder
* 
## Repository Structure

* [examples/](examples/) - example data
* [project/](project/) - project files
* [src/](src/) - source files
  * [thing_description_schema](src/thing_description_schema)
    * [schema](src/thing_description_schema/schema) -- LinkML schema
    * [datamodel](src/thing_description_schema/datamodel) -- generated
      Python datamodel
* [tests/](tests/) - Python tests



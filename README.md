# Temporary WoT TD Tooling

This repository is a LinkML-based schema for modelling the [Web of Things Thing Description](https://www.w3.org/TR/wot-thing-description11/) information model.
The aim is simplify the current WoT specification generation process.
For more information please refer to the [WoT github repo](https://github.com/w3c/wot-thing-description/tree/main/toolchain).

## Repository Structure

* [examples/](examples/) - example data
* [project/](project/) - project files
* [src/](src/) - source files
  * [thing_description_schema](src/thing_description_schema)
    * [schema](src/thing_description_schema/schema) -- LinkML schema
    * [datamodel](src/thing_description_schema/datamodel) -- generated
      Python datamodel
* [tests/](tests/) - Python tests

## Developer Documentation

* Install [Make](https://www.gnu.org/software/make)
* Install Python 3
* Install [Poetry](https://python-poetry.org/)
* Run `poetry install` to install dependencies
* Run `make all` create all resources
* When ready, run `make test` to validate the LinkML schema, based on the test data found in `examples` folder

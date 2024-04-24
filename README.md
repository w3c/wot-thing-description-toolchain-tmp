<<<<<<< HEAD
# Temporary WoT TD Tooling

The thing-description-schema is a LinkML-based schema for modelling the [Web of Things Thing Description](https://www.w3.org/TR/wot-thing-description11/) information model.
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

<details>
Use the `make` command to generate project artefacts:

* `make test`: validate the LinkML schema on test instances
* `make all`: make everything
* `make deploy`: deploys site
</details>
>>>>>>> thing-description-schema/master

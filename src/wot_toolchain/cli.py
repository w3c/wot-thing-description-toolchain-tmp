"""Command line interface; reports each diagnosed failure with the exit code of its error class."""

import dataclasses
import logging
import sys
from pathlib import Path

import click

from .config import DEFAULT_CONFIG, Config, load_config
from .errors import SchemaError, WotToolchainError
from .generators import run_pipeline

UNEXPECTED_ERROR_EXIT_CODE = 1

config_option = click.option('-c', '--config', 'config_path',
                             type=click.Path(path_type=Path, dir_okay=False),
                             default=DEFAULT_CONFIG,
                             show_default=True,
                             help="YAML file that names the root schema, the output directory, the vocabularies "
                                  "and the generators to run. Paths in it are relative to its directory.")
input_option = click.option('-i', '--input_schema',
                            type=click.Path(path_type=Path, dir_okay=False),
                            default=None,
                            help="LinkML schema file to generate the artifacts from. "
                                 "Replaces root_schema of the config.")
assertions_csv_option = click.option('--assertions-csv',
                                     type=click.Path(path_type=Path, dir_okay=False),
                                     default=None,
                                     help="File to write the assertion inventory CSV to. Replaces "
                                          "generators.spec.assertions_csv of the config. "
                                          "Ignored when the config does not list spec.")
extra_asserts_option = click.option('--extra-asserts',
                                    type=click.Path(path_type=Path, dir_okay=False),
                                    default=None,
                                    help="HTML file listing assertions that are tested but are not in the specification. "
                                         "They are added to the assertion inventory CSV. Replaces "
                                         "generators.spec.extra_asserts of the config. "
                                         "Ignored when the config does not list spec.")


@click.group()
@click.option("-v", "--verbose", count=True,
              help="Log more. -v shows progress messages, -vv also shows debug messages.")
@click.option("-q", "--quiet", is_flag=True, help="Log errors only. Wins over -v.")
def main(verbose: int, quiet: bool) -> None:
    """Generate the W3C Web of Things Thing Description artifacts from LinkML schemas."""
    logger = logging.getLogger()
    if verbose >= 2:
        logger.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logger.setLevel(level=logging.INFO)
    else:
        logger.setLevel(level=logging.WARNING)
    if quiet:
        logger.setLevel(level=logging.ERROR)
    logger.info(f"Logger {logger.name} set to level {logger.level}")


@main.command()
@config_option
@input_option
@assertions_csv_option
@extra_asserts_option
def generate_wot_resources(config_path: Path, input_schema: Path | None,
                           assertions_csv: Path | None, extra_asserts: Path | None) -> None:
    """Run the generators listed under generators in the config.

    The generators are jsonschema, jsonldcontext, shacl, owl, linkml,
    visualization (diagrams) and spec (the specification index.html and the
    assertion inventory CSV). Files are written to output_dir of the config.

    \b
    Exit codes:
      0  success
      1  unexpected error
      2  wrong command line usage
      3  config file missing or invalid
      4  LinkML schema missing or invalid
      5  an artifact could not be generated
    """
    try:
        config = _with_overrides(load_config(config_path), input_schema, assertions_csv, extra_asserts)
        run_pipeline(config)
    except WotToolchainError as error:
        logging.error("%s", error)
        sys.exit(error.exit_code)
    except Exception as error:
        logging.error(f"An unexpected error occurred during resource generation: {error}", exc_info=True)
        sys.exit(UNEXPECTED_ERROR_EXIT_CODE)


def _with_overrides(config: Config, input_schema: Path | None, assertions_csv: Path | None,
                    extra_asserts: Path | None) -> Config:
    if input_schema is not None:
        if not input_schema.is_file():
            raise SchemaError(f"{input_schema}: LinkML schema file not found (--input_schema).")
        config = dataclasses.replace(config, root_schema=input_schema)
    spec = config.spec
    if spec is None:
        return config
    if assertions_csv is not None:
        spec = dataclasses.replace(spec, assertions_csv=assertions_csv)
    if extra_asserts is not None:
        spec = dataclasses.replace(spec, extra_asserts=extra_asserts)
    return dataclasses.replace(config, spec=spec)


if __name__ == "__main__":
    main()

import click
import logging
import yaml

from pathlib import Path

from src.wotis import YAML_SCHEMA_PATH, ASSERTION_PATH
from src.wotis.generators import run_pipeline


input_option = click.option('-i', '--input_schema',
                            type=str,
                            show_default=True,
                            help="Path to the input schema specified as LinkML yaml.",
                            default=YAML_SCHEMA_PATH)
docs_option = click.option('-d',
                             '--generate_docs',
                             type=bool,
                             is_flag=True,
                             default=False,
                             show_default=True,
                             help="Boolean for generating the final TD Respec-based HTML specification.")
assertions_csv_option = click.option('--assertions-csv',
                             type=click.Path(path_type=Path, dir_okay=False),
                             default=ASSERTION_PATH,
                             show_default=True,
                             help="Path for the storing assertion inventory CSV. "
                                  "Defaults to resources/gens/assertions.csv.")
extra_asserts_option = click.option('--extra-asserts',
                             type=click.Path(path_type=Path, dir_okay=False, exists=False),
                             default=None,
                             help="Path to extra-asserts.html with additional testing assertions "
                                  "to merge into the assertion inventory.")


@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet")
def main(verbose: int, quiet: bool):
    """CLI for WOTIS (Web of Things Integrated Schemas) toolchain.

    :param verbose: Verbosity while running.
    :param quiet: Boolean to be quiet or verbose.
    """
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
@input_option
@docs_option
@assertions_csv_option
@extra_asserts_option
def generate_wot_resources(input_schema: str, generate_docs: bool, assertions_csv: Path, extra_asserts: Path):
    """
    Generating WoT resources (RDF, JSON-LD Context, SHACL Shapes, and JSON Schema)
    and the final Respec specification from LinkML schemas.
    """
    input_path = Path(input_schema)
    if not input_path.exists():
        raise FileNotFoundError(f"Cannot find input LinkML schema file {input_schema}.")

    try:
        run_pipeline(
            input_path,
            generate_docs=generate_docs,
            assertions_csv_path=assertions_csv,
            extra_asserts_path=extra_asserts,
        )
    except yaml.YAMLError as e:
        logging.error(f"LinkML schema validation failed: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during resource generation: {e}", exc_info=True)


if __name__ == "__main__":
    main()

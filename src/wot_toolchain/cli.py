"""Command line interface of the toolchain; the only module that resolves paths against the working directory."""

from __future__ import annotations

import dataclasses
import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import click

from .config import Project, load_project
from .diff_report import markdown_report
from .errors import WotToolchainError
from .pipeline import run_pipeline

DEFAULT_MANIFEST = Path("wot-toolchain.yaml")

config_option = click.option(
    "-c",
    "--config",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_MANIFEST,
    show_default=True,
    help="Path to the project manifest, relative to the current directory.",
)
input_option = click.option(
    "-i",
    "--input_schema",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="LinkML schema to use instead of the manifest's main_schema.",
)
docs_option = click.option(
    "-d",
    "--generate_docs",
    is_flag=True,
    default=False,
    show_default=True,
    help="Also generate the specification described by the manifest's spec section.",
)
output_dir_option = click.option(
    "--output-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Directory for generated artifacts instead of the manifest's output_dir, relative to the current directory.",
)
only_option = click.option(
    "--only",
    multiple=True,
    metavar="GENERATOR",
    help="Run only this generator of the manifest's generators; repeat for several.",
)


@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet", is_flag=True)
def main(verbose: int, quiet: bool) -> None:
    """CLI of the W3C Web of Things specification toolchain.

    \u000c
    Args:
        verbose: Verbosity while running; repeat for more detail.
        quiet: Only report errors.
    """
    logging.basicConfig(format="%(levelname)s: %(message)s")
    logger = logging.getLogger()
    if verbose >= 2:
        logger.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logger.setLevel(level=logging.INFO)
    else:
        logger.setLevel(level=logging.WARNING)
    if quiet:
        logger.setLevel(level=logging.ERROR)
    logger.info("Logger %s set to level %s", logger.name, logger.level)


@main.command()
@config_option
@input_option
@docs_option
@output_dir_option
@only_option
def generate_wot_resources(
    config: Path, input_schema: Path | None, generate_docs: bool, output_dir: Path | None, only: tuple[str, ...]
) -> None:
    """Generate the artifacts and, optionally, the specification of the project described by a manifest.

    \u000c
    Args:
        config: Project manifest.
        input_schema: Optional replacement for the manifest's main schema.
        generate_docs: Also generate the specification.
        output_dir: Optional replacement for the manifest's output directory.
        only: Generators to run instead of all the manifest's generators.

    Raises:
        click.UsageError: ``only`` names a generator the manifest does not list.
    """
    with _exit_on_toolchain_error():
        project = load_project(config.resolve())
        if input_schema is not None:
            project = dataclasses.replace(project, main_schema=input_schema.resolve())
        if output_dir is not None:
            project = dataclasses.replace(project, output_dir=output_dir.resolve())
        if only:
            project = _select_generators(project, only)
        run_pipeline(project, generate_docs=generate_docs)


@main.command()
@click.argument("generated", type=click.Path(dir_okay=False, path_type=Path))
@click.argument("reference", type=click.Path(dir_okay=False, path_type=Path))
def diff_report(generated: Path, reference: Path) -> None:
    """Print a Markdown report of the JSON paths in which GENERATED differs from REFERENCE.

    Differences do not fail the command; append the output to $GITHUB_STEP_SUMMARY to publish it.

    \u000c
    Args:
        generated: JSON file produced by this toolchain.
        reference: JSON file to compare against, for example from another toolchain.
    """
    with _exit_on_toolchain_error():
        click.echo(markdown_report(generated, reference))


@contextmanager
def _exit_on_toolchain_error() -> Iterator[None]:
    try:
        yield
    except WotToolchainError as error:
        logging.error("%s", error)
        sys.exit(1)


def _select_generators(project: Project, only: tuple[str, ...]) -> Project:
    unlisted = [name for name in only if name not in project.generators]
    if unlisted:
        raise click.UsageError(
            f"--only: not a generator listed in {project.manifest_path}: {', '.join(map(repr, unlisted))}. "
            f"Use one of: {', '.join(project.generators)}."
        )
    return dataclasses.replace(project, generators=tuple(name for name in project.generators if name in only))


if __name__ == "__main__":
    main()

"""Errors the toolchain diagnoses, each with the exit code the CLI reports for it."""


class WotToolchainError(Exception):
    """Base class for all errors raised deliberately by wot_toolchain."""

    exit_code = 1


class ConfigError(WotToolchainError):
    """The config file is missing, unreadable or invalid."""

    exit_code = 3


class SchemaError(WotToolchainError):
    """A LinkML schema file is missing, unreadable or invalid."""

    exit_code = 4


class GenerationError(WotToolchainError):
    """An artifact could not be generated."""

    exit_code = 5

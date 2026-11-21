"""Exception hierarchy for wot_toolchain.

Every failure the toolchain can diagnose is raised as a ``WotToolchainError``
subclass. The CLI is the only place that turns these into exit codes.
"""

from __future__ import annotations


class WotToolchainError(Exception):
    """Base class for all errors raised deliberately by wot_toolchain."""


class ManifestError(WotToolchainError):
    """The project manifest is missing, unreadable or describes an invalid project."""


class SchemaError(WotToolchainError):
    """A LinkML schema file is missing, unreadable or invalid."""


class GenerationError(WotToolchainError):
    """An artifact could not be generated or failed its own validation."""


class ExternalToolError(WotToolchainError):
    """An external program (for example ``bikeshed``) is missing or failed."""

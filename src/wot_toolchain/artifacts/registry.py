"""Artifact names and the registry mapping each name to the function that generates it."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Type-only: config validates names from this module, so a runtime import would be circular.
    from linkml_runtime.utils.schemaview import SchemaView

    from wot_toolchain.config import Project


class Artifact(StrEnum):
    """An artifact the pipeline can generate; member order is the order shown to users."""

    JSONSCHEMA = "jsonschema"
    SHACL = "shacl"
    JSONLDCONTEXT = "jsonldcontext"
    OWL = "owl"
    LINKML = "linkml"
    VISUALIZATION = "visualization"


type ArtifactGenerator = Callable[[Project, SchemaView, Path], None]


def artifact_names() -> tuple[str, ...]:
    """Return the name of every artifact, in user-facing order."""
    return tuple(artifact.value for artifact in Artifact)


@dataclass(frozen=True, slots=True)
class ArtifactRegistry:
    """The generator function of every artifact, exactly one per name."""

    generators: Mapping[str, ArtifactGenerator]

    def __post_init__(self) -> None:
        """Reject a mapping whose names differ from the artifact names.

        Raises:
            ValueError: If an artifact has no generator or a generator has no artifact.
        """
        registered, known = set(self.generators), set(artifact_names())
        if missing := sorted(known - registered):
            raise ValueError(f"No generator registered for artifacts {missing}")
        if unknown := sorted(registered - known):
            raise ValueError(f"Generators registered for unknown artifacts {unknown}")

    def generator(self, name: str) -> ArtifactGenerator:
        """Return the generator of the artifact ``name``.

        Raises:
            KeyError: If ``name`` is not an artifact name.
        """
        return self.generators[name]

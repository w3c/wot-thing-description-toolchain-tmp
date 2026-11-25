"""Named changes applied in order to the raw LinkML output of one artifact."""

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum, auto

from ..errors import GenerationError, WotToolchainError

logger = logging.getLogger(__name__)


class TransformKind(StrEnum):
    """Why a transform exists."""

    LINKML_BUG = auto()
    LINKML_GAP = auto()
    WOT_SHAPING = auto()
    COSMETIC = auto()


@dataclass(frozen=True, slots=True)
class Transform:
    """One in-place change to an artifact, with the reason it is needed."""

    name: str
    kind: TransformKind
    reason: str
    apply: Callable[..., None]

    def __post_init__(self) -> None:
        """Reject a blank name or reason."""
        if not self.name.strip():
            raise ValueError("Transform name must not be blank")
        if not self.reason.strip():
            raise ValueError(f"Transform {self.name!r} reason must not be blank")


def run_transforms(transforms: Sequence[Transform], *args: object) -> None:
    """Apply each transform to ``args`` in order; a failure names the transform."""
    for transform in transforms:
        logger.debug("Running transform %s", transform.name)
        try:
            transform.apply(*args)
        except WotToolchainError:
            raise
        except Exception as exc:
            raise GenerationError(f"Transform {transform.name!r} failed: {exc!r}") from exc

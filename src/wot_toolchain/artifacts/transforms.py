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
    after: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Reject a blank name or reason."""
        if not self.name.strip():
            raise ValueError("Transform name must not be blank")
        if not self.reason.strip():
            raise ValueError(f"Transform {self.name!r} reason must not be blank")


def _require_declared_order(transforms: Sequence[Transform]) -> None:
    """Reject a list in which a transform does not come after every transform it names in ``after``."""
    earlier: set[str] = set()
    for transform in transforms:
        missing = [name for name in transform.after if name not in earlier]
        if missing:
            raise GenerationError(f"Transform {transform.name!r} must run after {missing}, which do not precede it")
        earlier.add(transform.name)


def run_transforms(transforms: Sequence[Transform], *args: object) -> None:
    """Apply each transform to ``args`` in its declared order; a failure names the transform."""
    _require_declared_order(transforms)
    for transform in transforms:
        logger.debug("Running transform %s", transform.name)
        try:
            transform.apply(*args)
        except WotToolchainError:
            raise
        except Exception as exc:
            raise GenerationError(f"Transform {transform.name!r} failed: {exc!r}") from exc

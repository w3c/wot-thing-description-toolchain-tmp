"""Named, classified post-processing passes applied in order to a generated artifact."""

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum, auto

from wot_toolchain.errors import GenerationError, WotToolchainError

logger = logging.getLogger(__name__)


class PassKind(StrEnum):
    """Why a pass exists."""

    UPSTREAM_BUG = auto()
    UPSTREAM_GAP = auto()
    WOT_SHAPING = auto()
    COSMETIC = auto()


@dataclass(frozen=True, slots=True)
class Pass:
    """One in-place transformation of an artifact, with the reason it is needed."""

    name: str
    kind: PassKind
    reason: str
    apply: Callable[..., None]

    def __post_init__(self) -> None:
        """Reject a blank name or reason.

        Raises:
            ValueError: If ``name`` or ``reason`` is empty or whitespace only.
        """
        if not self.name.strip():
            raise ValueError("Pass name must not be blank")
        if not self.reason.strip():
            raise ValueError(f"Pass {self.name!r} reason must not be blank")


def run_passes(passes: Sequence[Pass], *args: object) -> None:
    """Apply each pass to ``args`` in sequence order.

    Raises:
        WotToolchainError: Unchanged, if a pass raises one.
        GenerationError: If a pass raises any other exception; the original is the cause.
    """
    for p in passes:
        logger.debug("Running pass %s", p.name)
        try:
            p.apply(*args)
        except WotToolchainError:
            raise
        except Exception as exc:
            raise GenerationError(f"Pass {p.name!r} failed: {exc!r}") from exc

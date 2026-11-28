"""Test that a transform list runs in order and rejects a broken declared order."""

import pytest

from wot_toolchain.artifacts.transforms import Transform, TransformKind, run_transforms
from wot_toolchain.errors import GenerationError


def _recording(name: str, after: tuple[str, ...] = ()) -> Transform:
    return Transform(
        name=name,
        kind=TransformKind.COSMETIC,
        reason="Records its name.",
        apply=lambda log: log.append(name),
        after=after,
    )


def test_transforms_run_in_list_order() -> None:
    log: list[str] = []

    run_transforms((_recording("first"), _recording("second", after=("first",))), log)

    assert log == ["first", "second"]


def test_transform_before_one_it_must_follow_is_rejected_and_nothing_runs() -> None:
    log: list[str] = []

    with pytest.raises(GenerationError, match=r"'second' must run after \['first'\]"):
        run_transforms((_recording("second", after=("first",)), _recording("first")), log)

    assert log == []


def test_transform_that_must_follow_a_missing_one_is_rejected() -> None:
    log: list[str] = []

    with pytest.raises(GenerationError, match=r"'second' must run after \['first'\]"):
        run_transforms((_recording("second", after=("first",)),), log)

    assert log == []


def test_failing_transform_is_named_in_the_error() -> None:
    def fail(_log: list[str]) -> None:
        raise KeyError("missing")

    broken = Transform(name="broken", kind=TransformKind.COSMETIC, reason="Fails.", apply=fail)

    with pytest.raises(GenerationError, match="Transform 'broken' failed"):
        run_transforms((broken,), [])

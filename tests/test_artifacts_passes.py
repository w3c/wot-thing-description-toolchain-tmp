import dataclasses
import logging

import pytest

from wot_toolchain.artifacts.passes import Pass, PassKind, run_passes
from wot_toolchain.errors import GenerationError, SchemaError


def _recording_pass(name: str, log: list[tuple[str, tuple[object, ...]]]) -> Pass:
    def apply(*args: object) -> None:
        log.append((name, args))

    return Pass(name=name, kind=PassKind.COSMETIC, reason="test", apply=apply)


def _raising_pass(name: str, error: Exception) -> Pass:
    def apply(*args: object) -> None:
        raise error

    return Pass(name=name, kind=PassKind.UPSTREAM_BUG, reason="test", apply=apply)


def test_pass_kind_values() -> None:
    assert [kind.name for kind in PassKind] == ["UPSTREAM_BUG", "UPSTREAM_GAP", "WOT_SHAPING", "COSMETIC"]


def test_passes_run_in_sequence_order() -> None:
    log: list[tuple[str, tuple[object, ...]]] = []
    run_passes([_recording_pass("first", log), _recording_pass("second", log), _recording_pass("third", log)])
    assert [name for name, _ in log] == ["first", "second", "third"]


def test_args_are_passed_through() -> None:
    log: list[tuple[str, tuple[object, ...]]] = []
    artifact: dict[str, object] = {}
    run_passes([_recording_pass("only", log)], artifact, "extra")
    assert log == [("only", (artifact, "extra"))]
    assert log[0][1][0] is artifact


def test_toolchain_error_propagates_unchanged() -> None:
    error = SchemaError("bad slot")
    with pytest.raises(SchemaError) as caught:
        run_passes([_raising_pass("broken", error)])
    assert caught.value is error


def test_generation_error_propagates_unchanged() -> None:
    error = GenerationError("cannot shape")
    with pytest.raises(GenerationError) as caught:
        run_passes([_raising_pass("broken", error)])
    assert caught.value is error


def test_foreign_exception_is_wrapped_naming_the_pass() -> None:
    error = KeyError("missing")
    with pytest.raises(GenerationError, match="broken_pass") as caught:
        run_passes([_raising_pass("broken_pass", error)])
    assert caught.value.__cause__ is error


def test_later_passes_do_not_run_after_failure() -> None:
    log: list[tuple[str, tuple[object, ...]]] = []
    with pytest.raises(GenerationError):
        run_passes([_raising_pass("broken", ValueError("x")), _recording_pass("after", log)])
    assert log == []


def test_empty_sequence_is_a_no_op() -> None:
    run_passes([], {})


def test_each_pass_name_is_debug_logged(caplog: pytest.LogCaptureFixture) -> None:
    log: list[tuple[str, tuple[object, ...]]] = []
    with caplog.at_level(logging.DEBUG, logger="wot_toolchain.artifacts.passes"):
        run_passes([_recording_pass("alpha", log), _recording_pass("beta", log)])
    messages = [record.getMessage() for record in caplog.records if record.name == "wot_toolchain.artifacts.passes"]
    assert len(messages) == 2
    assert "alpha" in messages[0]
    assert "beta" in messages[1]


@pytest.mark.parametrize("field", ["name", "reason"])
@pytest.mark.parametrize("blank", ["", "   ", "\t\n"])
def test_blank_name_or_reason_is_rejected(field: str, blank: str) -> None:
    values = {"name": "valid", "reason": "valid"} | {field: blank}
    with pytest.raises(ValueError, match=field):
        Pass(name=values["name"], kind=PassKind.WOT_SHAPING, reason=values["reason"], apply=lambda: None)


def test_pass_is_frozen() -> None:
    p = Pass(name="frozen", kind=PassKind.UPSTREAM_GAP, reason="test", apply=lambda: None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.name = "changed"  # type: ignore[misc]

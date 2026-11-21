"""Markdown report of the JSON paths that differ between a generated and a reference document."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from wot_toolchain.cli import main
from wot_toolchain.diff_report import (
    json_change_summary,
    json_changes,
    json_pointer,
    load_json,
    markdown_report,
)
from wot_toolchain.errors import GenerationError

REFERENCE = {"a": 1, "gone": True, "list": [1, 2], "nested": {"x/y": "old", "m~n": 0}}
GENERATED = {"a": 2, "list": [1, 3], "nested": {"x/y": "new", "m~n": 0}, "new": None}


def _write(path: Path, data: object) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.fixture
def documents(tmp_path: Path) -> tuple[Path, Path]:
    return _write(tmp_path / "generated.json", GENERATED), _write(tmp_path / "reference.json", REFERENCE)


def test_json_changes_lists_kind_and_path_from_reference_to_generated() -> None:
    assert json_changes(REFERENCE, GENERATED) == [
        ("changed", ("a",)),
        ("removed", ("gone",)),
        ("changed", ("list", 1)),
        ("changed", ("nested", "x/y")),
        ("added", ("new",)),
    ]


def test_lists_of_different_length_change_as_a_whole() -> None:
    assert json_changes({"l": [1]}, {"l": [1, 2]}) == [("changed", ("l",))]


def test_identical_documents_have_no_changes() -> None:
    assert json_changes(REFERENCE, json.loads(json.dumps(REFERENCE))) == []


@pytest.mark.parametrize(
    "path, pointer",
    [((), ""), (("a", 0, "b"), "/a/0/b"), (("x/y",), "/x~1y"), (("m~n",), "/m~0n"), (("~1",), "/~01")],
)
def test_json_pointer_escapes_per_rfc_6901(path: tuple[str | int, ...], pointer: str) -> None:
    assert json_pointer(path) == pointer


def test_json_change_summary_groups_by_pattern() -> None:
    golden = json.dumps({"$defs": {"A": {"type": "string"}, "B": {"type": "string"}}})
    current = json.dumps({"$defs": {"A": {"type": "integer"}, "B": {"type": "integer"}}, "extra": 1})
    assert json_change_summary(golden, current) == [
        "3 changes, 2 patterns",
        "    2  changed  $.$defs.*.type   e.g. $.$defs.A.type",
        "    1  added    $.extra   e.g. $.extra",
    ]


def test_markdown_report_names_files_counts_and_sorted_paths(documents: tuple[Path, Path]) -> None:
    generated, reference = documents
    report = markdown_report(generated, reference)
    assert str(generated) in report
    assert str(reference) in report
    assert "| added | 1 |" in report
    assert "| removed | 1 |" in report
    assert "| changed | 3 |" in report
    assert "```\n/a\n/list/1\n/nested/x~1y\n```" in report
    assert "```\n/new\n```" in report
    assert "```\n/gone\n```" in report


def test_markdown_report_is_deterministic(documents: tuple[Path, Path]) -> None:
    assert markdown_report(*documents) == markdown_report(*documents)


def test_markdown_report_of_identical_files_says_no_differences(tmp_path: Path) -> None:
    generated = _write(tmp_path / "g.json", REFERENCE)
    reference = _write(tmp_path / "r.json", REFERENCE)
    report = markdown_report(generated, reference)
    assert "No differences." in report
    assert "```" not in report


def test_root_type_change_is_reported_at_the_root(tmp_path: Path) -> None:
    report = markdown_report(_write(tmp_path / "g.json", []), _write(tmp_path / "r.json", {}))
    assert "| changed | 1 |" in report
    assert "```\n(document root)\n```" in report


def test_load_json_names_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    with pytest.raises(GenerationError, match="missing.json"):
        load_json(missing)


def test_load_json_names_invalid_file(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{ not json", encoding="utf-8")
    with pytest.raises(GenerationError, match="broken.json"):
        load_json(broken)


def test_cli_prints_report_and_exits_zero_on_differences(documents: tuple[Path, Path]) -> None:
    result = CliRunner().invoke(main, ["diff-report", *map(str, documents)])
    assert result.exit_code == 0, result.output
    assert result.output == markdown_report(*documents) + "\n"


def test_cli_exits_zero_on_identical_files(tmp_path: Path) -> None:
    generated = _write(tmp_path / "g.json", REFERENCE)
    reference = _write(tmp_path / "r.json", REFERENCE)
    result = CliRunner().invoke(main, ["diff-report", str(generated), str(reference)])
    assert result.exit_code == 0, result.output
    assert "No differences." in result.output


def test_cli_missing_file_exits_one_and_names_it(
    documents: tuple[Path, Path], tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    missing = tmp_path / "absent.json"
    result = CliRunner().invoke(main, ["diff-report", str(documents[0]), str(missing)])
    assert result.exit_code == 1
    assert "absent.json" in caplog.text
    assert result.output == ""


def test_cli_invalid_json_exits_one_and_names_it(
    documents: tuple[Path, Path], tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{ not json", encoding="utf-8")
    result = CliRunner().invoke(main, ["diff-report", str(broken), str(documents[1])])
    assert result.exit_code == 1
    assert "broken.json" in caplog.text

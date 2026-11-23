"""Failures must fail: broken inputs give a non-zero exit code and a typed error."""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from wot_toolchain.cli import main
from wot_toolchain.errors import ExternalToolError, GenerationError
from wot_toolchain.specgen.assertions import (
    ASSERTION_INLINE,
    ASSERTION_TABLE,
    html_assertions_to_csv,
    validate_html_assertion_inventory,
)
from wot_toolchain.specgen.bikeshed_processor import _split_by_markers, process_fragments

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_BIN = Path(sys.executable).parent / "wot-toolchain"


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A private copy of the project config file and the input resources, without generated output."""
    shutil.copy2(REPO_ROOT / "wot-toolchain.yaml", tmp_path / "wot-toolchain.yaml")
    shutil.copytree(REPO_ROOT / "resources", tmp_path / "resources", ignore=shutil.ignore_patterns("gens"))
    return tmp_path


def _generate(project: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(CLI_BIN), "generate-wot-resources"],
        cwd=project,
        capture_output=True,
        text=True,
    )


def test_valid_project_exits_zero(project: Path) -> None:
    result = _generate(project)
    assert result.returncode == 0, result.stderr


def test_broken_schema_exits_nonzero(project: Path) -> None:
    schema = project / "resources" / "schemas" / "thing_description.yaml"
    schema.write_text(schema.read_text(encoding="utf-8") + "\nclasses: [unclosed\n", encoding="utf-8")
    assert _generate(project).returncode != 0


def test_invalid_snippet_exits_nonzero_and_names_the_file(project: Path) -> None:
    (project / "resources" / "snippets" / "action-serialization.json").write_text("{ not json", encoding="utf-8")
    result = _generate(project)
    assert result.returncode != 0
    assert "action-serialization.json" in result.stderr


def test_bikeshed_nonzero_exit_raises_with_stderr(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    failing_interpreter = tmp_path / "python"
    failing_interpreter.write_text("#!/bin/sh\necho 'FATAL: boom' >&2\nexit 3\n", encoding="utf-8")
    failing_interpreter.chmod(0o755)
    monkeypatch.setattr(sys, "executable", str(failing_interpreter))
    with pytest.raises(ExternalToolError, match="FATAL: boom"):
        process_fragments(["a"], ["<p>x</p>"], tmp_path / "glossary.yaml")


def test_unrunnable_bikeshed_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "executable", str(tmp_path / "no-such-python"))
    with pytest.raises(ExternalToolError, match="bikeshed"):
        process_fragments(["a"], ["<p>x</p>"], tmp_path / "glossary.yaml")


def test_section_marker_mismatch_raises() -> None:
    with pytest.raises(GenerationError):
        _split_by_markers("no markers here", ["a", "b"])


def test_invalid_assertion_inventory_raises_and_writes_no_csv(tmp_path: Path) -> None:
    html = tmp_path / "index.html"
    html.write_text(
        f'<html><body><span class="{ASSERTION_INLINE}" id="dup">A MUST b.</span>'
        f'<span class="{ASSERTION_INLINE}" id="dup">C MUST d.</span></body></html>',
        encoding="utf-8",
    )
    out = tmp_path / "assertions.csv"
    with pytest.raises(GenerationError):
        html_assertions_to_csv(html, out)
    assert not out.exists()


def _table_assertion_html(tmp_path: Path, *ids: str) -> Path:
    rows = "".join(f'<tr class="{ASSERTION_TABLE}" id="{assertion_id}"><td>x</td></tr>' for assertion_id in ids)
    html = tmp_path / "index.html"
    html.write_text(f"<html><body><table>{rows}</table></body></html>", encoding="utf-8")
    return html


def test_inventory_flags_vocab_ids_of_given_foreign_prefixes(tmp_path: Path) -> None:
    html = _table_assertion_html(tmp_path, "core-vocab-a--Root", "extra-vocab-b--Item")
    problems = validate_html_assertion_inventory(html, foreign_vocab_id_prefixes=("extra",))
    assert problems == ["foreign table assertion prefixes: extra-vocab-b--Item"]


def test_inventory_knows_no_foreign_prefixes_by_itself(tmp_path: Path) -> None:
    html = _table_assertion_html(tmp_path, "jsonschema-vocab-a--A", "wotsec-vocab-b--B", "hctl-vocab-c--C")
    assert validate_html_assertion_inventory(html) == []


def test_quiet_is_a_flag() -> None:
    root = logging.getLogger()
    previous = root.level
    try:
        result = CliRunner().invoke(main, ["-q", "generate-wot-resources", "--help"])
        assert result.exit_code == 0, result.output
        assert "--only" in result.output
    finally:
        root.setLevel(previous)

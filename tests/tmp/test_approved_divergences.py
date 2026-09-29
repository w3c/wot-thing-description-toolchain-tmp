"""Validate the governance metadata for approved upstream divergences."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml


TESTS_DIR = Path(__file__).resolve().parent.parent
DIVERGENCES_DIR = TESTS_DIR / "approved_divergences"
DOCUMENTS = {
    "html.yaml": {"semantic-correction", "editorial-correction"},
    "snippets.yaml": {"complete-example"},
}


@pytest.mark.parametrize(("filename", "categories"), DOCUMENTS.items())
def test_approved_divergence_document_is_well_formed(
    filename: str, categories: set[str]
) -> None:
    document = yaml.safe_load((DIVERGENCES_DIR / filename).read_text(encoding="utf-8"))

    assert set(document) == {"schema_version", "upstream", "policy", "divergences"}
    assert document["schema_version"] == 1
    assert document["upstream"]["repository"] == "w3c/wot-thing-description"
    assert document["upstream"]["artifact"] == "resources/upstream/html/index.html"
    assert document["policy"]

    divergences = document["divergences"]
    identifiers = [entry["id"] for entry in divergences]
    assert len(identifiers) == len(set(identifiers)), "divergence IDs must be unique"
    for entry in divergences:
        assert entry["category"] in categories
        assert entry["review"] == "approved"
        assert entry["rationale"]
        assert entry["upstream_locator"]
        assert entry["expected_generated"]


def test_html_divergences_have_complete_locators() -> None:
    document = yaml.safe_load((DIVERGENCES_DIR / "html.yaml").read_text(encoding="utf-8"))
    for entry in document["divergences"]:
        locator = entry["upstream_locator"]
        if locator["kind"] == "table_cell":
            assert {"section_id", "table", "row_id", "column"} <= set(locator)
        else:
            assert locator["kind"] == "assertion"
            assert locator.get("assertion_id")
        assert entry["expected_generated"].get("text")


def test_snippet_divergences_have_complete_locators() -> None:
    document = yaml.safe_load((DIVERGENCES_DIR / "snippets.yaml").read_text(encoding="utf-8"))
    for entry in document["divergences"]:
        locator = entry["upstream_locator"]
        assert locator["kind"] == "example"
        assert locator.get("example_id")
        assert entry["expected_difference_paths"]
        assert entry["expected_generated"].get("json_paths")

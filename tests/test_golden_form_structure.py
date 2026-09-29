"""Validate generated Form and response specification structure."""

import re
from pathlib import Path

import pytest

GENERATED_HTML_PATH = Path(__file__).resolve().parent.parent / "resources" / "gens" / "index.html"

EXPECTED_OPERATION_TYPES = [
    "readproperty",
    "writeproperty",
    "observeproperty",
    "unobserveproperty",
    "invokeaction",
    "queryaction",
    "cancelaction",
    "subscribeevent",
    "unsubscribeevent",
    "readallproperties",
    "writeallproperties",
    "readmultipleproperties",
    "writemultipleproperties",
    "observeallproperties",
    "unobserveallproperties",
    "queryallactions",
    "subscribeallevents",
    "unsubscribeallevents",
]

EXPECTED_RESPONSE_ASSERTION_IDS = [
    "td-expectedResponse-default-contentType",
    "td-expectedResponse-missing-contentType",
    "td-expectedResponse-defined-contentType",
]

ADDITIONAL_EXPECTED_RESPONSE_ASSERTION_IDS = [
    "td-additionalExpectedResponse-contentType",
    "td-additionalExpectedResponse-missing-contentType",
    "td-additionalExpectedResponse-schema",
    "td-additionalExpectedResponse-noSchemaWithoutPayload",
]


@pytest.fixture(scope="module")
def generated_html() -> str:
    if not GENERATED_HTML_PATH.exists():
        pytest.skip(f"Generated HTML not found at {GENERATED_HTML_PATH}")
    return GENERATED_HTML_PATH.read_text(encoding="utf-8")


def _extract_section(html: str, section_id: str) -> str:
    pattern = rf'<section\s[^>]*id="{re.escape(section_id)}"[^>]*>'
    match = re.search(pattern, html)
    if not match:
        return ""
    start = match.start()
    depth = 0
    i = start
    while i < len(html):
        if html[i:i+8] == "<section":
            depth += 1
        elif html[i:i+10] == "</section>":
            depth -= 1
            if depth == 0:
                return html[start:i + 10]
        i += 1
    return ""


def _extract_section_by_heading_id(html: str, heading_id: str) -> str:
    pattern = rf'<section\b[^>]*>\s*<h[1-6]\s+id="{re.escape(heading_id)}"[^>]*>'
    match = re.search(pattern, html)
    if not match:
        return ""
    start = match.start()
    depth = 0
    i = start
    while i < len(html):
        if html[i:i+8] == "<section":
            depth += 1
        elif html[i:i+10] == "</section>":
            depth -= 1
            if depth == 0:
                return html[start:i + 10]
        i += 1
    return ""


class TestFormSubsectionsPresent:
    def test_well_known_operation_types_table_present(self, generated_html: str) -> None:
        form_section = _extract_section_by_heading_id(generated_html, "form")
        assert form_section, "Form section not found"
        assert 'id="table-operation-types"' in form_section

    def test_op_data_schema_mapping_is_in_interaction_semantics(self, generated_html: str) -> None:
        interaction_semantics = _extract_section(generated_html, "interaction-semantics")
        assert interaction_semantics, "Interaction Semantics section not found"
        assert 'id="sec-op-data-schema-mapping"' in interaction_semantics

        form_section = _extract_section_by_heading_id(generated_html, "form")
        assert form_section, "Form section not found"
        assert 'id="sec-op-data-schema-mapping"' not in form_section

    def test_response_usage_subsection_is_not_present(self, generated_html: str) -> None:
        assert 'id="sec-response-usage"' not in generated_html


class TestSectionTableIDs:
    def test_operation_types_table_id(self, generated_html: str) -> None:
        assert 'id="table-operation-types"' in generated_html

    def test_op_mapping_section_id(self, generated_html: str) -> None:
        assert 'id="sec-op-data-schema-mapping"' in generated_html

    def test_op_mapping_is_informative(self, generated_html: str) -> None:
        mapping_section = _extract_section(generated_html, "sec-op-data-schema-mapping")
        assert mapping_section, "sec-op-data-schema-mapping section not found"
        assert 'class="informative"' in mapping_section.split(">")[0]


class TestOperationTypeTableRows:
    @pytest.mark.parametrize("op_type", EXPECTED_OPERATION_TYPES)
    def test_operation_type_in_table(self, generated_html: str, op_type: str) -> None:
        form_section = _extract_section_by_heading_id(generated_html, "form")
        table_match = re.search(
            r'<div id="table-operation-types">.*?</div>',
            form_section,
            re.DOTALL,
        )
        assert table_match, "Operation types table not found"
        table_html = table_match.group()
        operation_cell = rf"<td>\s*{re.escape(op_type)}\s*</td>"
        assert re.search(operation_cell, table_html), (
            f"Operation type '{op_type}' not found in well-known operation types table"
        )


class TestResponseAssertionPlacement:
    @pytest.mark.parametrize("assertion_id", EXPECTED_RESPONSE_ASSERTION_IDS)
    def test_expected_response_assertion_is_in_expected_response_section(
        self, generated_html: str, assertion_id: str
    ) -> None:
        expected_response_section = _extract_section_by_heading_id(
            generated_html, "expectedresponse"
        )
        assert expected_response_section, "ExpectedResponse section not found"
        assert f'id="{assertion_id}"' in expected_response_section, (
            f"Assertion '{assertion_id}' not found in ExpectedResponse section"
        )

    @pytest.mark.parametrize("assertion_id", ADDITIONAL_EXPECTED_RESPONSE_ASSERTION_IDS)
    def test_additional_expected_response_assertion_is_in_additional_expected_response_section(
        self, generated_html: str, assertion_id: str
    ) -> None:
        additional_expected_response_section = _extract_section_by_heading_id(
            generated_html, "additionalexpectedresponse"
        )
        assert additional_expected_response_section, "AdditionalExpectedResponse section not found"
        assert f'id="{assertion_id}"' in additional_expected_response_section, (
            f"Assertion '{assertion_id}' not found in AdditionalExpectedResponse section"
        )

    @pytest.mark.parametrize("assertion_id", EXPECTED_RESPONSE_ASSERTION_IDS)
    def test_expected_response_assertion_is_not_in_additional_expected_response_section(
        self, generated_html: str, assertion_id: str
    ) -> None:
        additional_expected_response_section = _extract_section_by_heading_id(
            generated_html, "additionalexpectedresponse"
        )
        assert f'id="{assertion_id}"' not in additional_expected_response_section, (
            f"Assertion '{assertion_id}' should not be in AdditionalExpectedResponse section"
        )

    @pytest.mark.parametrize("assertion_id", ADDITIONAL_EXPECTED_RESPONSE_ASSERTION_IDS)
    def test_additional_expected_response_assertion_is_not_in_expected_response_section(
        self, generated_html: str, assertion_id: str
    ) -> None:
        expected_response_section = _extract_section_by_heading_id(
            generated_html, "expectedresponse"
        )
        assert f'id="{assertion_id}"' not in expected_response_section, (
            f"Assertion '{assertion_id}' should not be in ExpectedResponse section"
        )

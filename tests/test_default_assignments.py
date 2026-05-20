from pathlib import Path

from linkml_runtime.utils.schemaview import SchemaView

from src.wotis.specgen.tables import collect_slot_rows


def _plain_markdown(text: str) -> str:
    return text or ""


def test_td20_default_assignments_match_manual_golden_rows() -> None:
    cases = [
        ("resources/schemas/thing_description.yaml", "PropertyAffordance"),
        ("resources/schemas/thing_description.yaml", "ActionAffordance"),
        ("resources/schemas/jsonschema.yaml", "DataSchema"),
        ("resources/schemas/wot_security.yaml", "BasicSecurityScheme"),
        ("resources/schemas/wot_security.yaml", "DigestSecurityScheme"),
        ("resources/schemas/wot_security.yaml", "APIKeySecurityScheme"),
        ("resources/schemas/wot_security.yaml", "BearerSecurityScheme"),
        ("resources/schemas/hypermedia.yaml", "Form"),
        ("resources/schemas/hypermedia.yaml", "AdditionalExpectedResponse"),
    ]
    expected = {
        "td-vocab-observable--PropertyAffordance",
        "td-vocab-safe--ActionAffordance",
        "td-vocab-idempotent--ActionAffordance",
        "td-vocab-readOnly--DataSchema",
        "td-vocab-writeOnly--DataSchema",
        "td-vocab-in--BasicSecurityScheme",
        "td-vocab-in--DigestSecurityScheme",
        "td-vocab-qop--DigestSecurityScheme",
        "td-vocab-in--APIKeySecurityScheme",
        "td-vocab-in--BearerSecurityScheme",
        "td-vocab-alg--BearerSecurityScheme",
        "td-vocab-format--BearerSecurityScheme",
        "td-vocab-contentType--Form",
        "td-vocab-op--Form",
        "td-vocab-success--AdditionalExpectedResponse",
    }

    actual = set()
    for schema_path, class_name in cases:
        schema_view = SchemaView(str(Path(schema_path)), merge_imports=True)
        for row in collect_slot_rows(schema_view, class_name, _plain_markdown, "td"):
            if row["assignment"] == '<a href="#sec-default-values">with default</a>':
                actual.add(row["assertion_id"])

    assert actual == expected


def test_type_value_hints_are_independent_from_default_assignment() -> None:
    security = SchemaView("resources/schemas/wot_security.yaml", merge_imports=True)
    hypermedia = SchemaView("resources/schemas/hypermedia.yaml", merge_imports=True)

    basic_rows = {
        row["assertion_id"]: row
        for row in collect_slot_rows(security, "BasicSecurityScheme", _plain_markdown, "td")
    }
    apikey_rows = {
        row["assertion_id"]: row
        for row in collect_slot_rows(security, "APIKeySecurityScheme", _plain_markdown, "td")
    }
    bearer_rows = {
        row["assertion_id"]: row
        for row in collect_slot_rows(security, "BearerSecurityScheme", _plain_markdown, "td")
    }
    form_rows = {
        row["assertion_id"]: row
        for row in collect_slot_rows(hypermedia, "Form", _plain_markdown, "td")
    }

    xsd = "https://www.w3.org/TR/2012/REC-xmlschema11-2-20120405/#"
    s = f'<a href="{xsd}string"><code>string</code></a>'

    assert basic_rows["td-vocab-in--BasicSecurityScheme"]["range_text"] == (
        f"{s} (one of header, query, body, cookie, or auto)"
    )
    assert apikey_rows["td-vocab-in--APIKeySecurityScheme"]["range_text"] == (
        f"{s} (one of header, query, body, cookie, uri, or auto)"
    )
    assert bearer_rows["td-vocab-alg--BearerSecurityScheme"]["range_text"] == (
        f"{s} (e.g., ES256, or ES512-256)"
    )
    assert form_rows["td-vocab-op--Form"]["range_text"].startswith(
        f"{s} or <a>Array</a> of {s} (one of readproperty"
    )
    assert form_rows["td-vocab-subprotocol--Form"]["assignment"] == "optional"
    assert form_rows["td-vocab-subprotocol--Form"]["range_text"] == (
        f"{s} (e.g., longpoll, websub, or sse)"
    )

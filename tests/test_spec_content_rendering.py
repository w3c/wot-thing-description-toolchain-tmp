from unittest.mock import MagicMock

from src.wotis.respec_doc_generator import (
    render_spec_content_annotation,
    render_subsections,
)


def _process_description(text: str) -> str:
    html = (
        text.replace("*MUST*", "<em>MUST</em>")
        .replace("Thing Description", "<a>Thing Description</a>")
        .replace("TD Processors", "<a>TD Processors</a>")
    )
    return f"<p>{html}</p>"


def _make_mock_schema_view(enum_name: str, permissible_values: dict) -> MagicMock:
    sv = MagicMock()
    enum_def = MagicMock()
    pvs = {}
    for name, data in permissible_values.items():
        pv = MagicMock()
        pv.text = name
        pv.description = data.get("description", "")
        pv.comments = data.get("comments", [])
        pvs[name] = pv
    enum_def.permissible_values = pvs
    sv.get_enum.return_value = enum_def
    return sv


def test_spec_content_renders_assertion_list_items() -> None:
    annotations = {
        "spec_content": {
            "value": [
                {
                    "type": "list",
                    "items": [
                        {
                            "id": "td-context-ns-thing-mandatory",
                            "text": "Thing Description *MUST* include context.",
                        },
                        {"text": "Plain list item."},
                    ],
                }
            ],
        }
    }

    html = render_spec_content_annotation(annotations, _process_description)

    assert '<ul id=' not in html
    assert '<span class="rfc2119-assertion" id="td-context-ns-thing-mandatory">' in html
    assert "<a>Thing Description</a> <em>MUST</em> include context." in html
    assert "<li>Plain list item.</li>" in html


def test_spec_content_renders_assertion_inside_paragraph() -> None:
    annotations = {
        "spec_content": {
            "value": [
                {
                    "type": "paragraph",
                    "segments": [
                        {"text": "Before."},
                        {
                            "id": "td-processor-bidi-isolation",
                            "text": "TD Processors *MUST* isolate text.",
                        },
                        {"text": "After."},
                    ],
                }
            ],
        }
    }

    html = render_spec_content_annotation(annotations, _process_description)

    assert html.startswith("<p>Before. ")
    assert '<p id=' not in html
    assert '<span class="rfc2119-assertion" id="td-processor-bidi-isolation">' in html
    assert "<a>TD Processors</a> <em>MUST</em> isolate text." in html
    assert html.endswith(" After.</p>")


def test_spec_content_renders_note_block_directly() -> None:
    annotations = {
        "spec_content": {
            "value": [
                {
                    "type": "note",
                    "text": "Thing Description note.",
                }
            ],
        }
    }

    html = render_spec_content_annotation(annotations, _process_description)

    assert html == '<div class="note">\n<p><a>Thing Description</a> note.</p>\n</div>'
    assert ":::NOTE" not in html


def test_note_block_with_title() -> None:
    annotations = {
        "spec_content": {
            "value": [
                {
                    "type": "note",
                    "title": "Important caveat",
                    "text": "Some note text.",
                }
            ],
        }
    }

    html = render_spec_content_annotation(annotations, _process_description)

    assert '<p class="note" title="Important caveat">' in html
    assert "Some note text." in html
    assert "<div" not in html


def test_enum_table_renders_columns() -> None:
    sv = _make_mock_schema_view(
        "TestEnum",
        {
            "alpha": {"description": "First item"},
            "beta": {"description": "Second item"},
        },
    )
    annotations = {
        "spec_content": {
            "value": [
                {
                    "type": "enum_table",
                    "enum": "TestEnum",
                    "caption": "Test Table",
                    "table_id": "test-table",
                    "columns": [
                        {"field": "name", "header": "Name"},
                        {"field": "description", "header": "Description"},
                    ],
                }
            ],
        }
    }

    html = render_spec_content_annotation(
        annotations, _process_description, schema_view=sv
    )

    assert '<div id="test-table">' in html
    assert '<table class="def numbered">' in html
    assert "<caption>Test Table</caption>" in html
    assert "<th>Name</th>" in html
    assert "<th>Description</th>" in html
    assert "<td>alpha</td>" in html
    assert "<td>beta</td>" in html
    assert "First item" in html
    assert "Second item" in html


def test_enum_table_extracts_comment_columns() -> None:
    sv = _make_mock_schema_view(
        "OpType",
        {
            "readproperty": {
                "description": "Read op",
                "comments": [
                    "Thing to Consumer - All fields without writeOnly",
                    "Consumer to Thing - No correlation",
                ],
            },
        },
    )
    annotations = {
        "spec_content": {
            "value": [
                {
                    "type": "enum_table",
                    "enum": "OpType",
                    "columns": [
                        {"field": "name", "header": "Op"},
                        {
                            "field": "comment:Consumer to Thing",
                            "header": "C2T",
                        },
                        {
                            "field": "comment:Thing to Consumer",
                            "header": "T2C",
                        },
                    ],
                }
            ],
        }
    }

    html = render_spec_content_annotation(
        annotations, _process_description, schema_view=sv
    )

    assert "<td>readproperty</td>" in html
    assert "No correlation" in html
    assert "All fields without writeOnly" in html


def test_render_subsections_structure() -> None:
    annotations = {
        "spec_subsections": {
            "value": [
                {
                    "id": "sec-test",
                    "title": "Test Subsection",
                    "class": "informative",
                    "content": [
                        {"type": "markdown", "text": "Some content."},
                    ],
                },
                {
                    "id": "sec-other",
                    "title": "Other Subsection",
                    "content": [
                        {
                            "type": "list",
                            "items": [{"text": "Item one."}],
                        },
                    ],
                },
            ],
        }
    }

    html = render_subsections(annotations, _process_description)

    assert '<section id="sec-test" class="informative">' in html
    assert "<h4>Test Subsection</h4>" in html
    assert "Some content." in html
    assert '<section id="sec-other">' in html
    assert "class=" not in html.split("sec-other")[1].split(">")[0] or 'class="informative"' not in html.split("sec-other")[1]
    assert "<h4>Other Subsection</h4>" in html
    assert "<li>Item one.</li>" in html


def test_render_subsections_with_enum_table() -> None:
    sv = _make_mock_schema_view(
        "Colors",
        {
            "red": {"description": "A warm color"},
            "blue": {"description": "A cool color"},
        },
    )
    annotations = {
        "spec_subsections": {
            "value": [
                {
                    "id": "sec-colors",
                    "title": "Color Reference",
                    "content": [
                        {
                            "type": "enum_table",
                            "enum": "Colors",
                            "columns": [
                                {"field": "name", "header": "Color"},
                                {"field": "description", "header": "Desc"},
                            ],
                        }
                    ],
                }
            ],
        }
    }

    html = render_subsections(annotations, _process_description, schema_view=sv)

    assert '<section id="sec-colors">' in html
    assert "<h4>Color Reference</h4>" in html
    assert "<td>red</td>" in html
    assert "<td>blue</td>" in html
    assert "A warm color" in html

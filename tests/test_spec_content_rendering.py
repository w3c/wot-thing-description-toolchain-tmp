from src.wotis.respec_doc_generator import render_spec_content_annotation


def _process_description(text: str) -> str:
    html = (
        text.replace("*MUST*", "<em>MUST</em>")
        .replace("Thing Description", "<a>Thing Description</a>")
        .replace("TD Processors", "<a>TD Processors</a>")
    )
    return f"<p>{html}</p>"


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

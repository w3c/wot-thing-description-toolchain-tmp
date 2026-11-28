"""Test that a run reads each schema file once per merge mode."""

from pathlib import Path

from wot_toolchain.schema_utils import SchemaStore

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = REPO_ROOT / "resources" / "schemas"
TD_SCHEMA = SCHEMAS / "thing_description.yaml"


def test_same_file_and_merge_mode_share_one_view() -> None:
    store = SchemaStore()
    view = store.view(TD_SCHEMA, merge_imports=True)

    assert store.view(TD_SCHEMA, merge_imports=True) is view
    assert store.view(SCHEMAS / ".." / "schemas" / TD_SCHEMA.name, merge_imports=True) is view


def test_merge_mode_and_file_select_different_views() -> None:
    store = SchemaStore()
    merged = store.view(TD_SCHEMA, merge_imports=True)
    unmerged = store.view(TD_SCHEMA, merge_imports=False)

    assert unmerged is not merged
    assert "Form" in merged.schema.classes
    assert "Form" not in unmerged.schema.classes
    assert store.view(SCHEMAS / "hypermedia.yaml", merge_imports=False) is not unmerged

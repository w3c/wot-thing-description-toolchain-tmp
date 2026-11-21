"""A section schema that does not exist raises a typed error naming the file instead of being skipped."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from pathlib import Path

import pytest

from wot_toolchain.errors import SchemaError
from wot_toolchain.specgen.assertions import Assertion, extract_all_table_assertions, extract_inline_assertions

_Extractor = Callable[[dict[str, Path], dict[str, str]], list[Assertion]]


@pytest.mark.parametrize(
    "extract",
    [partial(extract_all_table_assertions, vocab_id_prefix="sen"), extract_inline_assertions],
    ids=["extract_all_table_assertions", "extract_inline_assertions"],
)
def test_missing_section_schema_raises_schema_error_naming_the_file(tmp_path: Path, extract: _Extractor) -> None:
    missing = tmp_path / "absent_module.yaml"
    with pytest.raises(SchemaError, match="absent_module.yaml"):
        extract({"sec-absent": missing}, {})

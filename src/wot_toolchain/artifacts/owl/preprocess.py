"""In-memory schema transforms before gen-owl."""

import copy
from pathlib import Path
from typing import cast

from linkml_runtime.linkml_model.meta import SchemaDefinition

from ...errors import SchemaError
from ...schema_utils import SchemaStore, load_schema_view
from ...schema_utils import get_schema as _get_schema


def preprocess_for_gen_owl(schema_path: Path, store: SchemaStore) -> SchemaDefinition:
    """Return a copy of the merged schema for gen-owl."""
    # Before merging: LinkML's merge would fail on a missing import with an untyped FileNotFoundError.
    _require_local_imports(schema_path, store)
    return copy.deepcopy(_get_schema(store.view(schema_path, merge_imports=True)))


def _require_local_imports(schema_path: Path, store: SchemaStore) -> None:
    """Check that ``schema_path`` and every local import reachable from it exist."""
    root_schema = _get_schema(load_schema_view(store, schema_path, merge_imports=False))

    # Import cycles are legal in LinkML; walk each file once so they do not recurse forever.
    visited: set[Path] = {schema_path.resolve()}

    def _walk(importer: str, imports: list[str], base_dir: Path) -> None:
        for import_name in imports:
            # CURIE imports (e.g. linkml:types) are resolved by LinkML, not from the local directory.
            if ":" in import_name:
                continue
            import_path = base_dir / f"{import_name}.yaml"
            if not import_path.is_file():
                raise SchemaError(f"{importer}: imports {import_name!r} but {import_path} does not exist.")
            if import_path.resolve() in visited:
                continue
            visited.add(import_path.resolve())
            sub_schema = _get_schema(store.view(import_path, merge_imports=False))
            _walk(str(import_path), cast(list[str], sub_schema.imports or []), import_path.parent)

    _walk(str(schema_path), cast(list[str], root_schema.imports or []), schema_path.parent)

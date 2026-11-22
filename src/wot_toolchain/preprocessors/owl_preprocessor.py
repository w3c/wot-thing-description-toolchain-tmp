"""In-memory schema transforms before gen-owl."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import cast

from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.linkml_model.meta import ClassDefinition, EnumDefinition, Prefix, SchemaDefinition, SlotDefinition
from linkml_runtime.utils.schemaview import SchemaView

from ..artifacts.owl.pre_passes import OWL_PRE_PASSES, OwlPreContext
from ..artifacts.owl.pre_passes import _attr_slot_name as _attr_slot_name
from ..artifacts.owl.pre_passes import _strip_non_ontological_enums as _strip_non_ontological_enums
from ..artifacts.passes import run_passes
from ..errors import SchemaError
from ..schema_utils import default_prefix, load_schema_view
from ..schema_utils import get_schema as _get_schema

_Slots = dict[str, SlotDefinition]
_Classes = dict[str, ClassDefinition]
_Enums = dict[str, EnumDefinition]
_Prefixes = dict[str, Prefix]


def preprocess_for_gen_owl(schema_path: str) -> str:
    """Return YAML string of schema ready for gen-owl.

    Raises:
        SchemaError: If a CURIE of the schema cannot be expanded because its prefix declarations
            (for example ``default_curi_maps``) cannot be resolved, the schema file or a local import
            does not exist, or the ``default_prefix`` is not declared.
    """
    context = _context(schema_path)
    s: SchemaDefinition = copy.deepcopy(_get_schema(context.view))
    run_passes(OWL_PRE_PASSES, s, context)
    return yaml_dumper.dumps(s)


def _context(schema_path: str) -> OwlPreContext:
    """Collect what the passes need from the schema at ``schema_path`` before any of them mutates its copy.

    Raises:
        SchemaError: If the schema file or a local import does not exist, or the ``default_prefix`` is not declared.
    """
    # Before merging: LinkML's merge would fail on a missing import with an untyped FileNotFoundError.
    enum_namespaces = _collect_enum_namespaces(schema_path)
    view = SchemaView(schema_path, merge_imports=True)
    local_schema = _get_schema(SchemaView(schema_path, merge_imports=False))
    local_slots = cast(_Slots, local_schema.slots)
    local_classes = cast(_Classes, local_schema.classes)
    return OwlPreContext(
        view=view,
        namespace=_namespace(view),
        local_schema_id=local_schema.id,
        enum_namespaces=enum_namespaces,
        no_uri_classes=frozenset(name for name, cls in local_classes.items() if not cls.class_uri),
        original_no_uri_slots=frozenset(name for name, slot in local_slots.items() if not slot.slot_uri),
    )


def _namespace(view: SchemaView) -> str:
    """Return the namespace URI of the default prefix of the schema of ``view``.

    Raises:
        SchemaError: If the schema has no ``default_prefix`` or it is not declared in ``prefixes``.
    """
    prefixes = cast(_Prefixes, _get_schema(view).prefixes)
    return str(cast(Prefix, prefixes[default_prefix(view)]).prefix_reference)


def _collect_enum_namespaces(schema_path: str) -> dict[str, str]:
    """Map each enum of the local imports of ``schema_path`` to the namespace of its originating sub-schema.

    Raises:
        SchemaError: If ``schema_path`` or a local (non-CURIE) import does not resolve to an existing file.
    """
    root_schema = _get_schema(load_schema_view(Path(schema_path), merge_imports=False))

    enum_to_ns: dict[str, str] = {}
    # Import cycles are legal in LinkML; walk each file once so they do not recurse forever.
    visited: set[Path] = {Path(schema_path).resolve()}

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
            sub_schema = _get_schema(SchemaView(str(import_path), merge_imports=False))
            dp = sub_schema.default_prefix
            prefixes = cast(_Prefixes, sub_schema.prefixes)
            if dp and dp in prefixes:
                sub_ns = str(cast(Prefix, prefixes[dp]).prefix_reference)
                for ename in cast(_Enums, sub_schema.enums):
                    if str(ename) not in enum_to_ns:
                        enum_to_ns[str(ename)] = sub_ns
            sub_imports = cast(list[str], sub_schema.imports or [])
            _walk(str(import_path), sub_imports, import_path.parent)

    root_imports = cast(list[str], root_schema.imports or [])
    _walk(schema_path, root_imports, Path(schema_path).parent)
    return enum_to_ns

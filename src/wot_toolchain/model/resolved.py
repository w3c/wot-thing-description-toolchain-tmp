"""The schema views of one project, each loaded once per pipeline run."""

from dataclasses import dataclass, field
from pathlib import Path

from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.model.annotations import validate_annotations
from wot_toolchain.schema_utils import load_schema_view


@dataclass(frozen=True, slots=True)
class ResolvedProject:
    """The merged view of the main schema and the unmerged view of each module, loaded on first use."""

    main_schema: Path
    # Mutable only to cache: each (file, merge_imports) pair is loaded once and then shared.
    _views: dict[tuple[Path, bool], SchemaView] = field(default_factory=dict, init=False, repr=False, compare=False)

    @property
    def merged(self) -> SchemaView:
        """Return the main schema with all imports merged.

        Raises:
            SchemaError: If the schema file is missing or is not valid YAML.
        """
        return self._view(self.main_schema, merge_imports=True)

    def validate(self) -> None:
        """Check the annotations of the merged view that the passes read.

        Raises:
            SchemaError: If the schema cannot be loaded or any of those annotations is malformed.
        """
        validate_annotations(self.merged)

    def module(self, schema: Path) -> SchemaView:
        """Return the view of ``schema`` without its imports merged.

        Raises:
            SchemaError: If the schema file is missing or is not valid YAML.
        """
        return self._view(schema, merge_imports=False)

    def _view(self, schema: Path, *, merge_imports: bool) -> SchemaView:
        key = (schema.resolve(), merge_imports)
        if key not in self._views:
            self._views[key] = load_schema_view(schema, merge_imports=merge_imports)
        return self._views[key]

"""Upstream linkml JSON-LD context generator with the WoT toolchain's fixed arguments."""

from copy import deepcopy
from typing import Any, Self

from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml_runtime.linkml_model.meta import SchemaDefinition, SlotDefinition
from linkml_runtime.utils.formatutils import underscore

from wot_toolchain.artifacts.jsonld_context.options import JsonLdContextOptions

type TermDefinition = dict[str, Any] | str


class WotContextGenerator(ContextGenerator):  # type: ignore[misc]  # linkml ships no type information
    """JSON-LD context generator; the only place that touches private upstream context API."""

    @classmethod
    def from_options(cls, schema: SchemaDefinition | str, options: JsonLdContextOptions) -> Self:
        """Build a generator for ``schema`` configured by ``options``."""
        return cls(
            schema,
            # Reason not recorded.
            mergeimports=True,
            fix_multivalue_containers=options.multivalue_containers,
        )

    def slot_term_definition(self, slot: SlotDefinition) -> TermDefinition:
        """Return the term definition upstream emits for ``slot``, independent of earlier calls."""
        # Upstream has no per-slot API: reset the accumulated body and replay visit_schema / visit_slot.
        self.context_body.clear()
        self.visit_schema()
        if slot.range is None:
            # Range-less slots get only an @id, not visit_slot; reason not recorded (introduced in 6bc508db).
            entry: dict[str, Any] = {}
            self._build_element_id(entry, slot.slot_uri)
            return entry
        self.visit_slot(slot.alias or slot.name, slot)
        term: TermDefinition = deepcopy(self.context_body[underscore(slot.alias or slot.name)])
        return term

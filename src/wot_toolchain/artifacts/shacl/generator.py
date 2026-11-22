"""Upstream linkml SHACL generator with the WoT toolchain's fixed arguments."""

from collections.abc import Callable
from typing import Self

from linkml.generators.common.subproperty import is_uri_range
from linkml.generators.shaclgen import ShaclGenerator
from linkml_runtime.linkml_model.meta import SchemaDefinition, SlotDefinition
from rdflib import SH, XSD, BNode, Graph, Literal, URIRef
from rdflib.collection import Collection

from wot_toolchain.artifacts.shacl.options import ShaclOptions

OBJECT_PROPERTY = "owl:ObjectProperty"


class WotShaclGenerator(ShaclGenerator):  # type: ignore[misc]  # linkml ships no type information
    """SHACL generator whose shape IRIs match the published WoT shapes."""

    @classmethod
    def from_options(cls, schema: SchemaDefinition | str, options: ShaclOptions) -> Self:
        """Build a generator for ``schema`` configured by ``options``."""
        return cls(
            schema,
            # Shape IRIs are published as <class IRI>Shape.
            suffix="Shape",
            # Shape IRIs are published as generated without merging imports.
            mergeimports=False,
            closed=not options.open,
            exclude_imports=options.only_root_schema_classes,
        )

    def as_graph(self) -> Graph:
        """Emit the shapes with literal URI slots and optional minimum counts stated as the schema means them."""
        graph: Graph = super().as_graph()
        self._constrain_literal_uris(graph)
        self._relax_optional_minimum_counts(graph)
        return graph

    def _constrain_literal_uris(self, graph: Graph) -> None:
        """Make a URI-valued slot that is no object property an ``xsd:anyURI`` literal."""
        # Upstream maps every URI range to sh:nodeKind sh:IRI and passes no slot to _add_type (shaclgen.py:708).
        for path in self._slot_paths(self._is_literal_uri):
            for shape in graph.subjects(SH.path, path):
                if (shape, SH.nodeKind, SH.IRI) in graph:
                    graph.set((shape, SH.nodeKind, SH.Literal))
                    graph.add((shape, SH.datatype, XSD.anyURI))

    def _relax_optional_minimum_counts(self, graph: Graph) -> None:
        """Let an optional slot with a minimum cardinality be absent or reach that count."""
        # Upstream writes minimum_cardinality as sh:minCount, which also makes the slot required (shaclgen.py:295).
        for path in self._slot_paths(self._has_optional_minimum_count):
            for node_shape, property_shape in list(graph.subject_objects(SH.property)):
                count = graph.value(property_shape, SH.minCount)
                if count is None or (property_shape, SH.path, path) not in graph:
                    continue
                graph.remove((property_shape, SH.minCount, count))
                absent, present = BNode(), BNode()
                graph.add((absent, SH.path, path))
                graph.add((absent, SH.maxCount, Literal(0)))
                graph.add((present, SH.path, path))
                graph.add((present, SH.minCount, count))
                alternatives = BNode()
                Collection(graph, alternatives, [absent, present])
                graph.add((node_shape, SH["or"], alternatives))

    def _slot_paths(self, selects: Callable[[SlotDefinition], bool]) -> set[URIRef]:
        """Return the property IRIs of the induced slots that ``selects`` accepts."""
        view = self.schemaview
        return {
            URIRef(view.get_uri(slot, expand=True))
            for class_name in view.all_classes()
            for slot in view.class_induced_slots(class_name)
            if selects(slot)
        }

    def _is_literal_uri(self, slot: SlotDefinition) -> bool:
        return is_uri_range(self.schemaview, slot.range) and OBJECT_PROPERTY not in (slot.implements or [])

    @staticmethod
    def _has_optional_minimum_count(slot: SlotDefinition) -> bool:
        return bool(slot.minimum_cardinality) and not slot.required

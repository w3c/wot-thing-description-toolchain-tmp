"""Upstream linkml SHACL generator with the WoT toolchain's fixed arguments."""

from typing import Self

from linkml.generators.common.subproperty import is_uri_range
from linkml.generators.shaclgen import ShaclGenerator
from linkml_runtime.linkml_model.meta import SchemaDefinition, SlotDefinition
from rdflib import SH, XSD, Graph, URIRef

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
        """Emit the shapes; a URI-valued slot that is no object property is an ``xsd:anyURI`` literal."""
        graph: Graph = super().as_graph()
        # Upstream maps every URI range to sh:nodeKind sh:IRI and passes no slot to _add_type (shaclgen.py:708).
        for path in self._literal_uri_paths():
            for shape in graph.subjects(SH.path, path):
                if (shape, SH.nodeKind, SH.IRI) in graph:
                    graph.set((shape, SH.nodeKind, SH.Literal))
                    graph.add((shape, SH.datatype, XSD.anyURI))
        return graph

    def _literal_uri_paths(self) -> set[URIRef]:
        """Return the property IRIs of the URI-valued slots that do not implement ``owl:ObjectProperty``."""
        view = self.schemaview
        return {
            URIRef(view.get_uri(slot, expand=True))
            for class_name in view.all_classes()
            for slot in view.class_induced_slots(class_name)
            if self._is_literal_uri(slot)
        }

    def _is_literal_uri(self, slot: SlotDefinition) -> bool:
        return is_uri_range(self.schemaview, slot.range) and OBJECT_PROPERTY not in (slot.implements or [])

"""Ordered post-processing passes applied to the SHACL graph."""

from linkml_runtime.utils.schemaview import SchemaView
from rdflib import Graph, URIRef
from rdflib.namespace import SH

from wot_toolchain.artifacts.passes import Pass, PassKind


def _jsonld_keyword_paths(schema_view: SchemaView) -> set[URIRef]:
    namespace = schema_view.schema.prefixes[schema_view.schema.default_prefix].prefix_reference
    return {
        URIRef(schema_view.expand_curie(slot.slot_uri)) if slot.slot_uri else URIRef(f"{namespace}{slot.name}")
        for slot in schema_view.all_slots().values()
        if (slot.alias or slot.name).startswith("@")
    }


def _remove_jsonld_keyword_properties(graph: Graph, schema_view: SchemaView) -> None:
    for path in _jsonld_keyword_paths(schema_view):
        for property_shape in list(graph.subjects(SH.path, path)):
            graph.remove((None, SH.property, property_shape))
            graph.remove((property_shape, None, None))


SHACL_PASSES: tuple[Pass, ...] = (
    Pass(
        name="remove_jsonld_keyword_properties",
        kind=PassKind.WOT_SHAPING,
        reason="@context/@type are JSON-LD keywords, not RDF properties, so they get no property shapes.",
        apply=_remove_jsonld_keyword_properties,
    ),
)

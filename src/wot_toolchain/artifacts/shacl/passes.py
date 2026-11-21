"""Ordered post-processing passes applied to the SHACL graph."""

from linkml_runtime.utils.schemaview import SchemaView
from rdflib import BNode, Graph, URIRef
from rdflib.collection import Collection
from rdflib.namespace import RDFS, SH
from rdflib.term import Node

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


def _remove_literal_datatype(graph: Graph, schema_view: SchemaView) -> None:
    """Remove ``sh:datatype rdfs:Literal``; the slot already carries ``sh:nodeKind sh:Literal``."""
    for s in list(graph.subjects(SH.datatype, RDFS.Literal)):
        graph.remove((s, SH.datatype, RDFS.Literal))


def _langstring_unions(schema_view: SchemaView) -> dict[tuple[URIRef, URIRef], list[URIRef]]:
    unions: dict[tuple[URIRef, URIRef], list[URIRef]] = {}
    for class_definition in schema_view.all_classes().values():
        if not class_definition.class_uri:
            continue
        for slot_name, slot_usage in class_definition.slot_usage.items():
            expressions = slot_usage.exactly_one_of or []
            ranges = [expression.range for expression in expressions if expression.range]
            slot_definition = schema_view.get_slot(slot_name)
            slot_uri = slot_usage.slot_uri or (slot_definition.slot_uri if slot_definition else None)
            if "langString" not in ranges or not slot_uri:
                continue

            datatypes = []
            for range_name in ranges:
                type_definition = schema_view.get_type(range_name)
                if not type_definition or not type_definition.uri:
                    continue
                datatype = URIRef(schema_view.expand_curie(type_definition.uri))
                if datatype not in datatypes:
                    datatypes.append(datatype)

            if len(datatypes) > 1:
                class_uri = URIRef(schema_view.expand_curie(class_definition.class_uri))
                unions[(class_uri, URIRef(schema_view.expand_curie(slot_uri)))] = datatypes
    return unions


# TODO: remove when https://github.com/orgs/linkml/discussions/2199 is resolved.
def _rewrite_langstring_union_to_sh_or(graph: Graph, schema_view: SchemaView) -> None:
    """Replace the datatype of each langString ``exactly_one_of`` slot usage with an ``sh:or`` of its datatypes."""
    for (class_uri, path), datatypes in _langstring_unions(schema_view).items():
        for node_shape in graph.subjects(SH.targetClass, class_uri):
            for property_shape in graph.objects(node_shape, SH.property):
                if (property_shape, SH.path, path) not in graph:
                    continue
                graph.remove((property_shape, SH.datatype, None))
                graph.remove((property_shape, SH["or"], None))

                branches: list[Node] = []
                for datatype in datatypes:
                    branch = BNode()
                    graph.add((branch, SH.datatype, datatype))
                    branches.append(branch)

                union = BNode()
                Collection(graph, union, branches)
                graph.add((property_shape, SH["or"], union))


SHACL_PASSES: tuple[Pass, ...] = (
    Pass(
        name="remove_jsonld_keyword_properties",
        kind=PassKind.WOT_SHAPING,
        reason="@context/@type are JSON-LD keywords, not RDF properties, so they get no property shapes.",
        apply=_remove_jsonld_keyword_properties,
    ),
    Pass(
        name="remove_literal_datatype",
        kind=PassKind.UPSTREAM_GAP,
        reason="Upstream emits sh:datatype rdfs:Literal, which is not a concrete datatype; sh:nodeKind sh:Literal "
        "already constrains the slot.",
        apply=_remove_literal_datatype,
    ),
    Pass(
        name="rewrite_langstring_union_to_sh_or",
        kind=PassKind.UPSTREAM_GAP,
        reason="LinkML SHACL drops heterogeneous exactly_one_of branches (discussion #2199), so xsd:string|"
        "rdf:langString is added back as sh:or.",
        apply=_rewrite_langstring_union_to_sh_or,
    ),
)

"""Post-process raw LinkML SHACL output for WoT datatype constraints."""

from __future__ import annotations

from linkml_runtime.utils.schemaview import SchemaView
from rdflib import BNode, Graph, URIRef
from rdflib.collection import Collection
from rdflib.namespace import RDFS, SH
from rdflib.term import Node

from ..artifacts.passes import run_passes
from ..artifacts.shacl.passes import SHACL_PASSES


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


def _remove_literal_datatype(graph: Graph) -> None:
    """Remove ``sh:datatype rdfs:Literal`` — not a concrete SHACL datatype.

    Slots typed ``rdfs:Literal`` in the schema already carry ``sh:nodeKind
    sh:Literal`` which is the correct SHACL constraint for accepting any
    literal type.
    """
    for s in list(graph.subjects(SH.datatype, RDFS.Literal)):
        graph.remove((s, SH.datatype, RDFS.Literal))


# W3C WoT requires rdf:langString alternatives for selected scalar slots; LinkML
# SHACL generation drops heterogeneous exactly_one_of branches (discussion #2199).
# TODO: remove when https://github.com/orgs/linkml/discussions/2199 is resolved.
def post_process_shacl(raw_shacl: str, schema_view: SchemaView) -> str:
    """Return raw LinkML SHACL Turtle with WoT datatype constraints corrected.

    Removes the property shapes of slots aliased to JSON-LD keywords and every ``sh:datatype rdfs:Literal``, and
    replaces the datatype of each slot usage whose ``exactly_one_of`` includes ``langString`` and has more than one
    branch datatype with an ``sh:or`` of those datatypes.
    """
    graph = Graph()
    graph.parse(data=raw_shacl, format="turtle")

    run_passes(SHACL_PASSES, graph, schema_view)
    _remove_literal_datatype(graph)

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

    return graph.serialize(format="turtle")

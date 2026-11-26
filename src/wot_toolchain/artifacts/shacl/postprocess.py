"""Post-process raw LinkML SHACL output for WoT datatype constraints."""

from __future__ import annotations

from rdflib import BNode, Graph, URIRef
from rdflib.collection import Collection
from rdflib.namespace import RDFS, SH
from rdflib.term import Node

from linkml_runtime.utils.schemaview import SchemaView

from ..transforms import Transform, TransformKind, run_transforms


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


def _add_langstring_alternatives(graph: Graph, schema_view: SchemaView) -> None:
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


def _remove_literal_datatype(graph: Graph, schema_view: SchemaView) -> None:
    """Remove ``sh:datatype rdfs:Literal``; the slot already carries ``sh:nodeKind sh:Literal``."""
    for shape in list(graph.subjects(SH.datatype, RDFS.Literal)):
        graph.remove((shape, SH.datatype, RDFS.Literal))


SHACL_TRANSFORMS: tuple[Transform, ...] = (
    # TODO: remove when https://github.com/orgs/linkml/discussions/2199 is resolved.
    Transform(
        name="add_langstring_alternatives",
        kind=TransformKind.LINKML_GAP,
        reason="LinkML emits one sh:datatype for a slot whose exactly_one_of ranges are several datatypes "
        "(discussion #2199). When one of them is langString, replaces sh:datatype by an sh:or over all of them.",
        apply=_add_langstring_alternatives,
    ),
    Transform(
        name="remove_literal_datatype",
        kind=TransformKind.LINKML_GAP,
        reason="LinkML emits sh:datatype rdfs:Literal for a slot whose range is rdfs:Literal. No literal has that "
        "datatype, so the constraint rejects every value. The shape keeps sh:nodeKind sh:Literal, which accepts "
        "plain and language-tagged strings.",
        apply=_remove_literal_datatype,
    ),
)


def post_process_shacl(raw_shacl: str, schema_view: SchemaView) -> str:
    graph = Graph()
    graph.parse(data=raw_shacl, format="turtle")
    run_transforms(SHACL_TRANSFORMS, graph, schema_view)
    return graph.serialize(format="turtle")

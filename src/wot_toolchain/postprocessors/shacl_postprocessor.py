"""Post-process raw LinkML SHACL output for WoT datatype constraints."""

from __future__ import annotations

from linkml_runtime.utils.schemaview import SchemaView
from rdflib import Graph

from ..artifacts.passes import run_passes
from ..artifacts.shacl.passes import SHACL_PASSES


def post_process_shacl(raw_shacl: str, schema_view: SchemaView) -> str:
    """Return raw LinkML SHACL Turtle with WoT datatype constraints corrected.

    Removes the property shapes of slots aliased to JSON-LD keywords and every ``sh:datatype rdfs:Literal``, and
    replaces the datatype of each slot usage whose ``exactly_one_of`` includes ``langString`` and has more than one
    branch datatype with an ``sh:or`` of those datatypes.
    """
    graph = Graph()
    graph.parse(data=raw_shacl, format="turtle")

    run_passes(SHACL_PASSES, graph, schema_view)

    return graph.serialize(format="turtle")

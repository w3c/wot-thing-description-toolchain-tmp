"""Serialize the OWL graph of one vocabulary as Turtle."""

from rdflib import Graph
from rdflib.plugin import register
from rdflib.serializer import Serializer

from .header import SCHEMA

register("wot-turtle", Serializer, "wot_toolchain.serializers.wot_turtle", "WotTurtleSerializer")


def post_process_owl(graph: Graph) -> str:
    """Return ``graph`` as Turtle."""
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)
    return graph.serialize(format="wot-turtle")

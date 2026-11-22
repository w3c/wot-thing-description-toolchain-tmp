"""Post-process gen-owl TTL into per-module OWL vocabulary files."""

from __future__ import annotations

from pathlib import Path

from linkml_runtime.utils.schemaview import SchemaView
from rdflib import Graph
from rdflib.plugin import register
from rdflib.serializer import Serializer

from ..artifacts.owl.header import SCHEMA
from ..artifacts.owl.passes import OWL_PASSES
from ..artifacts.passes import run_passes

register(
    "wot-turtle",
    Serializer,
    "wot_toolchain.serializers.wot_turtle",
    "WotTurtleSerializer",
)


def postprocess_owl(
    module_ttl: str,
    schema_file: str,
    output_file: str,
    schema_dir: Path,
    output_dir: Path,
    *,
    sv_merged: SchemaView | None = None,
) -> None:
    """Clean gen-owl output and write per-module OWL vocabulary file."""
    g = Graph()
    g.parse(data=module_ttl, format="turtle")
    postprocess_owl_graph(g, schema_file, output_file, schema_dir, output_dir, sv_merged=sv_merged)


def postprocess_owl_graph(
    g: Graph,
    schema_file: str,
    output_file: str,
    schema_dir: Path,
    output_dir: Path,
    *,
    sv_merged: SchemaView | None = None,
) -> None:
    """Clean the gen-owl graph in place and write the per-module OWL vocabulary file."""
    if sv_merged is None:
        sv_merged = SchemaView(str(schema_dir / schema_file), merge_imports=True)
    run_passes(OWL_PASSES, g, sv_merged)

    g.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    ttl = g.serialize(format="wot-turtle")
    (output_dir / output_file).write_text(ttl, encoding="utf-8")

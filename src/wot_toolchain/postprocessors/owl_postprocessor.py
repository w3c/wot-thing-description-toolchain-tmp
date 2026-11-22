"""Post-process gen-owl TTL into per-module OWL vocabulary files."""

from __future__ import annotations

from pathlib import Path

from linkml_runtime.utils.schemaview import SchemaView
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS
from rdflib.plugin import register
from rdflib.serializer import Serializer
from rdflib.term import Node

SCHEMA = Namespace("http://schema.org/")
LINKML = Namespace("https://w3id.org/linkml/")
LINKML_NS = str(LINKML)

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
    _strip_linkml_ranges(g)
    _add_domain_includes(g, sv_merged)

    g.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    ttl = g.serialize(format="wot-turtle")
    (output_dir / output_file).write_text(ttl, encoding="utf-8")


def _demote_to_datatype(g: Graph, props: set[Node]) -> None:
    """Demote ObjectProperty→DatatypeProperty for props that lost their only range."""
    for prop in props:
        if list(g.objects(prop, RDFS.range)):
            continue
        if (prop, RDF.type, OWL.ObjectProperty) in g:
            g.remove((prop, RDF.type, OWL.ObjectProperty))
            g.add((prop, RDF.type, OWL.DatatypeProperty))


def _strip_linkml_ranges(g: Graph) -> None:
    """Remove linkml: ranges; demote to DatatypeProperty if no range remains."""
    linkml_ranged_props: set[Node] = set()
    for s, _, o in list(g.triples((None, RDFS.range, None))):
        if isinstance(o, URIRef) and str(o).startswith(LINKML_NS):
            linkml_ranged_props.add(s)
            g.remove((s, RDFS.range, o))
    _demote_to_datatype(g, linkml_ranged_props)


def _add_domain_includes(g: Graph, sv: SchemaView) -> None:
    """Add schema:domainIncludes for properties used by multiple classes."""
    uri_to_classes: dict[str, set[str]] = {}
    for cls_def in sv.all_classes().values():
        if not cls_def.class_uri:
            continue
        for slot_name in cls_def.slots or []:
            su = (cls_def.slot_usage or {}).get(str(slot_name))
            if su and su.slot_uri:
                expanded = sv.expand_curie(su.slot_uri)
            else:
                slot = sv.get_slot(slot_name)
                if not slot or not slot.slot_uri:
                    continue
                expanded = sv.expand_curie(slot.slot_uri)
            uri_to_classes.setdefault(expanded, set()).add(cls_def.class_uri)
        for attr_def in (cls_def.attributes or {}).values():
            if attr_def.slot_uri:
                expanded = sv.expand_curie(attr_def.slot_uri)
                uri_to_classes.setdefault(expanded, set()).add(cls_def.class_uri)
    for uri_str, class_uris in uri_to_classes.items():
        if len(class_uris) < 2:
            continue
        prop_iri = URIRef(uri_str)
        if not any(g.triples((prop_iri, None, None))):
            continue
        for cu in class_uris:
            g.add((prop_iri, SCHEMA.domainIncludes, URIRef(sv.expand_curie(cu))))

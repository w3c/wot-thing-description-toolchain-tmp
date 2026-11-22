"""Ordered post-processing passes applied to the OWL graph."""

from linkml_runtime.utils.schemaview import SchemaView
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS
from rdflib.term import Node

from wot_toolchain.artifacts.owl.header import SCHEMA
from wot_toolchain.artifacts.passes import Pass, PassKind

LINKML = Namespace("https://w3id.org/linkml/")
LINKML_NS = str(LINKML)


def _demote_to_datatype(g: Graph, props: set[Node]) -> None:
    """Demote ObjectProperty→DatatypeProperty for props that lost their only range."""
    for prop in props:
        if list(g.objects(prop, RDFS.range)):
            continue
        if (prop, RDF.type, OWL.ObjectProperty) in g:
            g.remove((prop, RDF.type, OWL.ObjectProperty))
            g.add((prop, RDF.type, OWL.DatatypeProperty))


def _strip_linkml_ranges(g: Graph, schema_view: SchemaView) -> None:
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
        g.add((SCHEMA.domainIncludes, RDF.type, OWL.AnnotationProperty))
        for cu in class_uris:
            g.add((prop_iri, SCHEMA.domainIncludes, URIRef(sv.expand_curie(cu))))


OWL_PASSES: tuple[Pass, ...] = (
    Pass(
        name="strip_linkml_ranges",
        kind=PassKind.WOT_SHAPING,
        reason="Removes the three rdfs:range linkml:Any triples in jsonschema (enum, const, default); nothing in the "
        "other modules. Its _demote_to_datatype step changes nothing on current schemas.",
        apply=_strip_linkml_ranges,
    ),
    Pass(
        name="add_domain_includes",
        kind=PassKind.UPSTREAM_GAP,
        reason="gen-owl cannot emit schema:domainIncludes for properties used by several classes.",
        apply=_add_domain_includes,
    ),
)

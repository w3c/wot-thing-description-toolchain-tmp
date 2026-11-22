"""Post-process gen-owl TTL into per-module OWL vocabulary files."""

from __future__ import annotations

from pathlib import Path

from linkml_runtime.linkml_model.meta import SchemaDefinition
from linkml_runtime.utils.schemaview import SchemaView
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, VANN
from rdflib.plugin import register
from rdflib.serializer import Serializer
from rdflib.term import Node

from ..schema_utils import get_schema as _get_schema
from . import resolve_prefix_namespace

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
    sv = SchemaView(str(schema_dir / schema_file), merge_imports=False)
    if sv_merged is None:
        sv_merged = SchemaView(str(schema_dir / schema_file), merge_imports=True)
    ns = _module_namespace(sv)
    onto_iri = _ontology_iri(sv)

    _strip_foreign_subjects(g, ns, onto_iri)
    _strip_linkml_ranges(g)
    _fix_subproperty_literals(g, sv_merged)
    _strip_orphan_blank_nodes(g)
    _strip_empty_blank_node_restrictions(g)
    _add_domain_includes(g, sv_merged)
    _add_lang_tags(g)

    _add_ontology_header(g, sv, ns, onto_iri)

    g.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    ttl = g.serialize(format="wot-turtle")
    (output_dir / output_file).write_text(ttl, encoding="utf-8")


def _module_namespace(sv: SchemaView) -> str:
    dp = _get_schema(sv).default_prefix
    assert dp is not None
    return resolve_prefix_namespace(sv, dp)


def _ontology_iri(sv: SchemaView) -> URIRef:
    return URIRef(_get_schema(sv).id)


def _strip_foreign_subjects(g: Graph, local_ns: str, onto_iri: URIRef) -> None:
    """Remove subjects outside this module's namespace (includes linkml: subjects)."""
    onto_str = str(onto_iri)
    to_remove = [
        s for s in set(g.subjects()) if isinstance(s, URIRef) and not str(s).startswith(local_ns) and str(s) != onto_str
    ]
    for s in to_remove:
        for triple in list(g.triples((s, None, None))):
            g.remove(triple)


def _strip_empty_blank_node_restrictions(g: Graph) -> None:
    for s, p, o in list(g.triples((None, RDFS.subClassOf, None))):
        if not isinstance(o, BNode):
            continue
        if not list(g.triples((o, None, None))):
            g.remove((s, p, o))


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


def _remove_rdf_list(g: Graph, node: Node | None) -> None:
    """Walk and remove an RDF list starting at node."""
    while node and node != RDF.nil:
        next_nodes = list(g.objects(node, RDF.rest))
        for t in list(g.triples((node, None, None))):
            g.remove(t)
        node = next_nodes[0] if next_nodes else None


def _strip_orphan_blank_nodes(g: Graph) -> None:
    """Remove blank nodes unreferenced as object."""
    all_objects = set(g.objects())
    to_remove = [s for s in set(g.subjects()) if isinstance(s, BNode) and s not in all_objects]
    for s in to_remove:
        _remove_rdf_list(g, s)
        for triple in list(g.triples((s, None, None))):
            g.remove(triple)


def _fix_subproperty_literals(g: Graph, sv: SchemaView) -> None:
    """Convert rdfs:subPropertyOf Literal objects (gen-owl bug) to URIRef."""
    for s, _, o in list(g.triples((None, RDFS.subPropertyOf, None))):
        if not isinstance(o, Literal):
            continue
        expanded = sv.expand_curie(str(o))
        if expanded and expanded != str(o):
            g.remove((s, RDFS.subPropertyOf, o))
            g.add((s, RDFS.subPropertyOf, URIRef(expanded)))


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


def _add_lang_tags(g: Graph, lang: str = "en") -> None:
    """Add @en lang tag to plain-string literals on description/label predicates."""
    _TAGGED_PREDICATES = (SKOS.definition, RDFS.comment, RDFS.label)
    for pred in _TAGGED_PREDICATES:
        for s, _, o in list(g.triples((None, pred, None))):
            if isinstance(o, Literal) and o.language is None and o.datatype is None:
                g.remove((s, pred, o))
                g.add((s, pred, Literal(str(o), lang=lang)))


def _add_ontology_header(g: Graph, sv: SchemaView, ns: str, onto_iri: URIRef) -> None:
    schema = _get_schema(sv)

    g.add((onto_iri, RDF.type, OWL.Ontology))
    g.remove((onto_iri, RDFS.label, None))
    if schema.title:
        g.add((onto_iri, DCTERMS.title, Literal(f"{schema.title} Ontology", lang="en")))
        g.add((onto_iri, RDFS.label, Literal(schema.title, lang="en")))
    g.remove((onto_iri, RDFS.comment, None))
    if schema.title:
        owl_comment = f"Ontology for the W3C Web of Things {schema.title} vocabulary."
        g.add((onto_iri, RDFS.comment, Literal(owl_comment, lang="en")))
    g.add((onto_iri, VANN.preferredNamespacePrefix, Literal(schema.default_prefix)))
    g.add((onto_iri, VANN.preferredNamespaceUri, Literal(ns)))
    if schema.version:
        g.add((onto_iri, OWL.versionInfo, Literal(schema.version)))
    if schema.license:
        g.add((onto_iri, DCTERMS.license, URIRef(schema.license)))
    g.remove((onto_iri, DCTERMS.creator, None))
    if schema.created_by:
        g.add((onto_iri, DCTERMS.creator, URIRef(schema.created_by)))
    for contributor in schema.contributors or []:
        g.add((onto_iri, DCTERMS.contributor, URIRef(str(contributor))))

    publisher = _publisher_node(g, schema)
    if publisher is not None:
        g.add((onto_iri, DCTERMS.publisher, publisher))


def _publisher_node(g: Graph, schema: SchemaDefinition) -> BNode | None:
    annotation = (schema.annotations or {}).get("dcterms:publisher")
    if annotation is None:
        return None
    value = annotation.value
    try:
        org_type = value["@type"]
        name = value["schema:name"]
        url = value["schema:url"]
    except KeyError, TypeError:
        return None
    if org_type != "schema:Organization" or not name or not url:
        return None
    node = BNode()
    g.add((node, RDF.type, SCHEMA.Organization))
    g.add((node, SCHEMA.name, Literal(name)))
    g.add((node, SCHEMA.url, URIRef(url)))
    return node

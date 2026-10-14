"""Post-process gen-owl TTL into per-module OWL vocabulary files."""
from __future__ import annotations

from pathlib import Path
from typing import cast

from linkml_runtime.linkml_model.meta import (
    EnumDefinition,
    Prefix,
    SchemaDefinition,
)
from linkml_runtime.utils.schemaview import SchemaView
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, VANN, XSD

SCHEMA = Namespace("http://schema.org/")
LINKML = Namespace("https://w3id.org/linkml/")
LINKML_NS = str(LINKML)

_Enums = dict[str, EnumDefinition]
_Prefixes = dict[str, Prefix]


def _get_schema(sv: SchemaView) -> SchemaDefinition:
    schema = sv.schema
    assert schema is not None
    return schema


def postprocess_owl(
    module_ttl: str,
    schema_file: str,
    output_file: str,
    schema_dir: Path,
    output_dir: Path,
) -> None:
    """Clean gen-owl output and write per-module OWL vocabulary file."""
    g = Graph()
    g.parse(data=module_ttl, format="turtle")

    sv = SchemaView(str(schema_dir / schema_file), merge_imports=False)
    sv_merged = SchemaView(str(schema_dir / schema_file), merge_imports=True)
    ns = _module_namespace(sv)
    onto_iri = _ontology_iri(sv)

    _strip_foreign_subjects(g, ns, onto_iri)
    _strip_linkml_ranges(g)
    _fix_in_scheme(g, onto_iri)
    _fix_subproperty_literals(g, sv_merged)
    _fix_uri_annotation_literals(g)
    _clean_exact_match(g)
    _clean_enum_artifacts(g)
    _convert_enum_subclasses_to_individuals(g, sv_merged)
    _fix_aliased_labels(g)
    _strip_orphan_blank_nodes(g)
    _strip_empty_blank_node_restrictions(g)

    _add_ontology_header(g, sv, ns, onto_iri)

    output_dir.mkdir(parents=True, exist_ok=True)
    ttl = g.serialize(format="turtle")
    (output_dir / output_file).write_text(ttl, encoding="utf-8")


def _module_namespace(sv: SchemaView) -> str:
    schema = _get_schema(sv)
    dp = schema.default_prefix
    assert dp is not None
    prefix = cast(Prefix, cast(_Prefixes, schema.prefixes)[dp])
    ns = str(prefix.prefix_reference)
    if not ns.endswith(("#", "/")):
        ns += "#"
    return ns


def _ontology_iri(sv: SchemaView) -> URIRef:
    return URIRef(_get_schema(sv).id)


def _strip_foreign_subjects(g: Graph, local_ns: str, onto_iri: URIRef) -> None:
    """Remove subjects outside this module's namespace (includes linkml: subjects)."""
    onto_str = str(onto_iri)
    to_remove = [
        s for s in set(g.subjects())
        if isinstance(s, URIRef)
        and not str(s).startswith(local_ns)
        and str(s) != onto_str
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


def _demote_to_datatype(g: Graph, props: set[URIRef]) -> None:
    """Demote ObjectProperty→DatatypeProperty for props that lost their only range."""
    for prop in props:
        if list(g.objects(prop, RDFS.range)):
            continue
        if (prop, RDF.type, OWL.ObjectProperty) in g:
            g.remove((prop, RDF.type, OWL.ObjectProperty))
            g.add((prop, RDF.type, OWL.DatatypeProperty))


def _strip_linkml_ranges(g: Graph) -> None:
    """Remove linkml: ranges; demote to DatatypeProperty if no range remains."""
    linkml_ranged_props: set[URIRef] = set()
    for s, _, o in list(g.triples((None, RDFS.range, None))):
        if isinstance(o, URIRef) and str(o).startswith(LINKML_NS):
            linkml_ranged_props.add(s)
            g.remove((s, RDFS.range, o))
    _demote_to_datatype(g, linkml_ranged_props)


def _fix_in_scheme(g: Graph, onto_iri: URIRef) -> None:
    for s, p, o in list(g.triples((None, SKOS.inScheme, None))):
        g.remove((s, p, o))
        g.add((s, SKOS.inScheme, onto_iri))


def _clean_enum_artifacts(g: Graph) -> None:
    """Remove gen-owl enum artifacts (double-# PVs, unionOf, NamedIndividual)."""
    pv_subjects = {
        s for s in g.subjects()
        if isinstance(s, URIRef) and s.count("#") > 1
    }
    for s in pv_subjects:
        for triple in list(g.triples((s, None, None))):
            g.remove(triple)

    for triple in list(g.triples((None, LINKML.permissible_values, None))):
        g.remove(triple)

    for pred in (OWL.unionOf, OWL.oneOf):
        for s, _, bn in list(g.triples((None, pred, None))):
            if not isinstance(s, URIRef):
                continue
            g.remove((s, pred, bn))
            _remove_rdf_list(g, bn)

    for s, _, _ in list(g.triples((None, RDF.type, OWL.NamedIndividual))):
        g.remove((s, RDF.type, OWL.NamedIndividual))


def _remove_rdf_list(g: Graph, node: BNode | URIRef | None) -> None:
    """Walk and remove an RDF list starting at node."""
    while node and node != RDF.nil:
        next_nodes = list(g.objects(node, RDF.rest))
        for t in list(g.triples((node, None, None))):
            g.remove(t)
        node = cast(BNode | URIRef | None, next_nodes[0] if next_nodes else None)


def _convert_enum_subclasses_to_individuals(g: Graph, sv: SchemaView) -> None:
    """Convert PV subclasses to rdf:type individuals (upstream pattern)."""
    schema = _get_schema(sv)
    for edef in cast(_Enums, schema.enums).values():
        if not edef.enum_uri:
            continue
        enum_iri = URIRef(sv.expand_curie(edef.enum_uri))
        for s, _, _ in list(g.triples((None, RDFS.subClassOf, enum_iri))):
            if not isinstance(s, URIRef):
                continue
            g.remove((s, RDFS.subClassOf, enum_iri))
            g.remove((s, RDF.type, OWL.Class))
            g.add((s, RDF.type, enum_iri))


def _strip_orphan_blank_nodes(g: Graph) -> None:
    """Remove blank nodes unreferenced as object."""
    all_objects = set(g.objects())
    to_remove = [
        s for s in set(g.subjects())
        if isinstance(s, BNode) and s not in all_objects
    ]
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


def _fix_uri_annotation_literals(g: Graph) -> None:
    """Convert Literal objects to URIRef for predicates that expect resources."""
    _URI_PREDICATES = (RDFS.isDefinedBy, RDFS.seeAlso, RDFS.subClassOf)
    for pred in _URI_PREDICATES:
        for s, _, o in list(g.triples((None, pred, None))):
            if not isinstance(o, Literal):
                continue
            val = str(o)
            if val.startswith(("http://", "https://", "urn:")):
                g.remove((s, pred, o))
                g.add((s, pred, URIRef(val)))


def _fix_aliased_labels(g: Graph) -> None:
    """When skos:prefLabel exists (from LinkML alias), use it as rdfs:label."""
    for s, _, pref_label in list(g.triples((None, SKOS.prefLabel, None))):
        for _, _, old_label in list(g.triples((s, RDFS.label, None))):
            g.remove((s, RDFS.label, old_label))
        lang = pref_label.language if isinstance(pref_label, Literal) else None
        g.add((s, RDFS.label, Literal(str(pref_label), lang=lang)))
        g.remove((s, SKOS.prefLabel, pref_label))


def _clean_exact_match(g: Graph) -> None:
    for s, p, o in list(g.triples((None, SKOS.exactMatch, None))):
        g.remove((s, p, o))


def _add_ontology_header(g: Graph, sv: SchemaView, ns: str, onto_iri: URIRef) -> None:
    schema = _get_schema(sv)

    g.add((onto_iri, RDF.type, OWL.Ontology))
    if schema.title:
        g.add((onto_iri, DCTERMS.title, Literal(schema.title, lang="en")))
    if schema.description:
        g.add((onto_iri, RDFS.comment, Literal(schema.description, lang="en")))
    g.add((onto_iri, VANN.preferredNamespacePrefix, Literal(schema.default_prefix)))
    g.add((onto_iri, VANN.preferredNamespaceUri, Literal(ns)))
    if schema.version:
        g.add((onto_iri, OWL.versionInfo, Literal(schema.version)))
    if schema.license:
        g.add((onto_iri, DCTERMS.license, URIRef(schema.license)))
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
    except (KeyError, TypeError):
        return None
    if org_type != "schema:Organization" or not name or not url:
        return None
    node = BNode()
    g.add((node, RDF.type, SCHEMA.Organization))
    g.add((node, SCHEMA.name, Literal(name)))
    g.add((node, SCHEMA.url, URIRef(url)))
    return node

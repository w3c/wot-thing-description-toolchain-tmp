"""Post-process gen-owl TTL output into per-module OWL vocabulary files.

Takes per-module TTL produced by gen-owl (via owl_preprocessor) and:
- Strips linkml: namespace subjects (internal model artefacts)
- Strips linkml: ranges (linkml:Any, linkml:uri)
- Fixes skos:inScheme to point to the actual module ontology IRI
- Removes self-referential and backward skos:exactMatch triples
- Removes gen-owl enum artifacts (fragment IRIs, permissible_values triples, unionOf)
- Removes empty blank-node subClassOf restrictions
- Adds owl:Ontology headers per module (from schema metadata)
"""
from __future__ import annotations

from pathlib import Path

from linkml_runtime.linkml_model.meta import SchemaDefinition
from linkml_runtime.utils.schemaview import SchemaView
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, VANN, XSD

SCHEMA = Namespace("http://schema.org/")
LINKML = Namespace("https://w3id.org/linkml/")
LINKML_NS = str(LINKML)


def postprocess_owl(
    module_ttl: str,
    schema_file: str,
    output_file: str,
    schema_dir: Path,
    output_dir: Path,
) -> None:
    """Clean and write a single per-module OWL vocabulary file.

    Args:
        module_ttl: Turtle string from gen-owl for this module.
        schema_file: Schema YAML filename (e.g. 'thing_description.yaml').
        output_file: Output TTL filename (e.g. 'td.ttl').
        schema_dir: Directory containing schema YAML files.
        output_dir: Directory to write output TTL files.
    """
    g = Graph()
    g.parse(data=module_ttl, format="turtle")

    sv = SchemaView(str(schema_dir / schema_file), merge_imports=False)
    sv_merged = SchemaView(str(schema_dir / schema_file), merge_imports=True)

    _strip_linkml_subjects(g)
    _strip_foreign_subjects(g, sv)
    _strip_linkml_ranges(g)
    _fix_in_scheme(g, sv)
    _clean_exact_match(g)
    _clean_enum_artifacts(g)
    _convert_enum_subclasses_to_individuals(g, sv_merged)
    _strip_orphan_blank_nodes(g)
    _strip_empty_blank_node_restrictions(g)
    _strip_implicit_enum_classes(g, sv)

    _add_ontology_header(g, sv)

    output_dir.mkdir(parents=True, exist_ok=True)
    ttl = g.serialize(format="turtle")
    (output_dir / output_file).write_text(ttl, encoding="utf-8")


def _module_namespace(sv: SchemaView) -> str:
    prefix = sv.schema.prefixes[sv.schema.default_prefix]
    ns = str(prefix.prefix_reference)
    if not ns.endswith(("#", "/")):
        ns += "#"
    return ns


def _ontology_iri(sv: SchemaView) -> URIRef:
    return URIRef(sv.schema.id)


def _strip_linkml_subjects(g: Graph) -> None:
    to_remove = [s for s in set(g.subjects()) if str(s).startswith(LINKML_NS)]
    for s in to_remove:
        for triple in list(g.triples((s, None, None))):
            g.remove(triple)


def _strip_foreign_subjects(g: Graph, sv: SchemaView) -> None:
    """Remove triples for classes/properties not in this module's namespace.

    gen-owl with merge_imports=True emits definitions for all merged classes
    (needed for range resolution). Strip any subject whose IRI is outside the
    local module namespace so only local vocabulary appears in the output.
    """
    local_ns = _module_namespace(sv)
    onto_iri = str(_ontology_iri(sv))
    to_remove = [
        s for s in set(g.subjects())
        if isinstance(s, URIRef)
        and not str(s).startswith(local_ns)
        and str(s) != onto_iri
    ]
    for s in to_remove:
        for triple in list(g.triples((s, None, None))):
            g.remove(triple)


def _strip_empty_blank_node_restrictions(g: Graph) -> None:
    from rdflib import BNode as RDFBNode
    for s, p, o in list(g.triples((None, RDFS.subClassOf, None))):
        if not isinstance(o, RDFBNode):
            continue
        if not list(g.triples((o, None, None))):
            g.remove((s, p, o))


def _strip_linkml_ranges(g: Graph) -> None:
    """Remove rdfs:range triples where the range is a linkml: IRI.

    Demotes ObjectProperty to DatatypeProperty when the linkml range was the only one.
    """
    linkml_ranged_props: set[URIRef] = set()
    for s, _, o in list(g.triples((None, RDFS.range, None))):
        if isinstance(o, URIRef) and str(o).startswith(LINKML_NS):
            linkml_ranged_props.add(s)
            g.remove((s, RDFS.range, o))

    for prop in linkml_ranged_props:
        if list(g.objects(prop, RDFS.range)):
            continue
        if (prop, RDF.type, OWL.ObjectProperty) in g:
            g.remove((prop, RDF.type, OWL.ObjectProperty))
            g.add((prop, RDF.type, OWL.DatatypeProperty))


def _fix_in_scheme(g: Graph, sv: SchemaView) -> None:
    onto_iri = _ontology_iri(sv)
    for s, p, o in list(g.triples((None, SKOS.inScheme, None))):
        g.remove((s, p, o))
        g.add((s, SKOS.inScheme, onto_iri))


def _clean_enum_artifacts(g: Graph) -> None:
    """Remove gen-owl enum artifacts not present in the upstream WoT ontology."""
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


def _remove_rdf_list(g: Graph, node) -> None:
    """Walk and remove an RDF list starting at node."""
    while node and node != RDF.nil:
        next_nodes = list(g.objects(node, RDF.rest))
        for t in list(g.triples((node, None, None))):
            g.remove(t)
        node = next_nodes[0] if next_nodes else None


def _convert_enum_subclasses_to_individuals(g: Graph, sv: SchemaView) -> None:
    """Convert PV subclasses to named individuals for enums with enum_uri.

    gen-owl emits PVs as owl:Class + rdfs:subClassOf EnumClass.
    Upstream WoT ontology expects rdf:type EnumClass (individuals, not classes).
    """
    ns = _module_namespace(sv)
    for edef in sv.schema.enums.values():
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
    """Remove blank nodes not referenced as object by any other triple."""
    from rdflib import BNode as RDFBNode
    all_objects = set(g.objects())
    to_remove = [
        s for s in set(g.subjects())
        if isinstance(s, RDFBNode) and s not in all_objects
    ]
    for s in to_remove:
        _remove_rdf_list(g, s)
        for triple in list(g.triples((s, None, None))):
            g.remove(triple)


def _strip_implicit_enum_classes(g: Graph, sv: SchemaView) -> None:
    """Remove OWL classes generated from enums without an explicit enum_uri.

    Even after per-module processing, gen-owl may emit a class for enums that
    still lack enum_uri after _assign_enum_uris (e.g. enums with no matching
    sub-schema namespace). Strip those and demote any affected ObjectProperties.
    """
    from linkml_runtime.utils.formatutils import camelcase

    ns = _module_namespace(sv)
    implicit_iris: set[URIRef] = set()
    for ename, edef in sv.schema.enums.items():
        if edef.enum_uri:
            continue
        implicit_iris.add(URIRef(f"{ns}{camelcase(ename)}"))

    enum_ranged_props: set[URIRef] = set()
    for iri in implicit_iris:
        for triple in list(g.triples((iri, None, None))):
            g.remove(triple)
        for s, _, _ in list(g.triples((None, RDFS.range, iri))):
            enum_ranged_props.add(s)
            g.remove((s, RDFS.range, iri))

    for prop in enum_ranged_props:
        if list(g.objects(prop, RDFS.range)):
            continue
        if (prop, RDF.type, OWL.ObjectProperty) in g:
            g.remove((prop, RDF.type, OWL.ObjectProperty))
            g.add((prop, RDF.type, OWL.DatatypeProperty))


def _clean_exact_match(g: Graph) -> None:
    for s, p, o in list(g.triples((None, SKOS.exactMatch, None))):
        g.remove((s, p, o))


def _add_ontology_header(g: Graph, sv: SchemaView) -> None:
    schema = sv.schema
    onto_iri = _ontology_iri(sv)
    ns = _module_namespace(sv)

    # rdflib's default schema: prefix maps to https://schema.org/; rebind to http://
    g.bind("schema", SCHEMA, replace=True)

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


def _publisher_node(g: Graph, schema: SchemaDefinition) -> URIRef | None:
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
    from rdflib import BNode
    node = BNode()
    g.add((node, RDF.type, SCHEMA.Organization))
    g.add((node, SCHEMA.name, Literal(name)))
    g.add((node, SCHEMA.url, URIRef(url)))
    return node

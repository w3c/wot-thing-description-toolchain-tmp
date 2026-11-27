"""The owl:Ontology header of a published WoT vocabulary."""

from linkml_runtime.linkml_model.meta import SchemaDefinition
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, VANN

from ...errors import SchemaError

SCHEMA = Namespace("http://schema.org/")


def add_ontology_header(g: Graph, schema: SchemaDefinition, ontology: URIRef, namespace: str) -> None:
    """Describe ``ontology`` in ``g`` with the metadata of ``schema``; ``namespace`` is its vocabulary namespace."""
    g.add((ontology, RDF.type, OWL.Ontology))
    if schema.title:
        _add_title(g, ontology, schema.title)
    if schema.description:
        g.add((ontology, RDFS.comment, Literal(" ".join(schema.description.split()), lang="en")))
    g.add((ontology, VANN.preferredNamespacePrefix, Literal(schema.default_prefix)))
    g.add((ontology, VANN.preferredNamespaceUri, Literal(namespace)))
    if schema.version:
        g.add((ontology, OWL.versionInfo, Literal(schema.version)))
    if schema.license:
        g.add((ontology, DCTERMS.license, URIRef(schema.license)))
    if schema.created_by:
        g.add((ontology, DCTERMS.creator, URIRef(schema.created_by)))
    publisher = _publisher_node(g, schema)
    if publisher is not None:
        g.add((ontology, DCTERMS.publisher, publisher))
    _add_iri_annotations(g, schema, ontology)


def _add_iri_annotations(g: Graph, schema: SchemaDefinition, ontology: URIRef) -> None:
    """Add each schema annotation whose key is a CURIE and whose value is an IRI, e.g. ``owl:priorVersion``."""
    for key, annotation in (schema.annotations or {}).items():
        prefix, _, local_name = key.partition(":")
        value = annotation.value
        if prefix not in schema.prefixes or not isinstance(value, str):
            continue
        if "://" not in value:
            raise SchemaError(f"{schema.source_file or schema.name}: annotation {key!r} must be an IRI, got {value!r}.")
        g.add((ontology, URIRef(schema.prefixes[prefix].prefix_reference + local_name), URIRef(value)))


def _add_title(g: Graph, ontology: URIRef, title: str) -> None:
    g.add((ontology, DCTERMS.title, Literal(f"{title} Ontology", lang="en")))
    g.add((ontology, RDFS.label, Literal(title, lang="en")))


def _publisher_node(g: Graph, schema: SchemaDefinition) -> BNode | None:
    """Return a schema:Organization node for the schema's publisher annotation, or None if it declares none."""
    annotation = (schema.annotations or {}).get("dcterms:publisher")
    if annotation is None:
        return None
    value = annotation.value
    try:
        org_type = value["@type"]
        name = value["schema:name"]
        url = value["schema:url"]
    except (KeyError, TypeError) as exc:
        raise SchemaError(_malformed_publisher(schema)) from exc
    if org_type != "schema:Organization" or not name or not url:
        raise SchemaError(_malformed_publisher(schema))
    node = BNode()
    g.add((node, RDF.type, SCHEMA.Organization))
    g.add((node, SCHEMA.name, Literal(name)))
    g.add((node, SCHEMA.url, URIRef(url)))
    return node


def _malformed_publisher(schema: SchemaDefinition) -> str:
    return (
        f"{schema.source_file or schema.name}: annotation 'dcterms:publisher' must be a mapping with "
        "'@type: schema:Organization' and non-empty 'schema:name' and 'schema:url'."
    )

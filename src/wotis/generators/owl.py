"""Generate readable, module-scoped OWL vocabulary files from LinkML schemas."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from linkml_runtime.linkml_model.meta import ClassDefinition, SchemaDefinition, SlotDefinition
from linkml_runtime.utils.schemaview import SchemaView
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, XSD
from rdflib.namespace import NamespaceManager


SCHEMA_DIR = Path("resources/schemas")
MODULES = (
    ("thing_description.yaml", "td.ttl"),
    ("thing_model.yaml", "tm.ttl"),
    ("hypermedia.yaml", "hctl.ttl"),
    ("wot_security.yaml", "wotsec.ttl"),
    ("jsonschema.yaml", "jsonschema.ttl"),
)
SCHEMA = Namespace("http://schema.org/")
VANN = Namespace("http://purl.org/vocab/vann/")


@dataclass
class PropertyDefinition:
    """The vocabulary facts collected for one property IRI."""

    iri: URIRef
    description: str | None = None
    domains: set[URIRef] = field(default_factory=set)
    ranges: set[URIRef] = field(default_factory=set)
    is_object_property: bool = False


def generate_owl_vocabularies(output_dir: Path, schema_dir: Path = SCHEMA_DIR) -> None:
    """Write one OWL vocabulary file for every WoT LinkML schema module."""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "ontology.owl.ttl").unlink(missing_ok=True)
    for schema_file, output_file in MODULES:
        schema_path = schema_dir / schema_file
        local_view = SchemaView(schema_path, merge_imports=False)
        merged_view = SchemaView(schema_path, merge_imports=True)
        (output_dir / output_file).write_text(
            _serialize_module(local_view.schema, merged_view), encoding="utf-8"
        )


def _serialize_module(local_schema: SchemaDefinition, merged_view: SchemaView) -> str:
    namespace = _module_namespace(local_schema)
    manager = _namespace_manager(local_schema)
    ontology_iri = URIRef(local_schema.id)
    classes = _local_classes(local_schema, merged_view, namespace)
    properties = _local_properties(local_schema, merged_view, namespace, classes)
    blocks = [_prefixes(local_schema, manager), _ontology_block(local_schema, ontology_iri, namespace, manager)]
    blocks.extend(
        _class_block(class_iri, class_def, _parent_iri(class_def, merged_view), ontology_iri, manager)
        for class_iri, class_def in classes.items()
    )
    blocks.extend(_property_block(property_def, ontology_iri, manager) for property_def in properties.values())
    return "\n\n".join(block for block in blocks if block) + "\n"


def _module_namespace(schema: SchemaDefinition) -> str:
    prefix = schema.prefixes[schema.default_prefix]
    return str(prefix.prefix_reference)


def _namespace_manager(schema: SchemaDefinition) -> NamespaceManager:
    manager = NamespaceManager(Graph())
    manager.bind(schema.default_prefix, Namespace(_module_namespace(schema)), replace=True)
    for prefix, namespace in (("dcterms", DCTERMS), ("owl", OWL), ("rdf", RDF), ("rdfs", RDFS),
                              ("schema", SCHEMA), ("skos", SKOS), ("vann", VANN), ("xsd", XSD)):
        manager.bind(prefix, namespace, replace=True)
    return manager


def _prefixes(schema: SchemaDefinition, manager: NamespaceManager) -> str:
    prefixes = [
        (str(schema.default_prefix), Namespace(_module_namespace(schema))),
        ("dcterms", DCTERMS),
        ("owl", OWL),
        ("rdf", RDF),
        ("rdfs", RDFS),
        ("schema", SCHEMA),
        ("skos", SKOS),
        ("vann", VANN),
        ("xsd", XSD),
    ]
    return "\n".join(f"@prefix {prefix}: <{namespace}> ." for prefix, namespace in prefixes)


def _local_classes(
    local_schema: SchemaDefinition, merged_view: SchemaView, namespace: str
) -> dict[URIRef, ClassDefinition]:
    classes: dict[URIRef, ClassDefinition] = {}
    for class_def in local_schema.classes.values():
        iri = _class_iri(class_def, merged_view)
        if iri is not None and str(iri).startswith(namespace):
            classes[iri] = class_def
    return dict(sorted(classes.items(), key=lambda item: str(item[0])))


def _local_properties(
    local_schema: SchemaDefinition,
    merged_view: SchemaView,
    namespace: str,
    classes: dict[URIRef, ClassDefinition],
) -> dict[URIRef, PropertyDefinition]:
    properties: dict[URIRef, PropertyDefinition] = {}
    for slot_def in local_schema.slots.values():
        _record_property(properties, slot_def, None, merged_view, namespace)
    for class_def in local_schema.classes.values():
        class_iri = _class_iri(class_def, merged_view)
        domain = class_iri if class_iri in classes else None
        for slot_def in _class_slots(class_def, merged_view, set(local_schema.slots)):
            _record_property(properties, slot_def, domain, merged_view, namespace)
    return dict(sorted(properties.items(), key=lambda item: str(item[0])))


def _class_slots(
    class_def: ClassDefinition, schema_view: SchemaView, local_slot_names: set[str]
) -> Iterable[SlotDefinition]:
    yield from (class_def.attributes or {}).values()
    for slot_name in class_def.slots or []:
        if slot_name not in local_slot_names:
            continue
        try:
            slot_def = schema_view.induced_slot(slot_name, class_def.name)
        except ValueError:
            continue
        if slot_def is not None and slot_def.slot_uri:
            yield slot_def
    for slot_def in (class_def.slot_usage or {}).values():
        if slot_def.slot_uri:
            yield slot_def


def _record_property(
    properties: dict[URIRef, PropertyDefinition],
    slot_def: SlotDefinition,
    domain: URIRef | None,
    schema_view: SchemaView,
    namespace: str,
) -> None:
    if not slot_def.slot_uri or (slot_def.alias or slot_def.name).startswith("@"):
        return
    iri = _slot_iri(slot_def, schema_view, namespace)
    if iri is None or not str(iri).startswith(namespace):
        return
    property_def = properties.setdefault(iri, PropertyDefinition(iri=iri))
    property_def.description = property_def.description or slot_def.description
    if domain is not None:
        property_def.domains.add(domain)
    range_iri, is_object_property = _range_iri(slot_def.range, schema_view)
    if range_iri is not None:
        property_def.ranges.add(range_iri)
    property_def.is_object_property = property_def.is_object_property or is_object_property


def _class_iri(class_def: ClassDefinition, schema_view: SchemaView) -> URIRef | None:
    if not class_def.class_uri:
        return None
    return URIRef(schema_view.expand_curie(class_def.class_uri))


def _slot_iri(slot_def: SlotDefinition, schema_view: SchemaView, namespace: str) -> URIRef | None:
    if slot_def.slot_uri:
        return URIRef(schema_view.expand_curie(slot_def.slot_uri))
    return URIRef(f"{namespace}{slot_def.name}")


def _range_iri(range_name: str | None, schema_view: SchemaView) -> tuple[URIRef | None, bool]:
    if not range_name:
        return None, False
    class_def = schema_view.get_class(range_name)
    if class_def and class_def.class_uri:
        return _class_iri(class_def, schema_view), True
    type_def = schema_view.get_type(range_name)
    if type_def and type_def.uri:
        return URIRef(schema_view.expand_curie(type_def.uri)), False
    return None, False


def _ontology_block(
    schema: SchemaDefinition, ontology_iri: URIRef, namespace: str, manager: NamespaceManager
) -> str:
    predicates = [
        (RDF.type, OWL.Ontology),
        (DCTERMS.title, Literal(schema.title, lang="en")),
        (RDFS.comment, Literal(schema.description, lang="en")),
        (VANN.preferredNamespacePrefix, Literal(schema.default_prefix)),
        (VANN.preferredNamespaceUri, Literal(namespace)),
        (OWL.versionInfo, Literal(schema.version)),
        (DCTERMS.license, Literal(schema.license)),
        (DCTERMS.creator, URIRef(schema.created_by)),
    ]
    predicates.extend((DCTERMS.contributor, URIRef(contributor)) for contributor in schema.contributors or [])
    publisher = _publisher(schema, manager)
    if publisher:
        predicates.append((DCTERMS.publisher, publisher))
    return _turtle_block(ontology_iri, predicates, manager)


def _publisher(schema: SchemaDefinition, manager: NamespaceManager) -> str | None:
    annotation = (schema.annotations or {}).get("dcterms:publisher")
    if annotation is None:
        return None
    value = annotation.value
    try:
        organization_type = value["@type"]
        name = value["schema:name"]
        url = value["schema:url"]
    except KeyError:
        return None
    if organization_type != "schema:Organization" or not name or not url:
        return None
    return f"[ a schema:Organization ; schema:name {Literal(name).n3()} ; schema:url {_iri(URIRef(url), manager)} ]"


def _parent_iri(class_def: ClassDefinition, schema_view: SchemaView) -> URIRef | None:
    if not class_def.is_a:
        return None
    parent = schema_view.get_class(class_def.is_a)
    return _class_iri(parent, schema_view) if parent else None


def _class_block(
    class_iri: URIRef,
    class_def: ClassDefinition,
    parent_iri: URIRef | None,
    ontology_iri: URIRef,
    manager: NamespaceManager,
) -> str:
    predicates: list[tuple[URIRef, URIRef | Literal | str]] = [
        (RDF.type, OWL.Class),
        (RDFS.label, Literal(_local_name(class_iri))),
        (RDFS.comment, Literal(class_def.description, lang="en")),
    ]
    if parent_iri is not None:
        predicates.append((RDFS.subClassOf, parent_iri))
    predicates.extend(((RDFS.isDefinedBy, ontology_iri), (SKOS.inScheme, ontology_iri)))
    return _turtle_block(class_iri, predicates, manager)


def _property_block(property_def: PropertyDefinition, ontology_iri: URIRef, manager: NamespaceManager) -> str:
    property_type = OWL.ObjectProperty if property_def.is_object_property else OWL.DatatypeProperty
    predicates: list[tuple[URIRef, URIRef | Literal | str]] = [
        (RDF.type, property_type),
        (RDFS.label, Literal(_local_name(property_def.iri))),
    ]
    if property_def.description:
        predicates.append((RDFS.comment, Literal(property_def.description, lang="en")))
    predicates.extend((SCHEMA.domainIncludes, domain) for domain in sorted(property_def.domains, key=str))
    predicates.extend((SCHEMA.rangeIncludes, range_iri) for range_iri in sorted(property_def.ranges, key=str))
    predicates.extend(((RDFS.isDefinedBy, ontology_iri), (SKOS.inScheme, ontology_iri)))
    return _turtle_block(property_def.iri, predicates, manager)


def _turtle_block(
    subject: URIRef, predicates: list[tuple[URIRef, URIRef | Literal | str]], manager: NamespaceManager
) -> str:
    lines = [f"{_iri(subject, manager)}"]
    for index, (predicate, obj) in enumerate(predicates):
        terminal = " ." if index == len(predicates) - 1 else " ;"
        lines.append(f"    {_iri(predicate, manager)} {_object(obj, manager)}{terminal}")
    return "\n".join(lines)


def _iri(iri: URIRef, manager: NamespaceManager) -> str:
    try:
        prefix, _, local_name = manager.compute_qname(str(iri), generate=False)
    except (KeyError, ValueError):
        return f"<{iri}>"
    return f"{prefix}:{local_name}"


def _object(value: URIRef | Literal | str, manager: NamespaceManager) -> str:
    if isinstance(value, URIRef):
        return _iri(value, manager)
    if isinstance(value, Literal):
        return value.n3(manager)
    if isinstance(value, str):
        return value
    raise TypeError(f"Unsupported Turtle object: {value!r}")


def _local_name(iri: URIRef | None) -> str:
    if iri is None:
        return ""
    return str(iri).rsplit("#", 1)[-1].rsplit("/", 1)[-1]

"""Generate readable, module-scoped OWL vocabulary files from LinkML schemas."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import yaml

from linkml_runtime.linkml_model.meta import ClassDefinition, EnumDefinition, SchemaDefinition, SlotDefinition
from linkml_runtime.utils.schemaview import SchemaView
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, XSD
from rdflib.namespace import NamespaceManager


SCHEMA_DIR = Path("resources/schemas")
_OWL_CONFIG = Path(__file__).parent / "owl_config.yaml"
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
    is_annotation_property: bool = False
    sub_property_of: URIRef | None = None
    see_also: list[URIRef] = field(default_factory=list)


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
    enums = _local_enums(merged_view, namespace)
    properties = _local_properties(local_schema, merged_view, namespace, classes)
    content_blocks = [_ontology_block(local_schema, ontology_iri, namespace, manager)]
    content_blocks.extend(
        _class_block(class_iri, class_def, _parent_iri(class_def, merged_view), ontology_iri, manager)
        for class_iri, class_def in classes.items()
    )
    for enum_iri, enum_def in enums.items():
        content_blocks.extend(_enum_blocks(enum_iri, enum_def, ontology_iri, merged_view, manager))
    content_blocks.extend(_property_block(property_def, ontology_iri, manager) for property_def in properties.values())
    content = "\n\n".join(block for block in content_blocks if block)
    prefix_block = _prefixes_used(content, manager)
    return prefix_block + "\n\n" + content + "\n"


def _module_namespace(schema: SchemaDefinition) -> str:
    prefix = schema.prefixes[schema.default_prefix]
    return str(prefix.prefix_reference)


def _namespace_manager(schema: SchemaDefinition) -> NamespaceManager:
    manager = NamespaceManager(Graph())
    manager.bind(schema.default_prefix, Namespace(_module_namespace(schema)), replace=True)
    for prefix, namespace in (("dcterms", DCTERMS), ("owl", OWL), ("rdf", RDF), ("rdfs", RDFS),
                              ("schema", SCHEMA), ("skos", SKOS), ("vann", VANN), ("xsd", XSD)):
        manager.bind(prefix, namespace, replace=True)
    for p in schema.prefixes.values():
        manager.bind(p.prefix_prefix, Namespace(str(p.prefix_reference)), override=False)
    return manager


def _canonical_prefixes() -> list[str]:
    return yaml.safe_load(_OWL_CONFIG.read_text())["canonical_prefixes"]


def _prefixes_used(content: str, manager: NamespaceManager) -> str:
    import re
    used_in_content = set(re.findall(r'\b([a-zA-Z][a-zA-Z0-9_]*):', content))
    ns_map = {prefix: str(namespace) for prefix, namespace in manager.namespaces() if prefix}
    wanted = set(_canonical_prefixes()) | used_in_content
    lines = []
    for prefix in sorted(wanted):
        if prefix in ns_map:
            lines.append(f"@prefix {prefix}: <{ns_map[prefix]}> .")
    return "\n".join(lines)


def _local_classes(
    local_schema: SchemaDefinition, merged_view: SchemaView, namespace: str
) -> dict[URIRef, ClassDefinition]:
    classes: dict[URIRef, ClassDefinition] = {}
    for class_def in local_schema.classes.values():
        iri = _class_iri(class_def, merged_view)
        if iri is not None and str(iri).startswith(namespace):
            classes[iri] = class_def
    return dict(sorted(classes.items(), key=lambda item: str(item[0])))


def _local_enums(
    merged_view: SchemaView, namespace: str
) -> dict[URIRef, EnumDefinition]:
    enums: dict[URIRef, EnumDefinition] = {}
    for enum_def in merged_view.all_enums().values():
        if not enum_def.enum_uri:
            continue
        iri = URIRef(merged_view.expand_curie(enum_def.enum_uri))
        if str(iri).startswith(namespace):
            enums[iri] = enum_def
    return dict(sorted(enums.items(), key=lambda item: str(item[0])))


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


def _effective_range(slot_def: SlotDefinition, schema_view: SchemaView) -> str | None:
    raw = schema_view.get_slot(slot_def.name)
    if raw and raw.range:
        return slot_def.range
    if raw:
        branches = raw.exactly_one_of or []
        if branches:
            ranges = {b.range for b in branches if b.range}
            if len(ranges) == 1:
                return ranges.pop()
    return None


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
    if iri is None:
        return
    has_explicit_implements = bool(slot_def.implements)
    if not str(iri).startswith(namespace) and not has_explicit_implements:
        return
    property_def = properties.setdefault(iri, PropertyDefinition(iri=iri))
    property_def.description = property_def.description or slot_def.description
    if domain is not None:
        property_def.domains.add(domain)
    for owl_domain in _annotation_list(slot_def, "owl_domain"):
        domain_class = schema_view.get_class(owl_domain)
        if domain_class:
            domain_iri = _class_iri(domain_class, schema_view)
            if domain_iri:
                property_def.domains.add(domain_iri)
    effective_range = _effective_range(slot_def, schema_view)
    range_iri, is_object_property = _range_iri(effective_range, schema_view)
    if range_iri is not None:
        property_def.ranges.add(range_iri)
    for impl in slot_def.implements or []:
        if impl.endswith("ObjectProperty"):
            is_object_property = True
        elif impl.endswith("DatatypeProperty"):
            is_object_property = False
        elif impl.endswith("AnnotationProperty"):
            property_def.is_annotation_property = True
    property_def.is_object_property = property_def.is_object_property or is_object_property
    if slot_def.is_a and property_def.sub_property_of is None:
        parent = schema_view.get_slot(slot_def.is_a)
        if parent and parent.slot_uri:
            property_def.sub_property_of = URIRef(schema_view.expand_curie(str(parent.slot_uri)))
    for uri in slot_def.see_also or []:
        ref = URIRef(schema_view.expand_curie(uri))
        if ref not in property_def.see_also:
            property_def.see_also.append(ref)


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
    if range_name == "Any":
        return None, True
    class_def = schema_view.get_class(range_name)
    if class_def and class_def.class_uri:
        return _class_iri(class_def, schema_view), True
    type_def = schema_view.get_type(range_name)
    if type_def and type_def.uri:
        return URIRef(schema_view.expand_curie(type_def.uri)), False
    enum_def = schema_view.get_enum(range_name)
    if enum_def:
        return XSD.string, False
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
    ]
    if schema.license:
        predicates.append((DCTERMS.license, URIRef(schema.license)))
    if schema.created_by:
        predicates.append((URIRef(str(DCTERMS) + "author"), URIRef(schema.created_by)))
    for contributor in schema.contributors or []:
        predicates.append((DCTERMS.contributor, URIRef(str(contributor))))
    predicates.extend(_annotation_triples(schema, manager))
    return _turtle_block(ontology_iri, predicates, manager)


def _annotation_triples(
    schema: SchemaDefinition, manager: NamespaceManager
) -> list[tuple[URIRef, URIRef | Literal | str]]:
    """Emit ontology metadata triples from schema annotations with CURIE keys.

    dcterms:publisher is handled separately via _publisher() (nested org structure).
    All other CURIE-keyed annotations: URI-like values → URIRef, else → Literal.
    List values emit one triple per item.
    """
    triples: list[tuple[URIRef, URIRef | Literal | str]] = []
    for key, annotation in (schema.annotations or {}).items():
        if key == "dcterms:publisher":
            publisher = _publisher(schema, manager)
            if publisher:
                triples.append((DCTERMS.publisher, publisher))
            continue
        try:
            predicate = URIRef(manager.expand_curie(key))
        except Exception:
            continue
        value = annotation.value
        items = value if isinstance(value, list) else [value]
        for item in items:
            triples.append((predicate, _annotation_value(item)))
    return triples


def _annotation_value(value: object) -> URIRef | Literal:
    s = str(value)
    if s.startswith(("http://", "https://", "mailto:", "urn:")):
        return URIRef(s)
    return Literal(s)


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


def _enum_blocks(
    enum_iri: URIRef,
    enum_def: EnumDefinition,
    ontology_iri: URIRef,
    merged_view: SchemaView,
    manager: NamespaceManager,
) -> list[str]:
    blocks = []
    class_predicates: list[tuple[URIRef, URIRef | Literal | str]] = [
        (RDF.type, OWL.Class),
        (RDFS.label, Literal(_local_name(enum_iri))),
        (RDFS.comment, Literal(enum_def.description, lang="en")),
        (RDFS.subClassOf, SCHEMA.Enumeration),
        (RDFS.isDefinedBy, ontology_iri),
        (SKOS.inScheme, ontology_iri),
    ]
    blocks.append(_turtle_block(enum_iri, class_predicates, manager))
    for pv in (enum_def.permissible_values or {}).values():
        if not pv.meaning:
            continue
        instance_iri = URIRef(merged_view.expand_curie(pv.meaning))
        instance_predicates: list[tuple[URIRef, URIRef | Literal | str]] = [
            (RDF.type, enum_iri),
            (RDFS.label, Literal(_local_name(instance_iri))),
        ]
        if pv.description:
            instance_predicates.append((RDFS.comment, Literal(pv.description, lang="en")))
        instance_predicates.append((RDFS.isDefinedBy, ontology_iri))
        blocks.append(_turtle_block(instance_iri, instance_predicates, manager))
    return blocks


def _property_block(property_def: PropertyDefinition, ontology_iri: URIRef, manager: NamespaceManager) -> str:
    if property_def.is_annotation_property:
        property_type = OWL.AnnotationProperty
    elif property_def.is_object_property:
        property_type = OWL.ObjectProperty
    else:
        property_type = OWL.DatatypeProperty
    predicates: list[tuple[URIRef, URIRef | Literal | str]] = [
        (RDF.type, property_type),
        (RDFS.label, Literal(_local_name(property_def.iri))),
    ]
    if property_def.sub_property_of is not None:
        predicates.append((RDFS.subPropertyOf, property_def.sub_property_of))
    if property_def.description:
        predicates.append((RDFS.comment, Literal(property_def.description, lang="en")))
    predicates.extend((RDFS.seeAlso, ref) for ref in property_def.see_also)
    if not property_def.is_annotation_property:
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


def _annotation_list(slot_def: SlotDefinition, key: str) -> list[str]:
    annotations = slot_def.annotations
    if not annotations:
        return []
    if isinstance(annotations, dict):
        annotation = annotations.get(key)
    else:
        annotation = getattr(annotations, key, None)
    if annotation is None:
        return []
    value = annotation.value
    if isinstance(value, list):
        return value
    return [v.strip() for v in str(value).split(",")]


def _local_name(iri: URIRef | None) -> str:
    if iri is None:
        return ""
    return str(iri).rsplit("#", 1)[-1].rsplit("/", 1)[-1]

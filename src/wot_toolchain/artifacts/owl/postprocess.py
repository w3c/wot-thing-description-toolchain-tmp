"""Post-process the OWL graph of one vocabulary and serialize it as Turtle."""

from linkml_runtime.utils.schemaview import SchemaView
from rdflib import BNode, Graph, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS
from rdflib.plugin import register
from rdflib.serializer import Serializer
from rdflib.term import Node

from ...schema_utils import annotation_str_value, is_non_ontological_enum
from ..transforms import Transform, TransformKind, run_transforms
from .header import SCHEMA

LINKML_NAMESPACE = str(Namespace("https://w3id.org/linkml/"))

register("wot-turtle", Serializer, "wot_toolchain.serializers.wot_turtle", "WotTurtleSerializer")


def _demote_to_datatype(graph: Graph, properties: set[Node]) -> None:
    """Turn each object property without a range into a datatype property."""
    for prop in properties:
        if (prop, RDFS.range, None) in graph or (prop, RDF.type, OWL.ObjectProperty) not in graph:
            continue
        graph.remove((prop, RDF.type, OWL.ObjectProperty))
        graph.add((prop, RDF.type, OWL.DatatypeProperty))


def _strip_linkml_ranges(graph: Graph, schema_view: SchemaView) -> None:
    """Remove ranges in the LinkML namespace; a property left without a range becomes a datatype property."""
    stripped: set[Node] = set()
    for prop, _, range_ in list(graph.triples((None, RDFS.range, None))):
        if isinstance(range_, URIRef) and str(range_).startswith(LINKML_NAMESPACE):
            stripped.add(prop)
            graph.remove((prop, RDFS.range, range_))
    _demote_to_datatype(graph, stripped)


def _classes_by_property(schema_view: SchemaView) -> dict[str, set[str]]:
    """Return, per property IRI, the IRIs of the classes in the ``domain_of`` of its slots."""
    classes: dict[str, set[str]] = {}
    for slot_name in schema_view.all_slots(attributes=True):
        for class_name in schema_view.induced_slot(slot_name).domain_of:
            class_uri = schema_view.get_class(class_name).class_uri
            slot_uri = schema_view.induced_slot(slot_name, class_name).slot_uri
            if class_uri and slot_uri:
                classes.setdefault(schema_view.expand_curie(slot_uri), set()).add(schema_view.expand_curie(class_uri))
    return classes


def _class_or_union(graph: Graph, class_iris: list[str]) -> Node:
    """Return the single class of ``class_iris``, or a new owl:unionOf class over all of them."""
    members: list[Node] = [URIRef(class_iri) for class_iri in class_iris]
    for member in members:
        graph.add((member, RDF.type, OWL.Class))
    if len(members) == 1:
        return members[0]
    union = BNode()
    graph.add((union, RDF.type, OWL.Class))
    graph.add((union, OWL.unionOf, Collection(graph, BNode(), members).uri))
    return union


def _add_usage_domains(graph: Graph, schema_view: SchemaView) -> None:
    """Give each property without a declared rdfs:domain the classes that use it as its domain."""
    for property_iri, class_iris in _classes_by_property(schema_view).items():
        prop = URIRef(property_iri)
        if (prop, RDF.type, None) not in graph or (prop, RDFS.domain, None) in graph:
            continue
        graph.add((prop, RDFS.domain, _class_or_union(graph, sorted(class_iris))))


def _indexed_classes_by_property(schema_view: SchemaView) -> dict[str, set[str]]:
    """Return, per JSON-LD index property IRI, the names of the classes whose instances it indexes."""
    indexed: dict[str, set[str]] = {}
    for class_name in schema_view.all_classes():
        for slot in schema_view.class_induced_slots(class_name):
            index = annotation_str_value(slot, "jsonld_index")
            if index and slot.range in schema_view.all_classes():
                indexed.setdefault(schema_view.expand_curie(index), set()).add(slot.range)
    return indexed


def _most_general(schema_view: SchemaView, class_names: set[str]) -> set[str]:
    """Drop each class of ``class_names`` that has an ancestor among them."""
    return {name for name in class_names if not class_names & (set(schema_view.class_ancestors(name)) - {name})}


def _named_domain_classes(graph: Graph, prop: URIRef) -> set[URIRef]:
    """Return the named classes of the rdfs:domain of ``prop``, the members of a union included."""
    classes: set[URIRef] = set()
    for domain in graph.objects(prop, RDFS.domain):
        members = [domain, *(m for union in graph.objects(domain, OWL.unionOf) for m in Collection(graph, union))]
        classes.update(member for member in members if isinstance(member, URIRef))
    return classes


def _remove_domains(graph: Graph, prop: URIRef) -> None:
    """Remove every rdfs:domain of ``prop``, an anonymous union class with it."""
    for domain in list(graph.objects(prop, RDFS.domain)):
        graph.remove((prop, RDFS.domain, domain))
        if isinstance(domain, BNode):
            for union in list(graph.objects(domain, OWL.unionOf)):
                Collection(graph, union).clear()
            graph.remove((domain, None, None))


def _add_index_domains(graph: Graph, schema_view: SchemaView) -> None:
    """Add to the domain of each JSON-LD index property the classes whose instances it indexes."""
    names_by_iri = {
        schema_view.expand_curie(cls.class_uri): name
        for name, cls in schema_view.all_classes().items()
        if cls.class_uri
    }
    for property_iri, indexed in _indexed_classes_by_property(schema_view).items():
        prop = URIRef(property_iri)
        if (prop, RDF.type, None) not in graph:
            continue
        declared = _named_domain_classes(graph, prop)
        if any(str(iri) not in names_by_iri for iri in declared):
            continue
        general = _most_general(schema_view, indexed | {names_by_iri[str(iri)] for iri in declared})
        iris = sorted(schema_view.expand_curie(schema_view.get_class(name).class_uri) for name in general)
        if {URIRef(iri) for iri in iris} == declared:
            continue
        _remove_domains(graph, prop)
        graph.add((prop, RDFS.domain, _class_or_union(graph, iris)))


def _language_map_slot_iris(schema_view: SchemaView) -> set[str]:
    """Return the IRIs of the slots whose JSON-LD container is a language map."""
    return {
        schema_view.expand_curie(slot.slot_uri)
        for slot in schema_view.all_slots().values()
        if slot.slot_uri and annotation_str_value(slot, "jsonld_container") == "@language"
    }


def _add_language_map_ranges(graph: Graph, schema_view: SchemaView) -> None:
    """Give each property serialized as a JSON-LD language map the range rdf:langString."""
    for property_iri in _language_map_slot_iris(schema_view):
        prop = URIRef(property_iri)
        if (prop, RDF.type, OWL.DatatypeProperty) in graph:
            graph.set((prop, RDFS.range, RDF.langString))


def _class_valued_slots(schema_view: SchemaView) -> dict[str, list[str]]:
    """Return, per slot IRI, the class IRIs its values name: the ``meaning`` of each value of its enum range.

    Only an enum that has no ontology counterpart of its own and gives every value a ``meaning`` counts.
    """
    enums = schema_view.all_enums()
    found: dict[str, list[str]] = {}
    for slot in schema_view.all_slots().values():
        enum = enums.get(slot.range) if slot.range else None
        if not slot.slot_uri or enum is None or not is_non_ontological_enum(enum):
            continue
        meanings = [value.meaning for value in enum.permissible_values.values()]
        if meanings and all(meanings):
            found[schema_view.expand_curie(slot.slot_uri)] = [schema_view.expand_curie(m) for m in meanings]
    return found


def _add_class_valued_ranges(graph: Graph, schema_view: SchemaView) -> None:
    """Make each slot whose enum values name classes an object property ranging over exactly those classes."""
    for property_iri, class_iris in _class_valued_slots(schema_view).items():
        prop = URIRef(property_iri)
        if (prop, RDF.type, OWL.DatatypeProperty) not in graph:
            continue
        graph.remove((prop, RDF.type, OWL.DatatypeProperty))
        graph.add((prop, RDF.type, OWL.ObjectProperty))
        one_of = BNode()
        graph.add((one_of, RDF.type, OWL.Class))
        graph.add((one_of, OWL.oneOf, Collection(graph, BNode(), [URIRef(iri) for iri in class_iris]).uri))
        graph.set((prop, RDFS.range, one_of))


OWL_TRANSFORMS: tuple[Transform, ...] = (
    Transform(
        name="strip_linkml_ranges",
        kind=TransformKind.WOT_SHAPING,
        reason="A slot of range Any gets rdfs:range linkml:Any. The ontology has no LinkML terms.",
        apply=_strip_linkml_ranges,
    ),
    Transform(
        name="add_usage_domains",
        kind=TransformKind.LINKML_GAP,
        reason="gen-owl emits rdfs:domain only from a slot's own domain and ignores domain_of. A property without "
        "a domain gets the classes of its slots' domain_of: one class, or the owl:unionOf of several.",
        apply=_add_usage_domains,
    ),
    Transform(
        name="add_index_domains",
        kind=TransformKind.WOT_SHAPING,
        reason="A property named by ``jsonld_index`` on a slot is stated on the values of that slot, so the "
        "classes those values belong to are part of its domain.",
        apply=_add_index_domains,
    ),
    Transform(
        name="add_language_map_ranges",
        kind=TransformKind.WOT_SHAPING,
        reason="A slot with a JSON-LD language map holds language-tagged strings, so its range is rdf:langString "
        "and not the class that models the map in JSON.",
        apply=_add_language_map_ranges,
    ),
    Transform(
        name="add_class_valued_ranges",
        kind=TransformKind.WOT_SHAPING,
        reason="A slot whose enum values each name a class by ``meaning`` holds that class in RDF, not the JSON "
        "string, so it is an object property whose range is the owl:oneOf of those classes.",
        apply=_add_class_valued_ranges,
    ),
)


def post_process_owl(graph: Graph, schema_view: SchemaView) -> str:
    """Apply the OWL transforms to ``graph`` and return it as Turtle."""
    run_transforms(OWL_TRANSFORMS, graph, schema_view)
    graph.namespace_manager.bind("schema", SCHEMA, override=True, replace=True)
    return graph.serialize(format="wot-turtle")

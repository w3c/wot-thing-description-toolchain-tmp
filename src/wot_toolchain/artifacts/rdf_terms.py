"""The RDF terms a schema declares: property IRIs with the classes of their domain and range."""

from linkml_runtime.utils.schemaview import SchemaView

from ..schema_utils import annotation_str_value, is_non_ontological_enum


def domain_classes_by_property(schema_view: SchemaView) -> dict[str, set[str]]:
    """Return, per property IRI, the IRIs of the classes in the ``domain_of`` of its slots."""
    classes: dict[str, set[str]] = {}
    for slot_name in schema_view.all_slots(attributes=True):
        for class_name in schema_view.induced_slot(slot_name).domain_of:
            class_uri = schema_view.get_class(class_name).class_uri
            slot_uri = schema_view.induced_slot(slot_name, class_name).slot_uri
            if class_uri and slot_uri:
                classes.setdefault(schema_view.expand_curie(slot_uri), set()).add(schema_view.expand_curie(class_uri))
    return classes


def indexed_classes_by_property(schema_view: SchemaView) -> dict[str, set[str]]:
    """Return, per JSON-LD index property IRI, the names of the classes whose instances it indexes."""
    indexed: dict[str, set[str]] = {}
    for class_name in schema_view.all_classes():
        for slot in schema_view.class_induced_slots(class_name):
            index = annotation_str_value(slot, "jsonld_index")
            if index and slot.range in schema_view.all_classes():
                indexed.setdefault(schema_view.expand_curie(index), set()).add(slot.range)
    return indexed


def most_general_classes(schema_view: SchemaView, class_names: set[str]) -> set[str]:
    """Drop each class of ``class_names`` that has an ancestor among them."""
    return {name for name in class_names if not class_names & (set(schema_view.class_ancestors(name)) - {name})}


def language_map_property_iris(schema_view: SchemaView) -> set[str]:
    """Return the IRIs of the slots whose JSON-LD container is a language map."""
    return {
        schema_view.expand_curie(slot.slot_uri)
        for slot in schema_view.all_slots().values()
        if slot.slot_uri and annotation_str_value(slot, "jsonld_container") == "@language"
    }


def class_valued_properties(schema_view: SchemaView) -> dict[str, list[str]]:
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

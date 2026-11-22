"""Term keys, CURIE helpers and prefix declarations shared by the JSON-LD context transforms."""

from linkml_runtime.linkml_model.meta import SlotDefinition
from linkml_runtime.utils.formatutils import underscore
from linkml_runtime.utils.schemaview import SchemaView


def expand_curie(schema_view: SchemaView, curie: str) -> str:
    """Expand a CURIE to a full IRI using schema-declared prefixes."""
    expanded: str | None = schema_view.expand_curie(curie)
    if expanded and expanded != curie:
        return expanded
    return curie


def curie_term_name(curie: str) -> str:
    """Extract the local term name from a CURIE (e.g. 'td:name' → 'name')."""
    if ":" in curie:
        return curie.split(":", 1)[1]
    return curie


def context_slots(schema_view: SchemaView) -> list[SlotDefinition]:
    """Return every slot definition followed by the induced slots of every class."""
    slots = list(schema_view.all_slots().values())
    for class_name in schema_view.all_classes():
        slots.extend(schema_view.class_induced_slots(class_name))
    return slots


def slot_key(slot: SlotDefinition) -> str:
    """Return the context term key of a slot: its alias or name, underscored."""
    key: str = underscore(slot.alias or slot.name)
    return key


def prefix_declarations(schema_view: SchemaView) -> dict[str, str]:
    """Collect all prefix → namespace mappings from the schema."""
    return {name: str(p.prefix_reference) for name, p in schema_view.schema.prefixes.items() if p.prefix_reference}

"""Transforms that correct the ``@type`` coercion and scoped ``@context`` of term definitions."""

from typing import Any

from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.artifacts.jsonld_context.terms import slot_key


def remove_literal_type_coercion(context: dict[str, Any]) -> None:
    """Strip ``@type: rdfs:Literal`` from slot entries.

    ``rdfs:Literal`` is the correct OWL range for slots that accept both
    ``xsd:string`` and ``rdf:langString``, but it is not a valid JSON-LD
    type coercion target — JSON-LD ``@type`` expects a concrete datatype IRI.
    """
    for val in context.values():
        if isinstance(val, dict):
            if val.get("@type") == "rdfs:Literal":
                del val["@type"]
            if "@context" in val:
                remove_literal_type_coercion(val["@context"])


SKOS_ENUM_KEYS = frozenset({"text", "description", "meaning"})


def strip_skos_enum_contexts(context: dict[str, Any]) -> None:
    """Remove SKOS @context blocks that LinkML emits for enum-ranged slots."""
    for val in context.values():
        if not isinstance(val, dict):
            continue
        inner = val.get("@context")
        if isinstance(inner, dict) and SKOS_ENUM_KEYS.issubset(inner):
            del val["@context"]
        elif isinstance(inner, dict):
            strip_skos_enum_contexts(inner)
        if "@context" in val and isinstance(val["@context"], dict):
            strip_skos_enum_contexts(val["@context"])


def fix_vocab_type_coercion(context: dict[str, Any], schema_view: SchemaView) -> None:
    """Replace ``xsd:anyURI`` with ``@vocab`` for uriorcurie-ranged slots.

    LinkML emits ``@type: xsd:anyURI`` for ``range: uriorcurie`` but the
    upstream W3C context uses ``@type: @vocab`` so values resolve as
    vocabulary terms rather than plain URI strings.
    """
    vocab_slots = {slot_key(slot) for slot in schema_view.all_slots().values() if slot.range == "uriorcurie"}
    for key, val in context.items():
        if key in vocab_slots and isinstance(val, dict) and val.get("@type") == "xsd:anyURI":
            val["@type"] = "@vocab"
        if isinstance(val, dict) and "@context" in val:
            fix_vocab_type_coercion(val["@context"], schema_view)


def fix_enum_vocab_type_coercion(context: dict[str, Any], schema_view: SchemaView) -> None:
    """Set ``@type: @vocab`` for slots whose range is an enum with ``meaning`` declarations.

    When permissible values carry ``meaning`` CURIEs, their aliases are added
    to the context by ``add_enum_value_aliases``.  The ``@type: @vocab``
    coercion activates those aliases so bare string values expand to IRIs.
    Slots with ``designates_type`` are excluded — they map to ``@type``.
    """
    vocab_enum_slots: set[str] = set()
    for slot in schema_view.all_slots().values():
        if slot.designates_type:
            continue
        enum_def = schema_view.get_enum(slot.range) if slot.range else None
        if enum_def is None:
            continue
        if any(pv.meaning for pv in enum_def.permissible_values.values()):
            vocab_enum_slots.add(slot_key(slot))
    for key, val in context.items():
        if key in vocab_enum_slots and isinstance(val, dict) and "@type" not in val:
            val["@type"] = "@vocab"
        if isinstance(val, dict) and "@context" in val:
            fix_enum_vocab_type_coercion(val["@context"], schema_view)


def fix_object_property_id_coercion(context: dict[str, Any], schema_view: SchemaView) -> None:
    """Fix ``@type`` coercion for ``owl:ObjectProperty`` slots.

    Two cases:

    1. ``range: uri`` / ``range: uriorcurie`` — LinkML emits ``xsd:anyURI``,
       replace with ``@id``.
    2. ``range: string`` where values are name-based cross-references resolved
       to IRIs by the JSON-LD processor — LinkML emits no ``@type``, add ``@id``.
       Skipped when the enclosing context has ``@vocab`` set, because values
       resolve via vocabulary mapping instead (e.g. ``wotsec:allOf`` inside
       the ``security`` scoped context) (gap 3g).
    """
    replace_anyuri: set[str] = set()
    add_id: set[str] = set()
    all_classes = schema_view.all_classes()
    for slot in schema_view.all_slots().values():
        if "owl:ObjectProperty" not in (slot.implements or []):
            continue
        if slot.range in ("uri", "uriorcurie"):
            replace_anyuri.add(slot_key(slot))
        elif slot.range == "string" and slot.domain and slot.domain in all_classes:
            domain_has_vocab = any(s.designates_type for s in schema_view.class_induced_slots(slot.domain))
            if not domain_has_vocab:
                add_id.add(slot_key(slot))
    for key, val in context.items():
        if isinstance(val, dict) and key in replace_anyuri and val.get("@type") == "xsd:anyURI":
            val["@type"] = "@id"
        if isinstance(val, dict) and key in add_id and "@type" not in val:
            val["@type"] = "@id"
        if isinstance(val, dict) and "@context" in val:
            fix_object_property_id_coercion(val["@context"], schema_view)


def fix_type_designator_mapping(context: dict[str, Any], schema_view: SchemaView, *, root: bool = True) -> None:
    """Map ``designates_type`` slots to ``@type`` in JSON-LD context.

    When a slot carries ``designates_type: true`` its value determines the
    RDF type of the enclosing node.  The JSON-LD representation is
    ``{"@id": "@type"}``.  LinkML's context generator does not emit this.

    At root level, designator slots are *removed* — they must only appear
    inside scoped contexts where the owning class lives, otherwise they
    hijack ``@type`` globally.
    """
    designator_slots = {slot_key(slot) for slot in schema_view.all_slots().values() if slot.designates_type}
    for key in list(context.keys()):
        val = context[key]
        if key in designator_slots:
            if root:
                del context[key]
            else:
                context[key] = {"@id": "@type"}
        if isinstance(val, dict) and "@context" in val:
            fix_type_designator_mapping(val["@context"], schema_view, root=False)


def strip_datatype_property_id_coercion(context: dict[str, Any], schema_view: SchemaView) -> None:
    """Strip ``@type: @id`` from slots declared as ``owl:DatatypeProperty``.

    ``range: Any`` (a LinkML class) causes the context generator to emit
    ``@type: @id``.  When the slot's ``implements`` declares it as a
    DatatypeProperty, the coercion is wrong and must be removed.
    """
    datatype_slots = {
        slot_key(slot) for slot in schema_view.all_slots().values() if "owl:DatatypeProperty" in (slot.implements or [])
    }
    for key, val in context.items():
        if key in datatype_slots and isinstance(val, dict) and val.get("@type") == "@id":
            del val["@type"]
        if isinstance(val, dict) and "@context" in val:
            strip_datatype_property_id_coercion(val["@context"], schema_view)


def strip_inlined_class_id_coercion(context: dict[str, Any], schema_view: SchemaView) -> None:
    """Strip ``@type: @id`` from inlined slots whose range class has no identifier.

    LinkML emits ``@type: @id`` for every class-ranged slot (gap 3f).  When the
    range class has no identifier slot and ``inlined: true`` is set, values are
    always embedded objects that cannot be referenced by IRI — ``@type: @id`` is
    wrong.  Classes with identifiers keep ``@type: @id`` because their instances
    can be either inlined or referenced.
    """
    all_classes = schema_view.all_classes()
    inlined_slots: set[str] = set()
    for slot in schema_view.all_slots().values():
        if slot.range not in all_classes:
            continue
        if not schema_view.is_inlined(slot):
            continue
        if "owl:ObjectProperty" in (slot.implements or []):
            continue
        if any(s.identifier for s in schema_view.class_induced_slots(slot.range)):
            continue
        inlined_slots.add(slot_key(slot))
    for key, val in context.items():
        if key in inlined_slots and isinstance(val, dict) and val.get("@type") == "@id":
            del val["@type"]
        if isinstance(val, dict) and "@context" in val:
            strip_inlined_class_id_coercion(val["@context"], schema_view)

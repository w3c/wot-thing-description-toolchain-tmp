"""Compose the WoT JSON-LD context from LinkML-declared mappings."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml_runtime.linkml_model.meta import SlotDefinition
from linkml_runtime.utils.formatutils import underscore
from linkml_runtime.utils.schemaview import SchemaView

from . import curie_prefix, resolve_prefix_namespace

JSONLD_RESERVED_SLOT_NAMES = frozenset({"@context", "@type"})
JSONLD_FIXED_TERM_MAPPINGS = {"id": "@id"}


def _annotation_value(annotatable: Any, key: str) -> str | None:
    annotations = getattr(annotatable, "annotations", None) or {}
    annotation = (
        annotations.get(key)
        if isinstance(annotations, dict)
        else getattr(annotations, key, None)
    )
    return str(annotation.value) if annotation else None


def _expand_curie(schema_view: SchemaView, curie: str) -> str:
    """Expand a CURIE to a full IRI using schema-declared prefixes."""
    expanded = schema_view.expand_curie(curie)
    if expanded and expanded != curie:
        return expanded
    return curie


def _curie_term_name(curie: str) -> str:
    """Extract the local term name from a CURIE (e.g. 'td:name' → 'name')."""
    if ":" in curie:
        return curie.split(":", 1)[1]
    return curie


def _context_slots(schema_view: SchemaView) -> list[SlotDefinition]:
    slots = list(schema_view.all_slots().values())
    for class_name in schema_view.all_classes():
        slots.extend(schema_view.class_induced_slots(class_name))
    return slots


def _slot_key(slot: SlotDefinition) -> str:
    return underscore(slot.alias or slot.name)


def _owned_vocabulary_prefix(schema_view: SchemaView, class_name: str) -> str | None:
    class_definition = schema_view.get_class(class_name)
    prefix = curie_prefix(str(class_definition.class_uri) if class_definition.class_uri else None)
    if prefix is None:
        return None
    if any(
        curie_prefix(str(induced_slot.slot_uri) if induced_slot.slot_uri else None) == prefix
        for induced_slot in schema_view.class_induced_slots(class_name)
    ):
        return prefix
    return None


def _native_slot_context(generator: ContextGenerator, slot: SlotDefinition) -> dict[str, Any]:
    generator.context_body.clear()
    generator.visit_schema()
    if slot.range is None:
        entry: dict[str, Any] = {}
        generator._build_element_id(entry, slot.slot_uri)
        return entry
    generator.visit_slot(slot.alias or slot.name, slot)
    native_key = underscore(slot.alias or slot.name)
    return deepcopy(generator.context_body[native_key])


def _remove_reserved_jsonld_slots(context: dict[str, Any]) -> None:
    for keyword in JSONLD_RESERVED_SLOT_NAMES:
        context.pop(keyword, None)


def _apply_fixed_jsonld_term_mappings(context: dict[str, Any]) -> None:
    context.update(JSONLD_FIXED_TERM_MAPPINGS)


def _uninduced_slot_keys(schema_view: SchemaView) -> frozenset[str]:
    """Slot keys that no class induces and that no @index annotation references."""
    induced: set[str] = set()
    for cls_name in schema_view.all_classes():
        for slot in schema_view.class_induced_slots(cls_name):
            induced.add(slot.name)
    index_terms: set[str] = set()
    for slot in _context_slots(schema_view):
        if idx := _annotation_value(slot, "jsonld_index"):
            index_terms.add(_curie_term_name(idx))
    never_induced = set(schema_view.all_slots().keys()) - induced
    return frozenset(
        _slot_key(schema_view.get_slot(s))
        for s in never_induced
        if _slot_key(schema_view.get_slot(s)) not in index_terms
    )


def _remove_uninduced_slots(context: dict[str, Any], keys_to_remove: frozenset[str]) -> None:
    """Remove slots from root and all scoped contexts that are never induced by any class."""
    for key in keys_to_remove:
        context.pop(key, None)
    for val in context.values():
        if isinstance(val, dict) and "@context" in val:
            _remove_uninduced_slots(val["@context"], keys_to_remove)


def _remove_literal_type_coercion(context: dict[str, Any]) -> None:
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
                _remove_literal_type_coercion(val["@context"])


_SKOS_ENUM_KEYS = frozenset({"text", "description", "meaning"})


def _strip_skos_enum_contexts(context: dict[str, Any]) -> None:
    """Remove SKOS @context blocks that LinkML emits for enum-ranged slots."""
    for val in context.values():
        if not isinstance(val, dict):
            continue
        inner = val.get("@context")
        if isinstance(inner, dict) and _SKOS_ENUM_KEYS.issubset(inner):
            del val["@context"]
        elif isinstance(inner, dict):
            _strip_skos_enum_contexts(inner)
        if "@context" in val and isinstance(val["@context"], dict):
            _strip_skos_enum_contexts(val["@context"])


def _fix_vocab_type_coercion(context: dict[str, Any], schema_view: SchemaView) -> None:
    """Replace ``xsd:anyURI`` with ``@vocab`` for uriorcurie-ranged slots.

    LinkML emits ``@type: xsd:anyURI`` for ``range: uriorcurie`` but the
    upstream W3C context uses ``@type: @vocab`` so values resolve as
    vocabulary terms rather than plain URI strings.
    """
    vocab_slots = {
        _slot_key(slot)
        for slot in schema_view.all_slots().values()
        if slot.range == "uriorcurie"
    }
    for key, val in context.items():
        if key in vocab_slots and isinstance(val, dict) and val.get("@type") == "xsd:anyURI":
            val["@type"] = "@vocab"
        if isinstance(val, dict) and "@context" in val:
            _fix_vocab_type_coercion(val["@context"], schema_view)


def _fix_enum_vocab_type_coercion(context: dict[str, Any], schema_view: SchemaView) -> None:
    """Set ``@type: @vocab`` for slots whose range is an enum with ``meaning`` declarations.

    When permissible values carry ``meaning`` CURIEs, their aliases are added
    to the context by ``_add_enum_value_aliases``.  The ``@type: @vocab``
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
            vocab_enum_slots.add(_slot_key(slot))
    for key, val in context.items():
        if key in vocab_enum_slots and isinstance(val, dict) and "@type" not in val:
            val["@type"] = "@vocab"
        if isinstance(val, dict) and "@context" in val:
            _fix_enum_vocab_type_coercion(val["@context"], schema_view)


def _fix_object_property_id_coercion(context: dict[str, Any], schema_view: SchemaView) -> None:
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
            replace_anyuri.add(_slot_key(slot))
        elif slot.range == "string" and slot.domain and slot.domain in all_classes:
            domain_has_vocab = any(
                s.designates_type
                for s in schema_view.class_induced_slots(slot.domain)
            )
            if not domain_has_vocab:
                add_id.add(_slot_key(slot))
    for key, val in context.items():
        if isinstance(val, dict) and key in replace_anyuri and val.get("@type") == "xsd:anyURI":
            val["@type"] = "@id"
        if isinstance(val, dict) and key in add_id and "@type" not in val:
            val["@type"] = "@id"
        if isinstance(val, dict) and "@context" in val:
            _fix_object_property_id_coercion(val["@context"], schema_view)


def _add_enum_value_aliases(context: dict[str, Any], schema_view: SchemaView) -> None:
    """Add term aliases for enum permissible values that declare a ``meaning``.

    LinkML does not emit JSON-LD context entries for enum values.  When a
    permissible value carries a ``meaning`` CURIE the upstream W3C context
    maps the lowercase value text to the class IRI so that e.g.
    ``"type": "object"`` expands to ``jsonschema:ObjectSchema``.
    """
    for enum_def in schema_view.all_enums().values():
        for pv_name, pv in enum_def.permissible_values.items():
            if pv.meaning and str(pv_name) not in context:
                context[str(pv_name)] = str(pv.meaning)


def _fix_type_designator_mapping(
    context: dict[str, Any], schema_view: SchemaView, *, root: bool = True
) -> None:
    """Map ``designates_type`` slots to ``@type`` in JSON-LD context.

    When a slot carries ``designates_type: true`` its value determines the
    RDF type of the enclosing node.  The JSON-LD representation is
    ``{"@id": "@type"}``.  LinkML's context generator does not emit this.

    At root level, designator slots are *removed* — they must only appear
    inside scoped contexts where the owning class lives, otherwise they
    hijack ``@type`` globally.
    """
    designator_slots = {
        _slot_key(slot)
        for slot in schema_view.all_slots().values()
        if slot.designates_type
    }
    for key in list(context.keys()):
        val = context[key]
        if key in designator_slots:
            if root:
                del context[key]
            else:
                context[key] = {"@id": "@type"}
        if isinstance(val, dict) and "@context" in val:
            _fix_type_designator_mapping(val["@context"], schema_view, root=False)


def _strip_datatype_property_id_coercion(context: dict[str, Any], schema_view: SchemaView) -> None:
    """Strip ``@type: @id`` from slots declared as ``owl:DatatypeProperty``.

    ``range: Any`` (a LinkML class) causes the context generator to emit
    ``@type: @id``.  When the slot's ``implements`` declares it as a
    DatatypeProperty, the coercion is wrong and must be removed.
    """
    datatype_slots = {
        _slot_key(slot)
        for slot in schema_view.all_slots().values()
        if "owl:DatatypeProperty" in (slot.implements or [])
    }
    for key, val in context.items():
        if key in datatype_slots and isinstance(val, dict) and val.get("@type") == "@id":
            del val["@type"]
        if isinstance(val, dict) and "@context" in val:
            _strip_datatype_property_id_coercion(val["@context"], schema_view)


def _strip_inlined_class_id_coercion(context: dict[str, Any], schema_view: SchemaView) -> None:
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
        inlined_slots.add(_slot_key(slot))
    for key, val in context.items():
        if key in inlined_slots and isinstance(val, dict) and val.get("@type") == "@id":
            del val["@type"]
        if isinstance(val, dict) and "@context" in val:
            _strip_inlined_class_id_coercion(val["@context"], schema_view)


def _remove_linkml_internals(context: dict[str, Any]) -> None:
    """Strip LinkML-internal prefix and type declarations from a context dict."""
    context.pop("linkml", None)
    linkml_terms = [
        key for key, val in context.items()
        if isinstance(val, dict) and str(val.get("@id", "")).startswith("linkml:")
    ]
    for key in linkml_terms:
        del context[key]
    for val in context.values():
        if isinstance(val, dict) and "@context" in val:
            _remove_linkml_internals(val["@context"])


def _resolve_identifier_slot_uri(
    schema_view: SchemaView, class_name: str, slot_name: str,
) -> str | None:
    """Walk the class hierarchy to find a slot_uri for an identifier slot."""
    for ancestor in schema_view.class_ancestors(class_name, reflexive=True, mixins=True):
        cls = schema_view.get_class(ancestor)
        attrs = getattr(cls, "attributes", None) or {}
        attr = attrs.get(slot_name)
        if attr and attr.slot_uri:
            return str(attr.slot_uri)
    return None


def _fix_keyed_map_identifier_slots(context: dict[str, Any], schema_view: SchemaView) -> None:
    """Replace identifier slots' ``@id`` mapping with their ontology predicate.

    LinkML emits ``"name": "@id"`` for ``identifier: true`` slots, making the
    value the node identifier.  Keyed-map index properties are data properties
    and must map to their declared ``slot_uri`` instead.  When no ``slot_uri``
    exists anywhere in the class hierarchy the slot is purely structural and
    is removed from the context.
    """
    identifier_fixes: dict[str, str | None] = {}
    for map_slot in _context_slots(schema_view):
        if not _annotation_value(map_slot, "jsonld_index"):
            continue
        if map_slot.range not in schema_view.all_classes():
            continue
        for member_slot in schema_view.class_induced_slots(map_slot.range):
            if not member_slot.identifier:
                continue
            key = _slot_key(member_slot)
            if key in identifier_fixes:
                continue
            uri = (
                str(member_slot.slot_uri)
                if member_slot.slot_uri
                else _resolve_identifier_slot_uri(schema_view, map_slot.range, member_slot.name)
            )
            identifier_fixes[key] = uri

    for key, uri in identifier_fixes.items():
        existing = context.get(key)
        is_identifier_mapping = existing == "@id" or (
            isinstance(existing, dict) and existing.get("@id") == "@id"
        )
        if not is_identifier_mapping:
            continue
        if uri:
            context[key] = {"@id": uri}
        else:
            context.pop(key, None)


def _context_scope(schema_view: SchemaView, slot: SlotDefinition) -> str | None:
    if explicit_scope := _annotation_value(slot, "jsonld_context"):
        if explicit_scope not in schema_view.schema.prefixes:
            raise ValueError(f"Unknown jsonld_context prefix: {explicit_scope}")
        return explicit_scope
    if slot.range not in schema_view.all_classes():
        return None

    prefixes = {
        prefix
        for class_name in schema_view.class_ancestors(
            slot.range, reflexive=True, mixins=True
        )
        if (prefix := _owned_vocabulary_prefix(schema_view, class_name))
    }
    prefixes.discard(curie_prefix(str(slot.slot_uri) if slot.slot_uri else None))
    unknown_prefixes = prefixes - set(schema_view.schema.prefixes)
    if unknown_prefixes:
        raise ValueError(f"Unknown class URI prefix for {slot.range}: {sorted(unknown_prefixes)}")
    if len(prefixes) > 1:
        raise ValueError(
            f"Ambiguous JSON-LD context for {slot.name}: {sorted(prefixes)}. "
            "Declare jsonld_context explicitly."
        )
    return next(iter(prefixes), None)


def _cross_module_slot_keys(schema_view: SchemaView, prefix: str) -> set[str]:
    """Slot keys used by classes in this module but defined in other modules."""
    keys: set[str] = set()
    for cls in schema_view.all_classes().values():
        cls_prefix = curie_prefix(str(cls.class_uri) if cls.class_uri else None)
        if cls_prefix != prefix:
            continue
        for slot in schema_view.class_induced_slots(cls.name):
            slot_prefix = curie_prefix(str(slot.slot_uri) if slot.slot_uri else None)
            key = _slot_key(slot)
            if slot_prefix and slot_prefix != prefix and not key.startswith("@"):
                keys.add(key)
    return keys


def build_module_context(
    schema_view: SchemaView,
    generator: ContextGenerator,
    prefix: str,
) -> dict[str, Any]:
    """Build a standalone JSON-LD context dict for one vocabulary module."""
    ns = resolve_prefix_namespace(schema_view, prefix)
    context: dict[str, Any] = {"@vocab": ns}
    slots = _context_slots(schema_view)
    all_classes = schema_view.all_classes()
    seen_keys: set[str] = set()
    cross_module = _cross_module_slot_keys(schema_view, prefix)
    designator_slots = {
        _slot_key(slot)
        for slot in schema_view.all_slots().values()
        if slot.designates_type
        and any(
            curie_prefix(str(c.class_uri) if c.class_uri else None) == prefix
            for c in schema_view.all_classes().values()
            if slot.name in [s.name for s in schema_view.class_induced_slots(c.name)]
        )
    }
    for slot in slots:
        key = _slot_key(slot)
        slot_prefix = curie_prefix(str(slot.slot_uri) if slot.slot_uri else None)
        if slot_prefix != prefix and key not in cross_module and key not in designator_slots:
            continue
        if key in designator_slots:
            context[key] = {"@id": "@type"}
            seen_keys.add(key)
            continue
        if key in seen_keys:
            continue
        seen_keys.add(key)
        entry = _native_slot_context(generator, slot)
        if key in cross_module and isinstance(entry, dict):
            bare_id = entry.get("@id", key)
            if ":" not in bare_id:
                entry["@id"] = f"{slot_prefix}:{bare_id}"
        if container := _annotation_value(slot, "jsonld_container"):
            entry["@container"] = container
            if container == "@language":
                entry.pop("@index", None)
                entry.pop("@type", None)
        elif index := _annotation_value(slot, "jsonld_index"):
            entry["@index"] = _curie_term_name(index)
        if isinstance(entry, dict):
            inner = entry.get("@context")
            if isinstance(inner, dict) and _SKOS_ENUM_KEYS.issubset(inner):
                del entry["@context"]
            if entry.get("@type") == "@id" and "owl:DatatypeProperty" in (slot.implements or []):
                entry.pop("@type")
            if entry.get("@type") == "xsd:anyURI" and slot.range == "uriorcurie":
                entry["@type"] = "@vocab"
            if entry.get("@type") == "xsd:anyURI" and "owl:ObjectProperty" in (slot.implements or []):
                entry["@type"] = "@id"
            if (
                "@type" not in entry
                and slot.range == "string"
                and "owl:ObjectProperty" in (slot.implements or [])
                and slot.domain
                and slot.domain in all_classes
                and not any(
                    s.designates_type
                    for s in schema_view.class_induced_slots(slot.domain)
                )
            ):
                entry["@type"] = "@id"
            if (
                entry.get("@type") == "@id"
                and schema_view.is_inlined(slot)
                and slot.range in all_classes
                and "owl:ObjectProperty" not in (slot.implements or [])
                and not any(s.identifier for s in schema_view.class_induced_slots(slot.range))
            ):
                del entry["@type"]
            if "@type" not in entry and not slot.designates_type:
                enum_def = schema_view.get_enum(slot.range) if slot.range else None
                if enum_def and any(pv.meaning for pv in enum_def.permissible_values.values()):
                    entry["@type"] = "@vocab"
        context[key] = entry
    for cls in schema_view.all_classes().values():
        cls_prefix = curie_prefix(str(cls.class_uri) if cls.class_uri else None)
        if cls_prefix == prefix:
            context[cls.name] = {"@id": str(cls.class_uri)}
    for enum_def in schema_view.all_enums().values():
        for pv_name, pv in enum_def.permissible_values.items():
            if pv.meaning and curie_prefix(str(pv.meaning)) == prefix:
                key = str(pv_name)
                if key not in context:
                    context[key] = str(pv.meaning)
    _fix_keyed_map_identifier_slots(context, schema_view)
    return context


def _module_contexts(schema_view: SchemaView, generator: ContextGenerator) -> dict[str, dict[str, Any]]:
    scopes = {
        scope
        for slot in _context_slots(schema_view)
        if (scope := _context_scope(schema_view, slot))
    }
    return {
        scope: build_module_context(schema_view, generator, scope)
        for scope in scopes
    }


def _prefix_declarations(schema_view: SchemaView) -> dict[str, str]:
    """Collect all prefix → namespace mappings from the schema."""
    return {
        name: str(p.prefix_reference)
        for name, p in schema_view.schema.prefixes.items()
        if p.prefix_reference
    }


def _is_bare_term(term_id: str) -> bool:
    """Check if a term ID is a bare name (not a CURIE, IRI, or JSON-LD keyword)."""
    return (
        ":" not in term_id
        and "/" not in term_id
        and not term_id.startswith("@")
    )


def _expand_bare_ids(entry: dict[str, Any], root_vocab: str) -> dict[str, Any]:
    """Expand bare @id values using root @vocab so they resolve correctly in scoped contexts."""
    result = deepcopy(entry)
    term_id = result.get("@id", "")
    if isinstance(term_id, str) and _is_bare_term(term_id):
        result["@id"] = root_vocab + term_id
    return result


def _cross_vocab_terms(
    root_context: dict[str, Any],
    scoped_vocab: str,
) -> dict[str, Any]:
    """Find root-context terms whose @id doesn't match the scoped @vocab.

    These must be re-declared in scoped contexts so they remain accessible.
    Bare @id values are expanded using root @vocab to prevent mis-resolution.
    """
    root_vocab = root_context.get("@vocab", "")
    redeclare: dict[str, Any] = {}
    for key, val in root_context.items():
        if key.startswith("@"):
            continue
        if isinstance(val, str):
            if not val.startswith(scoped_vocab):
                redeclare[key] = val
        elif isinstance(val, dict):
            term_id = val.get("@id", "")
            if isinstance(term_id, str) and not term_id.startswith(scoped_vocab):
                if "@container" not in val and "@context" not in val:
                    redeclare[key] = _expand_bare_ids(val, root_vocab)
    return redeclare


def _term_resolves_to(val: Any, target_iri: str, scoped_vocab: str) -> bool:
    """Check if a context term definition resolves to the target IRI."""
    if isinstance(val, str):
        if val.startswith("@"):
            return False
        if ":" in val or "/" in val:
            return val == target_iri
        return scoped_vocab + val == target_iri
    if isinstance(val, dict):
        term_id = val.get("@id", "")
        if isinstance(term_id, str):
            if term_id.startswith("@"):
                return False
            if ":" in term_id or "/" in term_id:
                return term_id == target_iri
            return scoped_vocab + term_id == target_iri
    return False


def _ensure_index_term(
    scoped: dict[str, Any],
    schema_view: SchemaView,
    index_iri: str,
) -> None:
    """Ensure the scoped context has a term that resolves to the @index IRI."""
    scoped_vocab = scoped.get("@vocab", "")
    if index_iri.startswith(scoped_vocab):
        return
    for key, val in scoped.items():
        if key.startswith("@"):
            continue
        if _term_resolves_to(val, index_iri, scoped_vocab):
            return
    for slot in schema_view.all_slots().values():
        if slot.slot_uri and _expand_curie(schema_view, str(slot.slot_uri)) == index_iri:
            term = _slot_key(slot)
            scoped[term] = {"@id": index_iri}
            return
    local = index_iri.rsplit("#", 1)[-1] if "#" in index_iri else index_iri.rsplit("/", 1)[-1]
    scoped[local] = {"@id": index_iri}


def _apply_two_level_index_nesting(
    key: str,
    entry: dict[str, Any],
    scoped: dict[str, Any],
) -> None:
    parent_index = entry.get("@index")
    if not parent_index:
        return
    inner = scoped.get(key)
    if not isinstance(inner, dict):
        return
    if "@container" not in inner or "@index" not in inner:
        return
    inner_index = inner["@index"]
    if inner_index == parent_index:
        return
    level2 = {key: deepcopy(inner)}
    inner["@index"] = parent_index
    inner["@context"] = level2


def _apply_root_mapping(
    context: dict[str, Any],
    schema_view: SchemaView,
    slot: SlotDefinition,
    module_contexts: dict[str, dict[str, Any]],
) -> None:
    key = _slot_key(slot)
    entry = context.get(key)
    if not isinstance(entry, dict):
        return
    if container := _annotation_value(slot, "jsonld_container"):
        entry["@container"] = container
        if container == "@language":
            entry.pop("@index", None)
            entry.pop("@type", None)
        return
    index_iri = None
    if index := _annotation_value(slot, "jsonld_index"):
        index_iri = _expand_curie(schema_view, index)
        entry["@index"] = _curie_term_name(index)
    if "@context" in entry and not index_iri:
        return
    if scope := _context_scope(schema_view, slot):
        scoped = deepcopy(module_contexts[scope])
        scoped_vocab = scoped.get("@vocab", "")
        prefixes = _prefix_declarations(schema_view)
        for name, ns in prefixes.items():
            if name not in scoped:
                scoped[name] = ns
        cross_terms = _cross_vocab_terms(context, scoped_vocab)
        for term, val in cross_terms.items():
            if term not in scoped:
                scoped[term] = val
        if index_iri:
            _ensure_index_term(scoped, schema_view, index_iri)
        _apply_two_level_index_nesting(key, entry, scoped)
        entry["@context"] = scoped


def _apply_class_mappings(
    schema_view: SchemaView,
    context: dict[str, Any],
    module_contexts: dict[str, dict[str, Any]],
) -> None:
    global_uris = {
        _slot_key(slot): str(slot.slot_uri)
        for slot in schema_view.all_slots().values()
        if slot.slot_uri
    }
    for class_name in schema_view.all_classes():
        for slot in schema_view.class_induced_slots(class_name):
            key = _slot_key(slot)
            if global_uris.get(key) not in {None, str(slot.slot_uri)}:
                continue
            _apply_root_mapping(context, schema_view, slot, module_contexts)


def post_process_jsonld_context(schema_view: SchemaView, serialized_schema: str) -> str:
    """Add schema-declared scoped contexts and index predicates to LinkML output.

    LinkML natively emits container mappings when
    ``fix_multivalue_containers`` is enabled. It does not currently emit the
    RDF predicate represented by a keyed map, or scoped vocabulary contexts.
    """
    document = json.loads(serialized_schema)
    context = document["@context"]
    _remove_reserved_jsonld_slots(context)
    _apply_fixed_jsonld_term_mappings(context)
    _fix_keyed_map_identifier_slots(context, schema_view)
    generator = ContextGenerator(
        schema_view.schema,
        mergeimports=True,
        fix_multivalue_containers=True,
    )
    module_contexts = _module_contexts(schema_view, generator)
    for slot in schema_view.all_slots().values():
        _apply_root_mapping(context, schema_view, slot, module_contexts)
    _apply_class_mappings(schema_view, context, module_contexts)
    _remove_uninduced_slots(context, _uninduced_slot_keys(schema_view))
    _remove_literal_type_coercion(context)
    _strip_skos_enum_contexts(context)
    _strip_datatype_property_id_coercion(context, schema_view)
    _strip_inlined_class_id_coercion(context, schema_view)
    _fix_vocab_type_coercion(context, schema_view)
    _fix_enum_vocab_type_coercion(context, schema_view)
    _fix_object_property_id_coercion(context, schema_view)
    _fix_type_designator_mapping(context, schema_view)
    _add_enum_value_aliases(context, schema_view)
    _remove_linkml_internals(context)
    context["@version"] = 1.1
    return json.dumps(document, indent=2)

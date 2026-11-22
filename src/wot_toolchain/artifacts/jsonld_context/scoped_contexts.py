"""Container, index and scoped-context mappings applied to the terms of the root JSON-LD context."""

from copy import deepcopy
from typing import Any

from linkml_runtime.linkml_model.meta import SlotDefinition
from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.artifacts.jsonld_context.scopes import context_scope
from wot_toolchain.artifacts.jsonld_context.terms import (
    curie_term_name,
    expand_curie,
    prefix_declarations,
    slot_key,
)
from wot_toolchain.schema_utils import annotation_str_value


def _is_bare_term(term_id: str) -> bool:
    """Check if a term ID is a bare name (not a CURIE, IRI, or JSON-LD keyword)."""
    return ":" not in term_id and "/" not in term_id and not term_id.startswith("@")


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
            if (
                isinstance(term_id, str)
                and not term_id.startswith(scoped_vocab)
                and "@container" not in val
                and "@context" not in val
            ):
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
        if slot.slot_uri and expand_curie(schema_view, str(slot.slot_uri)) == index_iri:
            term = slot_key(slot)
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


def apply_root_mapping(
    context: dict[str, Any],
    schema_view: SchemaView,
    slot: SlotDefinition,
    module_contexts: dict[str, dict[str, Any]],
) -> None:
    """Set the container, the index and the scoped module context on the root term of a slot."""
    key = slot_key(slot)
    entry = context.get(key)
    if not isinstance(entry, dict):
        return
    if container := annotation_str_value(slot, "jsonld_container"):
        entry["@container"] = container
        if container == "@language":
            entry.pop("@index", None)
            entry.pop("@type", None)
            return
    index_iri = None
    if index := annotation_str_value(slot, "jsonld_index"):
        index_iri = expand_curie(schema_view, index)
        entry["@index"] = curie_term_name(index)
    is_keyed_map = index_iri is not None or container == "@id"
    if "@context" in entry and not is_keyed_map:
        return
    if scope := context_scope(schema_view, slot):
        scoped = deepcopy(module_contexts[scope])
        scoped_vocab = scoped.get("@vocab", "")
        prefixes = prefix_declarations(schema_view)
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


def apply_class_mappings(
    schema_view: SchemaView,
    context: dict[str, Any],
    module_contexts: dict[str, dict[str, Any]],
) -> None:
    """Apply the root mapping to every class-induced slot whose URI does not conflict with the global slot."""
    global_uris = {slot_key(slot): str(slot.slot_uri) for slot in schema_view.all_slots().values() if slot.slot_uri}
    for class_name in schema_view.all_classes():
        for slot in schema_view.class_induced_slots(class_name):
            key = slot_key(slot)
            if global_uris.get(key) not in {None, str(slot.slot_uri)}:
                continue
            apply_root_mapping(context, schema_view, slot, module_contexts)

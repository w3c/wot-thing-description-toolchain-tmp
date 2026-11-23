"""Ordered passes applied to the root JSON-LD context before and after its scoped contexts are attached."""

from wot_toolchain.artifacts.jsonld_context.coercions import (
    fix_enum_vocab_type_coercion,
    fix_object_property_id_coercion,
    fix_type_designator_mapping,
    fix_vocab_type_coercion,
    remove_literal_type_coercion,
    strip_datatype_property_id_coercion,
    strip_inlined_class_id_coercion,
    strip_skos_enum_contexts,
)
from wot_toolchain.artifacts.jsonld_context.identifiers import fix_keyed_map_identifier_slots
from wot_toolchain.artifacts.jsonld_context.root_terms import (
    add_enum_value_aliases,
    apply_fixed_jsonld_term_mappings,
    remove_linkml_internals,
    remove_non_root_terms,
    remove_reserved_jsonld_slots,
    remove_uninduced_slots,
    uninduced_slot_keys,
)
from wot_toolchain.artifacts.passes import Pass, PassKind

# Every pass is applied to (context, schema_view, extra_root_terms).
PRE_SCOPING_PASSES: tuple[Pass, ...] = (
    Pass(
        name="remove_reserved_jsonld_slots",
        kind=PassKind.UPSTREAM_BUG,
        reason="Upstream emits terms named @context and @type from slot aliases, and keyword-named terms are not "
        "valid JSON-LD terms.",
        apply=lambda context, sv, extra_root_terms: remove_reserved_jsonld_slots(context),
    ),
    Pass(
        name="apply_fixed_jsonld_term_mappings",
        kind=PassKind.WOT_SHAPING,
        reason="Maps id to @id without making it a LinkML identifier, which would make id required in JSON Schema.",
        apply=lambda context, sv, extra_root_terms: apply_fixed_jsonld_term_mappings(context),
    ),
    Pass(
        name="fix_keyed_map_identifier_slots",
        kind=PassKind.UPSTREAM_GAP,
        reason='Upstream emits bare "@id" for identifier slots. A key slot of a map stored as a dict needs its real '
        "URI or no term at all.",
        apply=lambda context, sv, extra_root_terms: fix_keyed_map_identifier_slots(context, sv),
    ),
)

POST_SCOPING_PASSES: tuple[Pass, ...] = (
    Pass(
        name="remove_uninduced_slots",
        kind=PassKind.WOT_SHAPING,
        reason="Drops slots that exist only for OWL (e.g. hasInteractionAffordance), keeping @index terms.",
        apply=lambda context, sv, extra_root_terms: remove_uninduced_slots(context, uninduced_slot_keys(sv)),
    ),
    Pass(
        name="remove_literal_type_coercion",
        kind=PassKind.WOT_SHAPING,
        reason="The range type used for title/description has URI rdfs:Literal, and upstream copies that into @type, "
        "which is not a valid coercion.",
        apply=lambda context, sv, extra_root_terms: remove_literal_type_coercion(context),
    ),
    Pass(
        name="strip_skos_enum_contexts",
        kind=PassKind.WOT_SHAPING,
        reason="The W3C TD context does not use upstream's SKOS enum scoped context, and that context's description "
        "key collides with td:description.",
        apply=lambda context, sv, extra_root_terms: strip_skos_enum_contexts(context),
    ),
    Pass(
        name="strip_datatype_property_id_coercion",
        kind=PassKind.UPSTREAM_BUG,
        reason="Upstream adds @type: @id for every class range (including Any), even on owl:DatatypeProperty slots "
        "(enum, const, default).",
        apply=lambda context, sv, extra_root_terms: strip_datatype_property_id_coercion(context, sv),
    ),
    Pass(
        name="strip_inlined_class_id_coercion",
        kind=PassKind.UPSTREAM_BUG,
        reason="Upstream ignores inlined and coerces inlined objects (response, additionalResponses) to @id.",
        apply=lambda context, sv, extra_root_terms: strip_inlined_class_id_coercion(context, sv),
    ),
    Pass(
        name="fix_vocab_type_coercion",
        kind=PassKind.UPSTREAM_GAP,
        reason="uriorcurie ranges come out as xsd:anyURI, but TD needs @vocab. Upstream xsd_anyuri_as_iri gives only "
        "@id.",
        apply=lambda context, sv, extra_root_terms: fix_vocab_type_coercion(context, sv),
    ),
    Pass(
        name="fix_enum_vocab_type_coercion",
        kind=PassKind.UPSTREAM_GAP,
        reason="Upstream _vocab_eligible_enum emits @vocab only if all values share one prefix and each value text "
        "equals its local name. OperationType fails both conditions.",
        apply=lambda context, sv, extra_root_terms: fix_enum_vocab_type_coercion(context, sv),
    ),
    # After fix_vocab_type_coercion: a uriorcurie owl:ObjectProperty slot keeps @vocab instead of getting @id.
    Pass(
        name="fix_object_property_id_coercion",
        kind=PassKind.UPSTREAM_GAP,
        reason="owl:ObjectProperty slots with a uri or string range need @type: @id. The upstream option applies to "
        "every slot or none, and ignores string ranges.",
        apply=lambda context, sv, extra_root_terms: fix_object_property_id_coercion(context, sv),
    ),
    Pass(
        name="fix_type_designator_mapping",
        kind=PassKind.UPSTREAM_GAP,
        reason='Upstream ignores designates_type, so scheme gets an ordinary entry instead of {"@id": "@type"}.',
        apply=lambda context, sv, extra_root_terms: fix_type_designator_mapping(context, sv),
    ),
    Pass(
        name="add_enum_value_aliases",
        kind=PassKind.UPSTREAM_GAP,
        reason="Upstream emits no aliases for enum values (e.g. readproperty to td:readProperty).",
        apply=lambda context, sv, extra_root_terms: add_enum_value_aliases(context, sv),
    ),
    Pass(
        name="remove_linkml_internals",
        kind=PassKind.COSMETIC,
        reason="Removes the linkml prefix and the Any to linkml:Any term.",
        apply=lambda context, sv, extra_root_terms: remove_linkml_internals(context),
    ),
    # After add_enum_value_aliases: it removes the aliases whose meaning is outside the default prefix.
    Pass(
        name="remove_non_root_terms",
        kind=PassKind.WOT_SHAPING,
        reason="Keeps only td-prefixed terms and the config file's extra_root_terms at the root, matching the W3C "
        "context layout.",
        apply=remove_non_root_terms,
    ),
)

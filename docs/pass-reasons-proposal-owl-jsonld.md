# Proposed reasons for OWL and JSON-LD context passes

These tags and reasons are unconfirmed proposals for the user to review. Nothing here has been confirmed.

How they were gathered: by reading the code, `git log -S`, and the upstream linkml 1.12.0 generators in `.venv`. Raw upstream output (no pre- or postprocessing) was generated for td, hctl and wotsec (OWL) and `thing_description.yaml` (context), then compared pass by pass. "DEAD" means the pass changed nothing on the current `resources/schemas`. Test fixtures were not run.

## OWL preprocess (`preprocessors/owl_preprocessor.py`, `preprocess_for_gen_owl` :59-99, call order)

| Pass | Proposed tag | Proposed reason | Evidence | Confidence |
|---|---|---|---|---|
| `_assign_enum_uris` :164 | WOT-SHAPING (or UPSTREAM-GAP) | Gives each enum a URI in the namespace of the module that defines it. Upstream falls back to the default prefix of the merged schema. Question: do you count that upstream fallback as an upstream gap? | 1de8d8eb; owlgen.py:1611-1618 | medium |
| `_collect_renames` :175 + `_apply_renames` :190 | WOT-SHAPING | Renames slots to the local name of their `slot_uri`. With `use_native_uris=False`, gen-owl already builds IRIs from `slot_uri`, so the only measured effect is on `rdfs:label` (0 IRI changes). The docstring example "td:hasForm not td:forms" is stale. Question: should labels be the JSON key or the `slot_uri` local name? | 14af5fb8, bb61d75f; owlgen.py:1609,1628 | high |
| `_strip_no_uri_classes` :331 | WOT-SHAPING | Removes classes without `class_uri`, which have no term in the ontology. | 1de8d8eb | medium-high |
| `_strip_foreign_mixins` :348 | WOT-SHAPING | Prevents `subClassOf` links into another module's classes (e.g. PropertyAffordance ⊄ DataSchema). | cd92fc45 | high |
| `_promote_attributes` :209 | UPSTREAM-GAP | gen-owl gives class attributes no global `rdfs:range`. | 1de8d8eb; owlgen.py:193-198; guidelines/owl-rdf-modeling.md:126-140 | high |
| `_strip_non_local` :245 | WOT-SHAPING | Keeps only the module's own slots and enums. | 1de8d8eb | medium-high |
| `_strip_jsonld_slots` :274 | WOT-SHAPING | `@`-keyword slots are JSON serialization details, not ontology terms. | 1de8d8eb | high |
| `_strip_no_uri_original_slots` :375 | WOT-SHAPING | Removes slots without `slot_uri`. | 1de8d8eb | medium-high |
| `_strip_discriminator_slots` :281 | DEAD | Changed nothing on current schemas. | 1de8d8eb | high (current schemas only) |
| `_strip_non_ontological_enums` :292 | WOT-SHAPING | Enums without `enum_uri` are JSON-Schema-only. Keeping them produced double-`#` IRIs, which pyoxigraph rejected. | 443e80e5; owl-rdf-modeling.md §7 | high |
| `_fix_enum_pv_labels` :305 | WOT-SHAPING | Renames permissible-value keys to the local name of their `meaning`, so the value IRIs and labels follow the WoT vocabulary. | cd92fc45; owlgen.py:1212 | high |
| `_infer_ranges_from_branches` :396 | DEAD | Changed nothing on current schemas. | 1de8d8eb | high (current schemas only) |
| `_clear_constraints` :437 | WOT-SHAPING | Prevents blank-node `owl:Restriction` axioms, which the WoT ontology does not use. It also sets `multivalued=True`; the effect of that on functional-property axioms was not measured. | 14af5fb8, 1de8d8eb | high |
| `_strip_dangling_slot_refs` :409 | WOT-SHAPING (plumbing) | Removes references to slots that earlier passes deleted. | cd92fc45 | high |
| `_strip_schema_metadata` :382 | WOT-SHAPING | Stops gen-owl emitting metamodel predicates and a second ontology header. Postprocess `_add_ontology_header` rebuilds the header. | 1de8d8eb | medium |

## OWL postprocess (`postprocessors/owl_postprocessor.py`, `postprocess_owl` :33-72, call order)

| Pass | Proposed tag | Proposed reason | Evidence | Confidence |
|---|---|---|---|---|
| `_strip_foreign_subjects` :85 | WOT-SHAPING | Removes subjects that belong to other modules. | f198fbf1 | high |
| `_strip_linkml_ranges` (+ `_demote_to_datatype`) | WOT-SHAPING | Since `bba1748f` removes three `rdfs:range linkml:Any` triples in jsonschema (`enum`, `const`, `default`); nothing in the other modules. `_demote_to_datatype` changes nothing on current schemas. | f198fbf1 | high (current schemas only) |
| `_fix_in_scheme` :124 (removed; now `WotOwlGenerator.add_metadata`) | DEAD | The raw `skos:inScheme` value is already the ontology IRI. | f198fbf1 | high (current schemas only) |
| `_fix_subproperty_literals` :185 (removed; now `WotOwlGenerator.add_metadata`) | UPSTREAM-GAP | gen-owl writes CURIE-valued annotations as plain strings, so `rdfs:subPropertyOf` comes out as a literal instead of an IRI. | ee7835d4; owlgen.py:437-440 | high |
| `_fix_uri_annotation_literals` :196 (removed; now `WotOwlGenerator.add_metadata`) | UPSTREAM-GAP | Same string-to-IRI repair for `rdfs:seeAlso` and `rdfs:subClassOf`. The `isDefinedBy` branch never fires. | cd92fc45 | high |
| `_clean_exact_match` :219 (removed; now `WotOwlGenerator.add_class`) | WOT-SHAPING | Removes the `skos:exactMatch` triples that `use_native_uris=False` produces. | f198fbf1; owlgen.py:513-515 | high |
| `_clean_enum_artifacts` :130 (removed; now `WotOwlGenerator.add_enum`) | WOT-SHAPING | Removes the gen-owl `unionOf` and `linkml:permissible_values` triples. The double-`#`, `oneOf` and `NamedIndividual` branches never fire. | f198fbf1; owlgen.py:1234-1250 | high |
| `_convert_enum_subclasses_to_individuals` :160 (removed; now `WotOwlGenerator.add_enum`) | WOT-SHAPING | gen-owl emits enum values as subclasses (`default_permissible_value_type=OWL.Class`); the WoT ontology uses instances. | f198fbf1; owlgen.py:164; owl-rdf-modeling.md §7 | high |
| `_fix_aliased_labels` :209 (removed; now `WotOwlGenerator.add_metadata`) | WOT-SHAPING | gen-owl turns `alias` into `skos:prefLabel`; this pass rewrites it as `rdfs:label`. Only wotsec is affected. | cd92fc45 | medium |
| `_strip_orphan_blank_nodes` | REMOVED | Deleted in step 16c-9: `WotOwlGenerator` emits no blank nodes since `bba1748f`, the pass changed nothing in any module. | f198fbf1 | high (current schemas only) |
| `_strip_empty_blank_node_restrictions` | REMOVED | Deleted in step 16c-9: changed nothing in any module. | f198fbf1 | high (current schemas only) |
| `_add_domain_includes` :224 | UPSTREAM-GAP | gen-owl cannot emit `schema:domainIncludes` for properties used by several classes. | 2b2da5fd; known-linkml-gaps.md #11; owl-accepted-differences.md P3 | high |
| `_add_is_defined_by` :254 (removed; now `WotOwlGenerator.add_metadata`) | WOT-SHAPING | Adds `rdfs:isDefinedBy <ontology>` to every local term. | 2b2da5fd; owl-rdf-modeling.md §5a | medium-high |
| `_add_lang_tags` | REMOVED | Deleted in step 16c-7: `WotOwlGenerator` sets upstream `default_language` and emits the `@en` tags itself; output unchanged. | 2b2da5fd | low-medium |
| `_add_ontology_header` :271 | WOT-SHAPING | Builds the ontology header from the schema's `annotations:`. `_publisher_node` :309 silently returns None when the annotation is malformed, instead of failing. | f198fbf1 | high |
| `g.bind("schema", ...)` :69 | COSMETIC | Sets the prefix name used in the output. | owl_postprocessor.py:69 | high |

## Serializer (`serializers/wot_turtle.py`)

| Pass | Proposed tag | Proposed reason | Evidence | Confidence |
|---|---|---|---|---|
| `WotTurtleSerializer` (predicate order :19-41, subject grouping :43,:61-112, `keywords={}` :45-48, `@prefix` :50-59) | COSMETIC | Copies the layout of the W3C ontology files. It does not change the triples. | owl-accepted-differences.md C1-C4; introducing commit not traced | high |

## JSON-LD merged context (`postprocessors/jsonld_context_postprocessor.py`, `post_process_jsonld_context` :774-821, call order)

| Pass | Proposed tag | Proposed reason | Evidence | Confidence |
|---|---|---|---|---|
| `_remove_reserved_jsonld_slots` :75 | UPSTREAM-BUG | Upstream emits terms named `@context` and `@type` from slot aliases, and keyword-named terms are not valid JSON-LD terms. | cc02149b; raw output has `"@context": {"@id": "@context"}` | medium (no JSON-LD processor run) |
| `_apply_fixed_jsonld_term_mappings` :80 | WOT-SHAPING | Maps `id` → `@id` without making it a LinkML `identifier`, which would make `id` required in JSON Schema. | cc02149b; raw output has `id` → `xsd:anyURI` | high |
| `_fix_keyed_map_identifier_slots` :397 | UPSTREAM-GAP | Upstream emits bare `"@id"` for identifier slots. A key slot of a map stored as a dict needs its real URI or no term at all. | d84e11c4; jsonldcontextgen.py:377-378 | high |
| `_module_contexts` :604 / `_context_scope` :436 | UPSTREAM-GAP | Upstream has no scoped `@context`. | 6bc508db; known-linkml-gaps.md #1, #3a | medium-high |
| `_apply_root_mapping` :721 | UPSTREAM-GAP | Upstream cannot express `@container: @index` / `@language`, an `@index` property, scoped contexts or two-level index nesting. | 6bc508db, d84e11c4; known-linkml-gaps.md #3, #3a | high |
| `_apply_class_mappings` :760 | UPSTREAM-GAP | Scoped contexts on class terms (same missing upstream feature). | 6bc508db | medium |
| `_remove_uninduced_slots` :102 | WOT-SHAPING | Drops slots that exist only for OWL (e.g. `hasInteractionAffordance`), keeping `@index` terms. | d84e11c4; guidelines/jsonld-context-composition.md:177-192 | high |
| `_remove_literal_type_coercion` :111 | WOT-SHAPING (or UPSTREAM-GAP) | The range type used for `title`/`description` has URI `rdfs:Literal`, and upstream copies that into `@type`, which is not a valid coercion. Question: is this a schema modelling choice, or an upstream gap because the OWL range cannot be kept apart from the JSON-LD coercion? | d84e11c4; jsonldcontextgen.py:421 | medium |
| `_strip_skos_enum_contexts` :129 | WOT-SHAPING | The W3C TD context does not use upstream's SKOS enum scoped context, and that context's `description` key collides with `td:description`. | a622d8dc; jsonldcontextgen.py:395-406 | high |
| `_fix_vocab_type_coercion` :143 | UPSTREAM-GAP | `uriorcurie` ranges come out as `xsd:anyURI`, but TD needs `@vocab`. Upstream `xsd_anyuri_as_iri` gives only `@id`. | 9cc0e1aa; known-linkml-gaps.md #3b; jsonldcontextgen.py:82-87,415 | high |
| `_fix_enum_vocab_type_coercion` :158 | UPSTREAM-GAP (partial) | Upstream `_vocab_eligible_enum` emits `@vocab` only if all values share one prefix and each value text equals its local name. OperationType fails both conditions. | a3f663cb; jsonldcontextgen.py:320-369 | high |
| `_fix_object_property_id_coercion` :182 | UPSTREAM-GAP | `owl:ObjectProperty` slots with a uri or string range need `@type: @id`. The upstream option applies to every slot or none, and ignores string ranges. | edbdcf64, 2e19ba5a; known-linkml-gaps.md #3d, #3g | high |
| `_add_enum_value_aliases` :216 | UPSTREAM-GAP | Upstream emits no aliases for enum values (e.g. `readproperty` → `td:readProperty`). | 76a60518; known-linkml-gaps.md #3c | high |
| `_fix_type_designator_mapping` :230 | UPSTREAM-GAP | Upstream ignores `designates_type`, so `scheme` gets an ordinary entry instead of `{"@id": "@type"}`. | edbdcf64; known-linkml-gaps.md #3e | high |
| `_strip_datatype_property_id_coercion` :253 | UPSTREAM-BUG | Upstream adds `@type: @id` for every class range (including `Any`), even on `owl:DatatypeProperty` slots (`enum`, `const`, `default`). | e98c2a84; jsonldcontextgen.py:393-394 | high |
| `_strip_inlined_class_id_coercion` :272 | UPSTREAM-BUG | Upstream ignores `inlined` and coerces inlined objects (`response`, `additionalResponses`) to `@id`. | 2e19ba5a; known-linkml-gaps.md #3f | high |
| `_remove_linkml_internals` :300 | COSMETIC | Removes the `linkml` prefix and the `Any` → `linkml:Any` term. | d84e11c4 | medium-high |
| `_remove_non_root_terms` :313 | WOT-SHAPING | Keeps only td-prefixed terms and the manifest's `extra_root_terms` at the root, matching the W3C context layout. | f2571209, 0da55192, 011fc17e; wot-toolchain.yaml:19-23 | medium |
| `context["@version"] = 1.1` :821 | UNCLEAR | Scoped contexts and `@index` need it. Question: is this our choice (WOT-SHAPING), or should upstream emit it when it uses JSON-LD 1.1 features (UPSTREAM-GAP)? | introducing commit not traced | low |

## JSON-LD per-module inline rules (`_module_terms` :512-601)

The equivalence notes come from reading the code only. No test compares module output with merged output.

| Rule | Proposed tag | Proposed reason / equivalence with merged pass | Evidence | Confidence |
|---|---|---|---|---|
| Slot filter :537 | WOT-SHAPING | Keeps the module's own prefix, slots used across modules, and type designators. | 0177c7eb | high |
| Designator → `@type` :539-542 | UPSTREAM-GAP | Same as the scoped branch of `_fix_type_designator_mapping`. | edbdcf64 | high |
| `_native_slot_context` :63 (called :546) | UPSTREAM-GAP | Calls private upstream API (`_build_element_id`, and resets `context_body`). | 6bc508db | medium |
| Cross-module prefixed `@id` :547-550 | WOT-SHAPING | Terms used across modules resolve to the vocabulary that owns them. | 0177c7eb | high |
| `jsonld_container` / `jsonld_index` :551-557 | UPSTREAM-GAP | Not equivalent to `_apply_root_mapping`: it has no scoped `@context` nesting and does not call `_ensure_index_term`. | 6bc508db | medium |
| SKOS strip :560-561 | WOT-SHAPING | Strips only at the entry level; the merged pass recurses into nested contexts. | a622d8dc | medium |
| DatatypeProperty `@id` strip :562-563 | UPSTREAM-BUG | Same as merged. | e98c2a84 | high |
| uriorcurie → `@vocab` :564-565 | UPSTREAM-GAP | Same as merged. | 9cc0e1aa | high |
| ObjectProperty `xsd:anyURI` → `@id` :566-567 | UPSTREAM-GAP | Same as merged. | edbdcf64 | high |
| String ObjectProperty → `@id` :568-576 | UPSTREAM-GAP | Same as merged, including the designator guard. | 2e19ba5a | high |
| Inlined `@id` strip :577-584 | UPSTREAM-BUG | Runs after the vocab and ObjectProperty fixes; the merged pass runs before them. The conditions look disjoint, so the result is probably the same. | 2e19ba5a | medium |
| Enum `@vocab` :585-588 | UPSTREAM-GAP (partial) | Same as merged. | a3f663cb | high |
| Class terms :590-593 | WOT-SHAPING | Exposes the module's class terms. | 6bc508db | medium |
| Enum aliases filtered by prefix :594-599 | UPSTREAM-GAP | Filters by prefix when adding the aliases; the merged context adds them all and `_remove_non_root_terms` filters later. The result is probably the same. | 76a60518 | medium |
| `_fix_keyed_map_identifier_slots` :600 | UPSTREAM-GAP | Same function as merged. | d84e11c4 | high |

These merged passes have no module counterpart: reserved-slot strip, fixed `id` mapping, uninduced strip, literal strip, linkml-internals strip, and `@version`. Whether anything leaks into module contexts because of this was not checked.

## Config: GEN_OWL_OPTIONS (`config.py:24-32`, used at `pipeline.py:190`)

- `metaclasses: False`: the upstream default `True` adds metamodel triples and punning (owlgen.py:132). Confidence: high.
- `type_objects: False`: `True` makes every slot an ObjectProperty; `False` allows DatatypeProperty. Confidence: high.
- `use_native_uris: False`: IRIs come from `class_uri`/`slot_uri`. This also makes the preprocess renames redundant for IRIs and is the source of the `skos:exactMatch` triples. Confidence: high.
- `skip_vacuous_local_range_axioms: True`: suppresses vacuous local range restrictions. Largely moot because `_clear_constraints` runs first. Confidence: medium.
- `skip_vacuous_min_zero_cardinality_axioms: True`: same caveat. Confidence: medium.
- `consolidate_cardinality_axioms: False`: equals the upstream default; moot after constraint clearing. Confidence: medium-low.
- `skip_abstract_class_as_unionof_subclasses: True`: no covering axioms, which matches the WoT ontology. Confidence: medium.

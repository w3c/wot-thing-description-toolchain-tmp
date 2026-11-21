# Pass reasons proposal: JSON Schema and SHACL post-processing

These are unconfirmed proposals for review. No tag here is final until the maintainer confirms it.

"Ablation" means: this one pass was turned into a no-op on the real TD schema at HEAD, and the output was compared with the normal output (script ran outside the repo, 2026-11-21).

## JSON Schema (`src/wot_toolchain/postprocessors/jsonschema_postprocessor.py`, `src/wot_toolchain/pipeline.py`)

| Pass | Proposed tag | Proposed reason | Evidence | Confidence |
|---|---|---|---|---|
| `designates_type` toggle, pipeline.py:104-130 | UPSTREAM-BUG | Upstream calls `type_ancestors(slot.range)`, which crashes when the range is an enum. The TD schema has no `designates_type` slots, so for TD this toggle does nothing. | edbdcf64; linkml jsonschemagen.py:1037-1038; pipeline.py:104-106 comment; ablation: TD designates_type slots = []; still exercised by tests/test_pipeline_jsonschema_errors.py:26 | high |
| `_fix_extra_slots`, :140 | DEAD | Upstream 1.12.0 already handles `extra_slots` natively. Ablation shows identical output with and without this pass. | 65c659a7 (docstring "linkml gen-jsonschema ignores it"); a6d087e5; linkml jsonschemagen.py:1043-1057; ablation: no-op | high |
| `_flatten_subclasses`, :154 | UNCLEAR | Changes output for `DataSchema` (jsonschema.yaml:271), but no commit or docstring says why. Question for you: does the W3C TD JSON Schema require `dataSchema` to be one flat object instead of separate per-type subclass definitions? | fed93b29 (no docstring); ablation: changes output | low |
| `_build_oneof_dispatch`, :190 | WOT-SHAPING | Builds the W3C `securityScheme` oneOf over known schemes plus a catch-all whose `scheme` must have a prefix. LinkML has no oneOf on a discriminator. | fed93b29; f432e087; wot_security.yaml:247; known-linkml-gaps.md gap #7 (the code comment at :205 says "#9") | high |
| `_build_enum_subset_partitions`, :220 | WOT-SHAPING | Splits `Form` into one variant per `op` subset (root/property/action/event) to match TD 1.1. | 65c659a7; hypermedia.yaml:464; known-linkml-gaps.md gap #8 | high |
| `_narrow_form_subsets`, :274 | WOT-SHAPING | Points each affordance's `forms` at its own Form variant, including the top-level properties of the tree_root class. | fc11b10d; thing_description.yaml:517,610,645,741; tests/test_jsonschema_postprocessor_generic.py:63,73,82 | medium |
| `_dedup_oneof`, :299 | UPSTREAM-GAP | Its live effect on TD is to collapse single-branch `oneOf` (e.g. `title`: `oneOf:[{type:string}]` next to `type:string`, which comes from string\|langString). Upstream already removes duplicate branches but leaves the one-item `oneOf` behind. | 3a46834d (docstring :300); linkml jsonschemagen.py:70,968-990; ablation: no duplicate branches remain after earlier passes, so only the single-branch collapse changes output | medium |
| `_normalize_types`, :318 | UPSTREAM-BUG | LinkML emits a top-level `type` next to `oneOf` for `exactly_one_of`, which conflicts when branches have different types. | fed93b29 (`_fix_oneof_type_conflict` docstring); 7fd91630 rename; ablation: 50 type+oneOf in raw output | medium |
| `_simplify_exclusive_minimum`, :330 | UPSTREAM-GAP | LinkML has no exclusive minimum, so `minimum_value: 0` + `none_of equals_number 0` becomes `minimum`+`not.anyOf.const`. This pass rewrites that to `exclusiveMinimum: 0` (`multipleOf`). | fed93b29 docstring and commit body; linkml jsonschemagen.py:635-640; ablation: 2 occurrences (Integer/NumberSchema.multipleOf) | high |
| `_remove_identifier_slots`, :460 | WOT-SHAPING | LinkML identifier slots are used as map keys and are not JSON members in TD documents. | fed93b29 docstring "internal to LinkML"; ablation: changes output | medium |
| `_remove_excluded_defs`, :440 | COSMETIC | Removes leftover LinkML defs: standalone enum defs (13) and `__identifier_optional` defs (6). The `jsonschema_exclude` branch does nothing for TD because no schema uses that annotation. | fed93b29 comments; linkml jsonschemagen.py:219,887; ablation: changes output, excluded_classes = [] | medium |
| `_resolve_refs`, :491 | WOT-SHAPING | Fixes references after removals: inlines enums, empties `linkml:Any`, maps identifier_optional refs to the base def, and rewrites `definitions` to `$defs`. Nested `_fix_additional_props_anyof` (:512) keeps only the string form for `titles`/`descriptions`, as W3C requires. | fed93b29; f9229feb; f432e087 (#69); known-linkml-gaps.md gap #9 (the code comment at :525 says "#11") | medium |
| `_remove_unreferenced_candidate_defs`, :426 | COSMETIC | Drops defs that nothing references any more (linkml:Any, tree_root, abstract, partitioned classes), based on schema markers rather than hard-coded names. | f0c2ca40; call-site comment :607; ablation: changes output | medium |
| `_clean_metadata`, :568, plus title :611-612 | COSMETIC | Removes per-def description/title and `metamodel_version`, and sets `version`/`title` from the schema. Question for you: is dropping def descriptions a deliberate match to the W3C schema? | fed93b29 (no stated reason); 7fd91630 | medium |

## SHACL (`src/wot_toolchain/postprocessors/shacl_postprocessor.py`)

| Pass | Proposed tag | Proposed reason | Evidence | Confidence |
|---|---|---|---|---|
| `_remove_jsonld_keyword_properties`, :21 (+ `_jsonld_keyword_paths` :12) | WOT-SHAPING | `@context`/`@type` are JSON-LD keywords, not RDF properties, so they get no property shapes. | cc02149b; ablation: drops td#atContext, td#atType | medium |
| `_remove_literal_datatype`, :56 | UPSTREAM-BUG | Upstream emits `sh:datatype rdfs:Literal`, which is not a concrete datatype. The slot already has `sh:nodeKind sh:Literal`. | d84e11c4; docstring :56-57; ablation: changes output | medium |
| langString `sh:or` rewrite, `_langstring_unions` :28 + `post_process_shacl` :83-99 | UPSTREAM-GAP | LinkML SHACL drops heterogeneous `exactly_one_of` branches, so `xsd:string`\|`rdf:langString` is added back. | 9471ee73; comment :67-69 (LinkML discussion #2199); tests/test_shacl_postprocessor.py:30,45; known-linkml-gaps.md gap #12; ablation: only (Thing, td#title) | high |

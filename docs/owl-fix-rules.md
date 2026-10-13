# OWL Fix Rules for Agents

## Accepted Differences (DO NOT FIX)

These are intentional or acceptable — remove from diff lists:

1. **Labels** — JSON key as `rdfs:label` instead of URI local name is fine
2. **`schema:domainIncludes`** — absence is acceptable
3. **`rdfs:Class` dual-typing** — `owl:Class` only is fine
4. **Language tags** — no `@en` on `rdfs:comment` is fine, this is outputed in new linkml version 
5. **Metadata** — license, creator, vann namespace hints, publisher differences are fine
6. **`rdfs:range` vs `schema:rangeIncludes`** — using `rdfs:range` instead of soft `schema:rangeIncludes` is fine (valid OWL)
7. **`rdfs:seeAlso`** — absence on properties is fine
8. **`skos:note`** — extra notes on properties are fine
~~9. Generated-only classes — removed, these need fixing (see T5)~~
10. **`rdfs:isDefinedBy`** — extra presence is fine
11. skos:definition is fine compared to rdfs:comment, but if both are present, they should be identical (no duplicates)

## Hard Constraints

1. **NO postprocessing** — All fixes must be in schema YAML files (`resources/schemas/*.yaml`), never in `owl_postprocessor.py`
2. **Existing tests MUST pass** — `test_golden_diff.py` (index.html, JSON schemas), all other non-OWL tests must not break
3. **JSON Schema output must not change** — JSON schema generation is separate from OWL; schema YAML changes must not alter JSON schema output. The ONLY change that is fine is the following: 10 changed descriptions + 5 added format fields 
4. **index.html must not change** — Spec generation must remain identical
5. **No golden/snapshot updates** without explicit user approval

## Remaining Issues to Fix

### td.ttl

| # | Status | Issue                                                                                                    | Fix Location |
|---|--------|----------------------------------------------------------------------------------------------------------|---|
| T1 | ✅ DONE | `td:hasInstanceConfiguration` ObjectProperty present and correct                                         | — |
| T2 | ✅ DONE | `td:OperationType` class + 18 named individuals generated correctly                                      | — |
| T3 | ✅ DONE | `jsonschema:properties` now in `jsonschema.ttl` (not td.ttl)                                             | — |
| T4 | ✅ DONE | `td:schemaDefinitions` generated — intentional (TD 2.0 addition, no upstream ontology declaration)       | — |
| T5 | ✅ DONE | `td:MultiLanguage` absent from td.ttl; `td:VersionInfo` retained (intentional)                           | — |
| T6 | ✅ DONE | `dcterms:created` and `dcterms:modified` not re-declared in td.ttl — correct. These are external Dublin Core properties reused via JSON-LD context (`dct:created`, `dct:modified`). Upstream ontology intentionally omits them (standard RDF practice: don't re-declare external vocab). Slots remain in schema for JSON Schema and JSON-LD context generation. | — |
| T7 | ❌ OPEN | `td:titleInLanguage` missing `rdfs:range xsd:string` and `rdfs:subPropertyOf dcterms:title` — upstream has `schema:rangeIncludes schema:Text` + subPropertyOf | Schema: add `range: string` and `subproperty_of` to `titles` slot |
| T8 | ❌ OPEN | `td:descriptionInLanguage` missing `rdfs:range xsd:string` and `rdfs:subPropertyOf dcterms:description` — upstream has `schema:rangeIncludes schema:Text` + subPropertyOf | Schema: add `range: string` and `subproperty_of` to `descriptions` slot |
| T9 | ❓ DECISION | `td:hasInstanceConfiguration` and `td:hasSecurityConfiguration` have no `rdfs:range` — matches upstream (upstream also has no range). Correct. | No action needed |

### hctl.ttl

| # | Status | Issue | Fix Location |
|---|--------|---|---|
| H1 | ✅ DONE | Ontology IRI now `https://www.w3.org/2019/wot/hypermedia#` (trailing `#` added) | `hypermedia.yaml` `id` field — done |
| H2 | ✅ DONE | `hctl:hasOperationType` emits as `owl:DatatypeProperty` with `schema:rangeIncludes xsd:string` — upstream has no range, this is acceptable (no blank-node unionOf present) | — |
| H3 | ✅ DONE | Single `rdfs:comment` on `hctl:forContentType` — no duplicate | — |

### jsonschema.ttl

| # | Status | Issue | Fix Location |
|---|--------|---|---|
| J1 | ✅ DONE | `jsonschema:properties` ObjectProperty now in `jsonschema.ttl` | — |
| J2 | ✅ CLOSED | Missing `jsonschema:anyOf` ObjectProperty — out of TD 1.1 spec scope; confirmed with Ege Korkan. See `docs/upstream-compatibility-findings.md` → "Toolchain coverage follow-up". | No action needed |
| J3 | ✅ DONE | `jsonschema:propertyName` DatatypeProperty present | — |
| J4 | ✅ DONE | `maxItems`, `minItems` use `schema:rangeIncludes xsd:nonNegativeInteger`; `multipleOf` uses `schema:rangeIncludes xsd:decimal` — matches upstream; no blank-node issue | — |
| J5 | ✅ DONE | `jsonschema:type` present in generated output — correct. Missing from upstream ontology is an upstream bug. Property is in TD 1.1 spec and JSON-LD context. | — |
| J6 | ✅ DONE | `contentEncoding`, `contentMediaType` have `schema:rangeIncludes xsd:string` | — |
| J7 | ✅ DONE | `maxLength`, `minLength` have `schema:rangeIncludes xsd:nonNegativeInteger` | — |
| J8 | ✅ DONE | No duplicate `rdfs:comment` strings in jsonschema.ttl | — |

### wotsec.ttl

| # | Status | Issue | Fix Location |
|---|--------|---|---|
| W1 | ❌ OPEN | `wotsec:apikeyIn` missing — slot_usage override of `in` with `slot_uri: wotsec:apikeyIn` not emitted as separate property. Upstream has it as independent `owl:DatatypeProperty`. | Preprocessor: slot_usage with different slot_uri needs to produce a separate top-level slot |
| W2 | ✅ DONE | `wotsec:format` now present in wotsec.ttl. Root cause: `_promote_attributes` was wiping `slot_uri = None`. Fixed by preserving `slot_uri` during promotion. | Preprocessor: removed `slot_uri = None` from `_promote_attributes` |
| W3 | ❓ INVESTIGATE | `wotsec:security_scheme_key` — may be needed for JSON-LD round-tripping. Present in generated output. | Needs decision |

### tm.ttl

| # | Status | Issue | Fix Location |
|---|--------|---|---|
| M1 | ❌ OPEN | `tm:hasVersion` should be `td:hasVersion` — upstream target tm.ttl defines `tm:hasVersion` but upstream td.ttl defines `td:hasVersionInfo`. Target tm.ttl has its own `tm:hasVersion` (ObjectProperty) + `tm:Version` class. Need to decide: emit `tm:hasVersion`+`tm:Version` from TM module. | Schema: add Version class and hasVersion slot to thing_model.yaml |
| M2 | ❌ OPEN | `tm:model` missing — defined in upstream td.ttl as `td:model` (DatatypeProperty, domain versionInfo). Target tm.ttl redefines as `tm:model`. | Schema: add model slot to thing_model.yaml |
| M3 | ❌ OPEN | `tm:versionInfo` missing — upstream target has it as `owl:AnnotationProperty` with `rdfs:seeAlso schema:version`. | Schema: add versionInfo to thing_model.yaml |

### Cross-module

| # | Status | Issue | Fix Location |
|---|--------|---|---|
| X1 | ❌ OPEN | `td:OperationType rdfs:subClassOf schema:Enumeration` missing from generated td.ttl — upstream has this. | Schema: add `is_a` or annotation to OperationType enum in hypermedia.yaml |
| X2 | ❌ OPEN | `td:PropertyAffordance rdfs:subClassOf jsonschema:DataSchema` wrong for TD 1.1 — caused by `mixins: [DataSchema]` in thing_description.yaml. Can't remove mixin (breaks JSON Schema). | Preprocessor: strip DataSchema mixin before gen-owl |
| X3 | ✅ DONE | `hctl:forSubProtocol` now present in hctl.ttl. Root cause: `_apply_renames` was wiping `slot_uri = None` after rename. Fixed by preserving `slot_uri` during rename. | Preprocessor: removed `slot_uri = None` from `_apply_renames` |
| X4 | ✅ DONE | DataSchema `name` attribute had no `slot_uri` — gen-owl was emitting spurious `jsonschema:name`. Fixed: `_promote_attributes` now skips attributes without `slot_uri` (implementation artifacts with no OWL mapping). Existing `propertyName` top-level slot with `slot_uri: jsonschema:propertyName` already covers the OWL property. DataSchema `name` is not in TD 1.1 spec table — it's a JSON-LD `@index` artifact. | Preprocessor: skip no-`slot_uri` attributes in `_promote_attributes` |

## Revert Needed

The `_fix_property_labels` function added to `owl_postprocessor.py` this session should be **reverted** — labels are now accepted as-is.

## What Agents Must Verify Before Changing Schema

For each YAML change:
1. Run `uv run pytest tests/ -x -q` — ALL tests must pass
2. Specifically check JSON schema output unchanged: `uv run pytest tests/test_golden_diff.py -x -q`
3. Check OWL output for intended effect
4. Do NOT add new postprocessor code
5. Do NOT update goldens/snapshots

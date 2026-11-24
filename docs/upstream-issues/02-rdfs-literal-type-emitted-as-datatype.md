# A type with `uri: rdfs:Literal` is emitted as a concrete datatype (JSON-LD context and SHACL)

- **linkml version:** 1.12.0 (linkml-runtime 1.12.0); **generators:** `ContextGenerator`, `ShaclGenerator`
- **Classification:** bug (my judgment). `rdfs:Literal` is the class of all literals, not a datatype
  IRI, but both generators treat it as one.
- **Backing canaries:** `test_context_coerces_literal_typed_slot_to_rdfs_literal`,
  `test_shacl_emits_rdfs_literal_datatype` (both in `tests/test_upstream_canaries.py`)

## Reproducer

Schema (default generator options):

```yaml
id: https://example.org/probe
name: probe
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/ex#
  rdfs: http://www.w3.org/2000/01/rdf-schema#
default_prefix: ex
imports: [linkml:types]
types:
  literal:
    typeof: string
    uri: rdfs:Literal
slots:
  label:
    slot_uri: ex:label
    range: literal
classes:
  Thing:
    class_uri: ex:Thing
    slots: [label]
```

- `json.loads(ContextGenerator(schema).serialize())["@context"]["label"]` prints
  `{'@type': 'rdfs:Literal', '@id': 'label'}`.
- `ShaclGenerator(schema).serialize()` emits for `ex:label`:
  `sh:datatype rdfs:Literal ; sh:maxCount 1 ; sh:nodeKind sh:Literal ; sh:order 0 ; sh:path ex:label .`

Effect checked with rdflib 7 JSON-LD parsing: value `"hi"` under that context becomes
`Literal('hi', datatype=URIRef('http://www.w3.org/2000/01/rdf-schema#Literal'))` instead of a plain
string. In SHACL, `xsd:string` and `rdf:langString` values do not have datatype `rdfs:Literal`, so I
expect them to violate the shape; I did not run a SHACL engine to confirm.

**Expected:** no `@type` in the context; in SHACL only `sh:nodeKind sh:Literal`.
**Actual:** `@type: rdfs:Literal` and `sh:datatype rdfs:Literal`.

## Suspected cause

- Context: `linkml/generators/jsonldcontextgen.py:416-421` skips only `xsd:string` and URI ranges and
  otherwise writes `slot_def["@type"] = range_type.uri`.
- SHACL: `linkml/generators/shaclgen.py:719-721` emits `sh:nodeKind sh:Literal` plus
  `sh:datatype <type uri>` for any type URI not in `_NON_LITERAL_TYPE_URIS`.

## Workaround in this repo

- `remove_literal_type_coercion` in `src/wot_toolchain/artifacts/jsonld_context/coercions.py`
- `_remove_literal_datatype` in `src/wot_toolchain/artifacts/shacl/passes.py`

# LinkML issue drafts

Unfiled drafts. Each one is guarded by a canary in `tests/test_upstream_canaries.py` and was verified
against linkml 1.12.0 (linkml-runtime 1.12.0) on 2026-11-21. Bug vs. feature-gap labels are the
author's judgment, as stated in each draft.

## 01: gen-json-schema crashes on a `designates_type` slot whose range is an enum { #draft-01 }

- **linkml version:** 1.12.0 (linkml-runtime 1.12.0); **generator:** `JsonSchemaGenerator`
- **Classification:** bug (crash on a valid schema).
- **Backing canary:** `tests/test_upstream_canaries.py::test_jsonschema_crashes_on_enum_ranged_type_designator`

### Reproducer

Default options; the canary raises the same error with this repo's generator options.

```python
from linkml.generators.jsonschemagen import JsonSchemaGenerator

schema = """
id: https://example.org/probe
name: probe
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/ex#
default_prefix: ex
imports: [linkml:types]
enums:
  Kind:
    permissible_values:
      A: {}
slots:
  kind:
    range: Kind
    designates_type: true
classes:
  A:
    slots: [kind]
"""
JsonSchemaGenerator(schema).serialize()
```

Actual output (last traceback lines):

```
  File ".../linkml/generators/jsonschemagen.py", line 1038, in handle_class_slot
  ...
  File ".../linkml_runtime/utils/schemaview.py", line 942, in get_type
    raise ValueError(msg)
ValueError: No such type: "Kind"
```

**Expected:** a JSON Schema where `kind` is constrained to the type designator value(s) of `A`.
**Actual:** the `ValueError` above; no output.

### Suspected cause

`linkml/generators/jsonschemagen.py:1038` calls `self.schemaview.type_ancestors(slot.range)` for every
`designates_type` slot. `type_ancestors` resolves the name strictly as a type
(`linkml_runtime/utils/schemaview.py:942`), so an enum range raises. Checking
`slot.range in self.schemaview.all_types()` first would probably avoid it (untested).

### Workaround in this repo

`before_generate_class_slot` in `src/wot_toolchain/artifacts/jsonschema/generator.py` hands the upstream
generator a copy of each type designator slot with `designates_type = False`.

## 02: A type with `uri: rdfs:Literal` is emitted as a concrete datatype (JSON-LD context and SHACL) { #draft-02 }

- **linkml version:** 1.12.0 (linkml-runtime 1.12.0); **generators:** `ContextGenerator`, `ShaclGenerator`
- **Classification:** bug (my judgment). `rdfs:Literal` is the class of all literals, not a datatype
  IRI, but both generators treat it as one.
- **Backing canaries:** `test_context_coerces_literal_typed_slot_to_rdfs_literal`,
  `test_shacl_emits_rdfs_literal_datatype` (both in `tests/test_upstream_canaries.py`)

### Reproducer

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

### Suspected cause

- Context: `linkml/generators/jsonldcontextgen.py:416-421` skips only `xsd:string` and URI ranges and
  otherwise writes `slot_def["@type"] = range_type.uri`.
- SHACL: `linkml/generators/shaclgen.py:719-721` emits `sh:nodeKind sh:Literal` plus
  `sh:datatype <type uri>` for any type URI not in `_NON_LITERAL_TYPE_URIS`.

### Workaround in this repo

- `remove_literal_type_coercion` in `src/wot_toolchain/artifacts/jsonld_context/coercions.py`
- `_remove_literal_datatype` in `src/wot_toolchain/artifacts/shacl/passes.py`

## 03: gen-jsonld-context: no way to suppress the SKOS scoped context on enum-ranged slots { #draft-03 }

- **linkml version:** 1.12.0 (linkml-runtime 1.12.0); **generator:** `ContextGenerator`
- **Classification:** feature gap (my judgment). The output is intentional upstream (`ENUM_CONTEXT`
  constant); it is unwanted when the target context must match an existing vocabulary context that
  serializes enum values as plain strings.
- **Backing canary:** `tests/test_upstream_canaries.py::test_context_emits_skos_context_for_enum_ranged_slot`

### Reproducer

```python
import json
from linkml.generators.jsonldcontextgen import ContextGenerator

schema = """
id: https://example.org/probe
name: probe
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/ex#
default_prefix: ex
imports: [linkml:types]
enums:
  Color:
    permissible_values:
      red:
        meaning: ex:Red
slots:
  color:
    range: Color
classes:
  Thing:
    slots: [color]
"""
print(json.loads(ContextGenerator(schema).serialize())["@context"]["color"])
```

Actual output:

```
{'@context': {'text': 'skos:notation', 'description': 'skos:prefLabel', 'meaning': '@id'}, '@id': 'color'}
```

**Desired:** an option (for example `--no-enum-context`) that emits `{'@id': 'color'}` without the
  scoped `@context` and without adding the `skos` prefix.
**Actual:** every enum-ranged slot gets the SKOS scoped context; there is no flag to turn it off.

### Cause

`linkml/generators/jsonldcontextgen.py:30-34` defines `ENUM_CONTEXT`; `visit_slot` assigns it at
line 406 (and merges it with `@vocab` at line 404 for vocab-eligible enums) and adds the `skos`
prefix at lines 408-412. No generator option gates this.

### Workaround in this repo

`strip_skos_enum_contexts` in `src/wot_toolchain/artifacts/jsonld_context/coercions.py`
deletes any scoped `@context` that contains the keys `text`, `description`, `meaning`.

## 04: gen-jsonld-context coerces a `range: Any` slot to `@type: @id`, even when it implements `owl:DatatypeProperty` { #draft-04 }

- **linkml version:** 1.12.0 (linkml-runtime 1.12.0); **generator:** `ContextGenerator`
- **Classification:** bug (my judgment). A `linkml:Any` range admits literal values, and
  `@type: @id` turns string values into IRIs. Whether the generator should also honour
  `implements: [owl:DatatypeProperty]` is a design question for upstream.
- **Backing canary:** `tests/test_upstream_canaries.py::test_context_coerces_datatype_property_to_id`

### Reproducer

```python
import json
from linkml.generators.jsonldcontextgen import ContextGenerator

schema = """
id: https://example.org/probe
name: probe
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/ex#
  owl: http://www.w3.org/2002/07/owl#
default_prefix: ex
imports: [linkml:types]
slots:
  value:
    range: Any
    implements: [owl:DatatypeProperty]
classes:
  Any:
    class_uri: linkml:Any
  Thing:
    slots: [value]
"""
print(json.loads(ContextGenerator(schema).serialize())["@context"]["value"])
```

Actual output:

```
{'@type': '@id', '@id': 'value'}
```

Effect checked with rdflib 7 JSON-LD parsing: under `{"value": {"@type": "@id"}}` the instance value
`"42"` became `URIRef('file:///<cwd>/42')` instead of a literal.

**Expected:** `{'@id': 'value'}` (no type coercion).
**Actual:** `{'@type': '@id', '@id': 'value'}`.

### Suspected cause

`linkml/generators/jsonldcontextgen.py:383-394`: any slot whose range is in `self.schema.classes`
gets `@type: @id`. There is no exception for a class with `class_uri: linkml:Any`, and `implements`
is not consulted.

### Workaround in this repo

`strip_datatype_property_id_coercion` in
`src/wot_toolchain/artifacts/jsonld_context/coercions.py` removes `@type: @id` from slots whose
`implements` contains `owl:DatatypeProperty`.

## 05: gen-jsonld-context emits `@type: @id` for inlined slots whose range class has no identifier { #draft-05 }

- **linkml version:** 1.12.0 (linkml-runtime 1.12.0); **generator:** `ContextGenerator`
- **Classification:** feature gap / cosmetic, not a wrong-RDF bug (my judgment, see below).
- **Backing canary:** `tests/test_upstream_canaries.py::test_context_coerces_inlined_class_without_identifier_to_id`

### Reproducer

```python
import json
from linkml.generators.jsonldcontextgen import ContextGenerator

schema = """
id: https://example.org/probe
name: probe
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/ex#
default_prefix: ex
imports: [linkml:types]
slots:
  part:
    range: Part
    inlined: true
classes:
  Part:
    attributes:
      n:
        range: string
  Thing:
    slots: [part]
"""
print(json.loads(ContextGenerator(schema).serialize())["@context"]["part"])
```

Actual output:

```
{'@type': '@id', '@id': 'part'}
```

**Expected:** `{'@id': 'part'}`. `Part` has no identifier and `part` is inlined, so its values are always
embedded objects and can never be IRI strings.

**Impact:** JSON-LD applies `@type: @id` only to string values. With rdflib 7, `{"part": {"n": "x"}}` under this
context parsed to a blank node with `ex:n "x"`, which is correct. So the RDF is not wrong for valid
data. The coercion is redundant, and it makes the generated context differ from hand-written
contexts (in this repo, the W3C WoT TD context) that omit it.

### Suspected cause

`linkml/generators/jsonldcontextgen.py:383-394`: every class-ranged slot gets `@type: @id`. The
generator does not check `inlined` or whether the range class has an identifier.

### Workaround in this repo

`strip_inlined_class_id_coercion` in
`src/wot_toolchain/artifacts/jsonld_context/coercions.py` removes `@type: @id` when
`SchemaView.is_inlined(slot)` is true, the range class has no identifier slot, and the slot does not
implement `owl:ObjectProperty`.

## 06: gen-owl emits IRI-valued element annotations (rdfs:subPropertyOf, rdfs:seeAlso, ...) as string literals { #draft-06 }

- **linkml version:** 1.12.0 (linkml-runtime 1.12.0); **generator:** `OwlSchemaGenerator`
- **Classification (my judgment):** bug for `rdfs:subPropertyOf` / `rdfs:subClassOf`, whose objects must
  be resources (a literal object of `rdfs:subPropertyOf` is not valid OWL 2 DL); feature gap for
  `rdfs:seeAlso` / `rdfs:isDefinedBy`, since there is no way to mark an annotation value as an IRI.
- **Backing canaries** (`tests/test_upstream_canaries.py`): `test_owl_emits_subproperty_annotation_as_literal_curie`,
  `test_owl_emits_uri_annotation_as_literal` (3 parametrizations)

### Reproducer (default options; the canaries also reproduce it with this repo's `GEN_OWL_OPTIONS`)

```python
from linkml.generators.owlgen import OwlSchemaGenerator
from rdflib import Graph, URIRef
from rdflib.namespace import RDFS
schema = """
id: https://example.org/probe
name: probe
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/ex#
  rdfs: http://www.w3.org/2000/01/rdf-schema#
  dcterms: http://purl.org/dc/terms/
default_prefix: ex
imports: [linkml:types]
enums:
  Color:
    enum_uri: ex:Color
    annotations: {rdfs:subClassOf: "http://schema.org/Enumeration", rdfs:isDefinedBy: "https://example.org/probe"}
    permissible_values: {red: {meaning: ex:Red}}
slots:
  label:
    slot_uri: ex:label
    annotations: {rdfs:subPropertyOf: dcterms:title, rdfs:seeAlso: "http://schema.org/name"}
classes:
  Thing: {class_uri: ex:Thing, slots: [label]}
"""
g = Graph().parse(data=OwlSchemaGenerator(schema).serialize(), format="turtle")
for s, p in [("label", RDFS.subPropertyOf), ("label", RDFS.seeAlso),
             ("Color", RDFS.subClassOf), ("Color", RDFS.isDefinedBy)]:
    for o in g.objects(URIRef("https://example.org/ex#" + s), p):
        print(f"ex:{s} {g.qname(p)} {o!r}")
```

Actual output (stderr deprecation notices omitted):
```
ex:label rdfs:subPropertyOf rdflib.term.Literal('dcterms:title')
ex:label rdfs:seeAlso rdflib.term.Literal('http://schema.org/name')
ex:Color rdfs:subClassOf rdflib.term.Literal('http://schema.org/Enumeration')
ex:Color rdfs:isDefinedBy rdflib.term.Literal('https://example.org/probe')
```

**Expected:** IRI objects, with the CURIE `dcterms:title` expanded. **Actual:** plain string literals.

**Suspected cause:** `linkml/generators/owlgen.py:424-442` (`add_metadata`): the annotation key is expanded to an IRI, but
every string value goes through `self._literal(v.value, e)` (line 439), which always returns a
`Literal`. The value is never checked for being a CURIE or IRI.

**Workaround in this repo:** the `WotOwlGenerator.add_metadata` override in
`src/wot_toolchain/artifacts/owl/generator.py`.

## 07: gen-shacl ignores `exactly_one_of` ranges and silently drops the alternative datatype branches { #draft-07 }

- **linkml version:** 1.12.0 (linkml-runtime 1.12.0); **generator:** `ShaclGenerator`
- **Classification:** bug (my judgment). The schema admits `rdf:langString` values; the shape rejects
  them without any warning. The same alternatives written as `any_of` are handled.
- **Backing canary:** `tests/test_upstream_canaries.py::test_shacl_drops_langstring_branch_of_exactly_one_of`

### Reproducer (default options)

```python
from linkml.generators.shaclgen import ShaclGenerator

schema = """
id: https://example.org/probe
name: probe
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/ex#
  rdf: http://www.w3.org/1999/02/22-rdf-syntax-ns#
default_prefix: ex
imports: [linkml:types]
types:
  langString: {uri: rdf:langString, base: str}
slots:
  title:
    slot_uri: ex:title
    range: string
classes:
  Thing:
    class_uri: ex:Thing
    slots: [title]
    slot_usage:
      title:
        exactly_one_of: [{range: string}, {range: langString}]
"""
print(ShaclGenerator(schema).serialize())
```

Actual property shape for `ex:title` (`rdf:langString` appears nowhere in the output):

```
_:c14n0 sh:datatype xsd:string ;
	sh:maxCount 1 ;
	sh:nodeKind sh:Literal ;
	sh:order 0 ;
	sh:path ex:title .
```

Replacing `exactly_one_of` with `any_of` in the same schema yields an `sh:or` over
(`sh:datatype xsd:string`) and (`sh:datatype rdf:langString`), each with `sh:nodeKind sh:Literal`.

**Expected:** both branches represented, e.g. `sh:xone` (or `sh:or`, which is equivalent here because
the datatypes are disjoint). **Actual:** only the slot's base range `xsd:string` is kept.

**Suspected cause:** `linkml/generators/shaclgen.py:314-324` builds `sh:or` from `any_of`; the file contains no
`exactly_one_of` handling at all (`grep -c exactly_one_of shaclgen.py` returns 0).

**Workaround in this repo:** the pass `rewrite_langstring_union_to_sh_or` in
`src/wot_toolchain/artifacts/shacl/passes.py`; its comment cites linkml discussion #2199
(not checked).

# gen-shacl ignores `exactly_one_of` ranges and silently drops the alternative datatype branches

- **linkml version:** 1.12.0 (linkml-runtime 1.12.0); **generator:** `ShaclGenerator`
- **Classification:** bug (my judgment). The schema admits `rdf:langString` values; the shape rejects
  them without any warning. The same alternatives written as `any_of` are handled.
- **Backing canary:** `tests/test_upstream_canaries.py::test_shacl_drops_langstring_branch_of_exactly_one_of`

## Reproducer (default options)

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

**Workaround in this repo:** `post_process_shacl` (with helper `_langstring_unions`) in
`src/wot_toolchain/postprocessors/shacl_postprocessor.py`; its comment cites linkml discussion #2199
(not checked).

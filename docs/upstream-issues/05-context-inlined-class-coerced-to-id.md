# gen-jsonld-context emits `@type: @id` for inlined slots whose range class has no identifier

- **linkml version:** 1.12.0 (linkml-runtime 1.12.0); **generator:** `ContextGenerator`
- **Classification:** feature gap / cosmetic, not a wrong-RDF bug (my judgment, see below).
- **Backing canary:** `tests/test_upstream_canaries.py::test_context_coerces_inlined_class_without_identifier_to_id`

## Reproducer

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

## Suspected cause

`linkml/generators/jsonldcontextgen.py:383-394`: every class-ranged slot gets `@type: @id`. The
generator does not check `inlined` or whether the range class has an identifier.

## Workaround in this repo

`strip_inlined_class_id_coercion` in
`src/wot_toolchain/artifacts/jsonld_context/coercions.py` removes `@type: @id` when
`SchemaView.is_inlined(slot)` is true, the range class has no identifier slot, and the slot does not
implement `owl:ObjectProperty`.

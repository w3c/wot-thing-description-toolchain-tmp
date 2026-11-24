# gen-jsonld-context coerces a `range: Any` slot to `@type: @id`, even when it implements `owl:DatatypeProperty`

- **linkml version:** 1.12.0 (linkml-runtime 1.12.0); **generator:** `ContextGenerator`
- **Classification:** bug (my judgment). A `linkml:Any` range admits literal values, and
  `@type: @id` turns string values into IRIs. Whether the generator should also honour
  `implements: [owl:DatatypeProperty]` is a design question for upstream.
- **Backing canary:** `tests/test_upstream_canaries.py::test_context_coerces_datatype_property_to_id`

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

## Suspected cause

`linkml/generators/jsonldcontextgen.py:383-394`: any slot whose range is in `self.schema.classes`
gets `@type: @id`. There is no exception for a class with `class_uri: linkml:Any`, and `implements`
is not consulted.

## Workaround in this repo

`strip_datatype_property_id_coercion` in
`src/wot_toolchain/artifacts/jsonld_context/coercions.py` removes `@type: @id` from slots whose
`implements` contains `owl:DatatypeProperty`.

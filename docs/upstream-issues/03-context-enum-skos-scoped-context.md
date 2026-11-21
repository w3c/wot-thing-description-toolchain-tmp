# gen-jsonld-context: no way to suppress the SKOS scoped context on enum-ranged slots

- **linkml version:** 1.12.0 (linkml-runtime 1.12.0); **generator:** `ContextGenerator`
- **Classification:** feature gap (my judgment). The output is intentional upstream (`ENUM_CONTEXT`
  constant); it is unwanted when the target context must match an existing vocabulary context that
  serializes enum values as plain strings.
- **Backing canary:** `tests/test_upstream_canaries.py::test_context_emits_skos_context_for_enum_ranged_slot`

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

## Cause

`linkml/generators/jsonldcontextgen.py:30-34` defines `ENUM_CONTEXT`; `visit_slot` assigns it at
line 406 (and merges it with `@vocab` at line 404 for vocab-eligible enums) and adds the `skos`
prefix at lines 408-412. No generator option gates this.

## Workaround in this repo

`_strip_skos_enum_contexts` in `src/wot_toolchain/postprocessors/jsonld_context_postprocessor.py`
deletes any scoped `@context` that contains the keys `text`, `description`, `meaning`.

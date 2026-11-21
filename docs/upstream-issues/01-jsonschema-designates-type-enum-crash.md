# gen-json-schema crashes on a `designates_type` slot whose range is an enum

- **linkml version:** 1.12.0 (linkml-runtime 1.12.0); **generator:** `JsonSchemaGenerator`
- **Classification:** bug (crash on a valid schema).
- **Backing canary:** `tests/test_upstream_canaries.py::test_jsonschema_crashes_on_enum_ranged_type_designator`

## Reproducer

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

## Suspected cause

`linkml/generators/jsonschemagen.py:1038` calls `self.schemaview.type_ancestors(slot.range)` for every
`designates_type` slot. `type_ancestors` resolves the name strictly as a type
(`linkml_runtime/utils/schemaview.py:942`), so an enum range raises. Checking
`slot.range in self.schemaview.all_types()` first would probably avoid it (untested).

## Workaround in this repo

`_gen_jsonschema` in `src/wot_toolchain/pipeline.py` temporarily sets `designates_type = False` on every
slot before calling the generator and restores it afterwards.

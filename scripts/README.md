# Scripts

## `prepare_upstream_template.py`

Temporary migration helper that replaces inline examples in the upstream W3C template (`resources/upstream/html/index.template.html`) with `%snippet()%` placeholder calls, producing `resources/index.template.html`. This script will be removed once the snippet system is merged upstream.

```bash
uv run python scripts/prepare_upstream_template.py
```

## `validate_snippets.py`

Validates the snippets in `resources/snippets/` after generation: Thing Description snippets against the generated JSON Schema (`resources/gens/jsonschema/jsonschema.json`), Thing Model snippets (root `"@type": "tm:ThingModel"`) against the upstream TM JSON Schema. Snippets with `validate: false` in `_snippets.yaml` are skipped. Exits 1 when a snippet is invalid, 2 when a JSON Schema or `_snippets.yaml` cannot be used. CI runs it after generation.

```bash
uv run wot-toolchain generate-wot-resources
uv run python scripts/validate_snippets.py
```

`--snippets`, `--td-schema` and `--tm-schema` name other inputs.

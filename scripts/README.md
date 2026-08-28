# Scripts

## `prepare_upstream_template.py`

Temporary migration helper that replaces inline examples in the upstream W3C template (`resources/upstream/html/index.template.html`) with `%snippet()%` placeholder calls, producing `resources/index.template.html`. This script will be removed once the snippet system is merged upstream.

```bash
uv run python scripts/prepare_upstream_template.py
```

Run generation and show only snippet validation errors and warnings.

```bash
uv run wotis generate-wot-resources -d 2>&1 | grep -iE "snippet|Snippet"
```

If errors: check the failing `.json` file in `resources/snippets/`. Common causes:
- Snippet is not a complete valid TD/TM (missing required fields).
- `validate: false` missing in `_snippets.yaml` for a non-TD/TM snippet.
- Snippet `id` in `_snippets.yaml` is not unique across all snippets.

To check a specific snippet manually against the generated schema:
```bash
python3 -c "
import json, sys, re
from pathlib import Path
from jsonschema import validate, ValidationError

schema = json.load(open('resources/gens/jsonschema/jsonschema.json'))
snippet_path = Path(sys.argv[1])
# strip JSONC comments and front-matter block
text = snippet_path.read_text()
try:
    instance = json.loads(text)
    validate(instance=instance, schema=schema)
    print('OK', snippet_path.name)
except ValidationError as e:
    print('FAIL', snippet_path.name, '->', e.message)
except json.JSONDecodeError as e:
    print('PARSE ERROR', snippet_path.name, '->', e)
" resources/snippets/SNIPPET_NAME.json
```

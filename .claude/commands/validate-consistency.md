Validate cross-artifact consistency after a schema change. Generates fresh artifacts, then cross-checks them for semantic drift.

**Step 1 — generate:**
```bash
uv run wotis generate-wot-resources -d 2>&1 | grep -E "ERROR|WARNING"
```

**Step 2 — JSON Schema structure:**
```bash
python3 -c "
import json, sys
s = json.load(open('resources/gens/jsonschema/jsonschema.json'))
missing = {'\$schema', '\$defs', 'title'} - set(s.keys())
if missing:
    print('FAIL JSON Schema missing keys:', missing); sys.exit(1)
print('OK JSON Schema — defs count:', len(s.get('\$defs', {})))
"
```

**Step 3 — JSON-LD context structure:**
```bash
python3 -c "
import json, sys
ctx = json.load(open('resources/gens/jsonldcontext/context.jsonld'))
if '@context' not in ctx:
    print('FAIL context.jsonld missing @context'); sys.exit(1)
print('OK JSON-LD context — terms count:', len(ctx['@context']))
"
```

**Step 4 — cross-check orphan terms (classes in schema vs context):**
```bash
python3 -c "
import json
schema = json.load(open('resources/gens/jsonschema/jsonschema.json'))
ctx = json.load(open('resources/gens/jsonldcontext/context.jsonld'))
defs = set(schema.get('\$defs', {}).keys())
raw_ctx = ctx.get('@context', {})
terms = set(raw_ctx.keys()) if isinstance(raw_ctx, dict) else set()
primitives = {'string','integer','number','boolean','object','array','null'}
ns_terms = {'@vocab','@version','@language','td','hctl','wotsec','jsonschema','tm','xsd','rdf','rdfs','owl','schema','dcterms'}
schema_only = defs - terms - primitives
ctx_only = terms - defs - ns_terms
if schema_only:
    print('In JSON Schema only (missing from context):', sorted(schema_only)[:20])
if ctx_only:
    print('In context only (missing from schema):', sorted(ctx_only)[:20])
if not schema_only and not ctx_only:
    print('OK no orphan terms')
"
```

**Step 5 — TD instance gate:**
```bash
uv run pytest tests/test_td_instance_gate.py -v --tb=short 2>&1 | tail -40
```

**Step 6 — diff generated JSON Schema vs manual golden:**
```bash
python3 -c "
import json, difflib, pathlib
gen_path = pathlib.Path('resources/gens/jsonschema/jsonschema.json')
gold_path = pathlib.Path('tests/manual_goldens/jsonschema/td-json-schema-validation.json')
if not gold_path.exists():
    print('Golden not found (not blocking)')
else:
    gen = json.dumps(json.load(gen_path.open()), sort_keys=True, indent=2).splitlines()
    gold = json.dumps(json.load(gold_path.open()), sort_keys=True, indent=2).splitlines()
    diff = list(difflib.unified_diff(gold, gen, 'golden', 'generated', lineterm='', n=2))
    if diff:
        print(f'JSON Schema drift: {len(diff)} changed lines (first 40):')
        print('\n'.join(diff[:40]))
    else:
        print('OK JSON Schema matches golden')
"
```

**Step 7 — diff generated JSON-LD context vs manual golden:**
```bash
python3 -c "
import json, difflib, glob, pathlib
gen_path = pathlib.Path('resources/gens/jsonldcontext/context.jsonld')
goldens = sorted(glob.glob('tests/manual_goldens/jsonld-context/*.jsonld'))
if not goldens:
    print('No JSON-LD golden found (not blocking)')
else:
    gen = json.dumps(json.load(gen_path.open()), sort_keys=True, indent=2).splitlines()
    gold = json.dumps(json.load(open(goldens[0])), sort_keys=True, indent=2).splitlines()
    diff = list(difflib.unified_diff(gold, gen, 'golden', 'generated', lineterm='', n=2))
    if diff:
        print(f'JSON-LD context drift: {len(diff)} changed lines (first 40):')
        print('\n'.join(diff[:40]))
    else:
        print('OK JSON-LD context matches golden')
"
```

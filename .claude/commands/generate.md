Run the full WoTIS pipeline (resources + spec HTML) and surface only warnings and errors.

```bash
uv run wotis generate-wot-resources -d 2>&1 | grep -E "ERROR|WARNING|error|warning" | grep -v "^$"
```

If no output: pipeline clean. If errors appear: fix before running tests.

After generation, confirm key artifacts exist and are non-empty:
```bash
for f in resources/gens/jsonschema/jsonschema.json resources/gens/jsonldcontext/context.jsonld resources/gens/shacl/shapes.shacl.ttl resources/gens/owl/ontology.owl.ttl resources/gens/index.html; do
  [ -s "$f" ] && echo "OK $f" || echo "MISSING/EMPTY $f"
done
```

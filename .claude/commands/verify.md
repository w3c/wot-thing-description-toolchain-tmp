Run the full verification loop after a schema or postprocessor change. Usage: `/verify`

**Step 1 — ensure dependencies are current:**
```bash
uv sync
```

**Step 2 — regenerate all artifacts:**
```bash
uv run wotis generate-wot-resources -d 2>&1 | tee /tmp/wotis-generate.log
grep -E "ERROR" /tmp/wotis-generate.log
```
Must exit with no ERROR lines. If any ERROR: stop and fix before continuing.

**Step 3 — check for known-noise warnings (ignore these):**
- `DeprecationWarning` from `owlgen.py` lines 244/247/250
- `WARNING:linkml.generators.owlgen: Multiple owl types`

Any other WARNING line: investigate.

**Step 4 — validate snippets:**
```bash
uv run wotis generate-wot-resources -d 2>&1 | grep -iE "snippet"
```
Every snippet must pass. `validate: false` only acceptable for non-TD/TM snippets.

**Step 5 — run tests:**
```bash
uv run pytest tests/ -v 2>&1 | tail -20
```
All tests must pass. xfail is acceptable; XPASS or ERROR is not.

**Step 6 — check priority artifacts exist and are non-empty:**
```bash
for f in resources/gens/jsonschema/jsonschema.json \
          resources/gens/index.html \
          resources/gens/linkml/linkml.yaml; do
  [ -s "$f" ] && echo "OK: $f" || echo "MISSING OR EMPTY: $f"
done
ls resources/gens/assertions/*.csv 2>/dev/null | head -5
```

**Step 7 — report.**

State clearly: CLEAN (all steps passed) or BLOCKED (list exact errors). Do not declare a change complete while any step fails.

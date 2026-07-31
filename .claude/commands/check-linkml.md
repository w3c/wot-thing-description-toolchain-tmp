Check whether a LinkML feature exists natively before writing a postprocessor. Usage: `/check-linkml <feature or question>`

The goal is to prevent postprocessors for things LinkML already supports. First check `KNOWN_LINKML_GAPS.md` — if the gap is already documented there, skip to the conclusion. Otherwise run all steps below.

**Step 1 — LinkML metamodel docs (what is valid in LinkML YAML schemas):**

Fetch and search these pages for the feature. These document the schema language itself — valid slot meta-slots, annotations, and class constructs.
- https://linkml.io/linkml-model/latest/docs/ (metamodel overview)
- https://linkml.io/linkml-model/latest/docs/SlotDefinition/ (all slot meta-slots)
- https://linkml.io/linkml-model/latest/docs/ClassDefinition/ (all class meta-slots)
- Source: https://github.com/linkml/linkml-model/tree/main/linkml_model

**Step 2 — LinkML generator docs (what generators actually produce):**

Fetch and search these pages for generator-specific behavior and known limitations:
- https://linkml.io/linkml/generators/json-schema.html
- https://linkml.io/linkml/generators/jsonld-context.html
- https://linkml.io/linkml/generators/shacl.html
- https://linkml.io/linkml/generators/owl.html
- https://linkml.io/linkml/schemas/slots.html

**Step 3 — LinkML GitHub open issues and PRs (both repos):**

Use the most relevant label(s) from this list to narrow the search. Pick the label(s) that match the artifact or feature area:

| Area | Labels to use |
|---|---|
| JSON Schema generator | `generator-jsonschema` |
| JSON-LD context generator | `generator-jsonld` |
| SHACL generator | `generator-shacl` |
| OWL generator | `generator-owl` |
| LinkML metamodel constructs | `metamodel`, `metamodel-compat`, `linkml-model` |
| Schema loading/validation | `loading`, `linkml-validate`, `schemaview` |
| Prefix / namespace handling | `prefixes` |
| Slot/class features | `rules`, `arrays`, `mapping` |
| Bug in any generator | `bug` + generator label |
| New feature request | `enhancement` + generator label |

```bash
curl -s "https://api.github.com/search/issues?q=$ARGUMENTS+repo:linkml/linkml+is:open+label:generator-jsonschema+label:generator-jsonld&per_page=5" | python3 -c "
import sys, json
results = json.load(sys.stdin).get('items', [])
print('=== linkml/linkml open (labeled) ===')
print('(none)') if not results else [print(r['number'], r['state'], r['title'], '\n ', r['html_url']) for r in results]
"
curl -s "https://api.github.com/search/issues?q=$ARGUMENTS+repo:linkml/linkml-model+is:open&per_page=5" | python3 -c "
import sys, json
results = json.load(sys.stdin).get('items', [])
print('=== linkml/linkml-model open ===')
print('(none)') if not results else [print(r['number'], r['state'], r['title'], '\n ', r['html_url']) for r in results]
"
```

Adjust the `label:` filters in the URL to match the feature area from the table above.

**Step 4 — LinkML GitHub closed/merged PRs (may already be released):**
```bash
curl -s "https://api.github.com/search/issues?q=$ARGUMENTS+repo:linkml/linkml+is:closed+label:generator-jsonschema&per_page=5" | python3 -c "
import sys, json
results = json.load(sys.stdin).get('items', [])
print('=== linkml/linkml closed (labeled) ===')
print('(none)') if not results else [print(r['number'], r['state'], r['title'], '\n ', r['html_url']) for r in results]
"
```

Adjust label filter to match the area. Also search without a label filter if no labeled results found.

**Step 5 — check installed linkml version:**
```bash
uv run python3 -c "import linkml; print('linkml version:', linkml.__version__)"
```

**Step 6 — conclusion.**

Based on the above, answer:
- Is the feature valid LinkML YAML (metamodel supports it)?
- Does the relevant generator actually emit it correctly in the installed version?
- Is it supported in a newer version not yet pinned in `pyproject.toml`?
- Is there an open PR that adds it? (link it, note expected release)
- Is it genuinely missing from both schema language and generator? (only then: postprocessor is justified)

State clearly: **USE LINKML NATIVE** or **POSTPROCESSOR JUSTIFIED** with reasoning. If justified, add the gap to `KNOWN_LINKML_GAPS.md`.

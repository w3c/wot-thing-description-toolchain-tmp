Review a PR against all WOTIS project rules. Usage: `/review-pr <PR_NUMBER>`

Fetch the PR and review it across all dimensions: schema annotations, postprocessor correctness, snippet validity, CI pipeline coverage, golden drift, and cross-artifact consistency.

**Current priority artifacts (verify these; others are lower priority for now):**
- `resources/gens/jsonschema/jsonschema.json` — JSON Schema correctness
- `resources/gens/assertions/` — assertion CSVs (IDs match anchors in index.html)
- `resources/gens/linkml/linkml.yaml` — generated LinkML export
- `resources/gens/index.html` — HTML spec (auto-generated sections only; see HTML Correctness in AGENTS.md)

SHACL, OWL, and JSON-LD context are generated but not the current correctness focus — flag obvious errors but do not block on them.

**Step 1 — fetch PR metadata:**
```bash
curl -s "https://api.github.com/repos/w3c/wot-thing-description-toolchain-tmp/pulls/$ARGUMENTS" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Title:', d['title'])
print('Author:', d['user']['login'])
print('Base:', d['base']['ref'])
print('Head SHA:', d['head']['sha'])
print('Fork repo:', d['head']['repo']['full_name'])
print('Additions:', d['additions'], '| Deletions:', d['deletions'], '| Files:', d['changed_files'])
print()
print('Body:')
print(d.get('body','(no description)'))
" 2>/dev/null
```

**Step 2 — list changed files:**
```bash
curl -s "https://api.github.com/repos/w3c/wot-thing-description-toolchain-tmp/pulls/$ARGUMENTS/files" | python3 -c "
import sys, json
for f in json.load(sys.stdin):
    print(f['status'].upper()[:3], f'+{f[\"additions\"]}/-{f[\"deletions\"]}', f['filename'])
"
```

**Step 3 — schema annotation review (if any schema YAML changed).**

For each modified `resources/schemas/*.yaml`, use the `mcpmarket-me:linkml-review` plugin to review it, then manually check:
- `spec_description` present → base `description` also updated?
- RFC refs use `[[RFC####]]` syntax, not bare URLs?
- `spec_content` segment IDs follow `td-{kebab-case}` and are unique in file?
- `spec_type_values` with `mode: one_of` is exhaustive?
- No `spec_*` annotation on a slot that also has `spec_exclude: true`?

Then verify the change produces correct output in the **priority artifacts**:
- JSON Schema: slot/class changes reflected correctly (type, required, additionalProperties)?
- Assertions CSV: new normative statements have a `td-{kebab-case}` anchor and appear in the CSV?
- index.html (auto-generated sections): vocabulary table rows match schema (name, type, optional/mandatory)?
- linkml.yaml: schema export is structurally valid?

**Step 4 — postprocessor review (if postprocessors changed).**

Check:
- Does the postprocessor have a comment citing the W3C spec section it satisfies?
- Is the fix scoped to one artifact type (not mixing JSON Schema + context logic)?
- Is the postprocessor tested directly (not only via full pipeline)?

**Step 5 — snippet review (if snippets changed).**
```bash
uv run wotis generate-wot-resources -d 2>&1 | grep -iE "snippet|ERROR|WARNING"
```
- Every `.jsonc` must have a unique `id` in its front-matter.
- `// @hide-start` / `// @hide-end` used only for boilerplate, not to mask invalid sections.
- `validate: false` only for non-TD/TM snippets.
- Groups in `resources/snippets/groups/*.yaml` reference existing `.jsonc` files?

**Step 6 — CI pipeline review (if `.github/workflows/` changed).**

Check:
- All 4 jobs present: `static-analysis`, `build`, `test-gates`, `golden-diff`?
- `build` job generates artifacts and uploads them before test jobs run?
- `linkml-lint` non-blocking now but has a path to becoming blocking?
- Golden diff covers priority artifacts: `jsonschema.json`, assertion CSVs, `index.html`?
- Snippet validation step present?

**Step 7 — known-failures review (if anything under `tests/known_failures/` changed).**
- New entries must be valid TD files only (name contains `-valid`).
- Every entry must correspond to a GitHub issue (check PR description).

**Step 8 — golden files review (if `tests/manual_goldens/` changed).**
- Require explicit justification in PR description.
- Confirm maintainer has approved the golden update.

**Step 9 — summary.**

Produce a review with:
- APPROVE / REQUEST_CHANGES / COMMENT verdict
- Blocking issues (must fix before merge)
- Non-blocking suggestions
- Confirmed checklist items from AGENTS.md

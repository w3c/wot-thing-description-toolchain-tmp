# Snippet Authoring Guide

**Author:** Mahda Noura (mahda.noura@siemens.com)
**Date:** 29.10.2026

---

Worked examples for authoring TD/TM JSON snippets rendered in the generated specification.

For schema validation, see `resources/schemas/snippet_schema.yaml`.

---

## 1. Naming Conventions

**Rule: snippet file names use kebab-case matching the logical topic.**

```
action-serialization.json     # good — topic is clear
simple-td.json                # good
myThing_example.json          # wrong — not kebab-case
```

**Rule: `id` in `_snippets.yaml` must be globally unique and use the pattern `{topic}-{qualifier}`.**

Rationale: the `id` becomes the HTML element ID used for cross-referencing with `[[[#id]]]` in the spec. Collisions break ReSpec anchors. Before assigning an `id`, check that it does not conflict with an existing `id` already defined in `resources/index.template.html` — the template contains hand-authored section and element IDs that share the same HTML ID namespace.

```yaml
action-serialization:
  id: action-serialization-sample      # unique, descriptive
```

---

## 2. Metadata Field Reference

Each snippet is registered in `_snippets.yaml`. The following fields are available:

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `id` | for `aside` layout | — | HTML element ID for cross-referencing with `[[[#id]]]` |
| `title` | no | — | Example title displayed in the spec |
| `layout` | no | `aside` | `aside` (wrapped in `<aside class="example">`) or `pre` (`<pre class="example json">`) |
| `validate` | no | `true` | Whether to validate against TD/TM JSON Schema |
| `hide_paths` | no | — | Dot-notation paths to hide (replaced with `// ...`) |
| `show_paths` | no | — | Dot-notation paths to show (everything else becomes `// ...`) |

`hide_paths` and `show_paths` are mutually exclusive.

### Path Notation

Paths use dot-separated keys to target nested JSON properties:

- Top-level: `securityDefinitions`, `@context`, `id`
- Nested: `properties.temperature.forms`, `properties.lampState.type`
- Wildcard: `properties.*.forms` (matches any property name)

**Collapse vs hide:**

- `properties.*.forms` — entire `"forms"` key hidden (removed from output)
- `properties.*.forms.*` — `"forms": [// ...]` (key visible, contents collapsed)

### Schema Validation

The snippet schema is defined in `resources/schemas/snippet_schema.yaml`. Validate with:

```bash
uv run pytest tests/test_snippet_schema.py -v
```

---

## 3. Worked Example: Simple Snippet

A minimal snippet with default settings.

**Step 1 — Create the JSON file** (`resources/snippets/simple-td.json`):

```json
{
    "@context": "https://www.w3.org/ns/wot-next/td",
    "id": "urn:uuid:0804d572-cce8-422a-bb7c-4412fcd56f06",
    "title": "MyLampThing",
    "securityDefinitions": {
        "basic_sc": { "scheme": "basic", "in": "header" }
    },
    "security": "basic_sc",
    "properties": {
        "status": {
            "type": "string",
            "forms": [{ "href": "https://mylamp.example.com/status" }]
        }
    }
}
```

**Step 2 — Register in `_snippets.yaml`**:

```yaml
snippets:
  simple-td:
    id: td-simple
    title: Simple Thing Description
```

With no `hide_paths`, `show_paths`, or `layout` override, the snippet renders in full inside an `<aside class="example">` block with the given title.

**Step 3 — Add the template directive** in `resources/index.template.html`:

```
%snippet('simple-td')%
```

**Rendered output:** a titled example block containing the full syntax-highlighted JSON.

---

## 4. Worked Example: `hide_paths`

Use `hide_paths` to collapse boilerplate (context, security, form details) so the reader focuses on the relevant structure.

**Metadata:**

```yaml
snippets:
  action-serialization:
    id: action-serialization-sample
    title: Sample of an Action serialization
    hide_paths:
    - '@context'
    - id
    - title
    - securityDefinitions
    - security
    - actions.*.forms.*
```

**Effect on rendered output:** hidden paths are replaced with `// ...` in the displayed JSON. The full `action-serialization.json` file has 47 lines, but the rendered output shows only the `actions.fade` structure with `input`, `output`, and collapsed `forms`:

```json
{
    // ...
    "actions": {
        "fade": {
            "title": "Fade in/out",
            "description": "Smooth fade in and out animation.",
            "input": {
                "type": "object",
                "properties": {
                    "from": { "type": "integer", "minimum": 0, "maximum": 100 },
                    "to": { "type": "integer", "minimum": 0, "maximum": 100 },
                    "duration": { "type": "number" }
                },
                "required": ["to", "duration"]
            },
            "output": { "type": "string" },
            "forms": [
                // ...
            ]
        }
    }
}
```

**Path notation:**
- `@context` — top-level key (quote `@` keys)
- `actions.*.forms.*` — wildcard matches any key at that level. Hides all `forms` entries inside all actions.
- `properties.*.forms.*` — same pattern for property forms

---

## 5. Worked Example: `show_paths`

The inverse of `hide_paths`. Everything **not** listed becomes `// ...`. Use when the relevant portion is small relative to the full snippet.

**Metadata:**

```yaml
snippets:
  dataschema-serialization:
    id: dataschema-serialization-sample
    title: Sample of a DataSchema serialization
    show_paths:
    - properties.lampState.type
    - properties.lampState.properties
```

**Effect:** only `properties.lampState.type` and `properties.lampState.properties` are shown in full. Everything else (context, security, forms, other properties) is replaced with `// ...`.

**Rule: `hide_paths` and `show_paths` are mutually exclusive.** Setting both causes undefined behavior.

---

## 6. Worked Example: Snippet Group (Toggle)

Groups combine two related snippets into a single rendered block with a toggle. The `with-default` layout shows a compact version by default with a toggle to reveal the expanded version.

**Metadata:**

```yaml
groups:
  coap-binding:
    layout: with-default
    title: MyLampThing with CoAP Protocol Binding
    toggle_label: with Default Values
    compact: coap-binding-compact
    expanded: coap-binding-expanded
```

Both `coap-binding-compact` and `coap-binding-expanded` must exist as entries in the `snippets:` section (they can have `validate: false` if they are partial examples).

**Template directive** — same syntax as individual snippets:

```
%snippet('coap-binding')%
```

The renderer auto-detects that `coap-binding` is a group name and renders the toggle layout.

### Snippet Group (Tabbed)

For side-by-side comparison of related documents (e.g., Thing Model vs Thing Description):

```yaml
groups:
  linking-td-to-tm:
    title: Linking Thing Description to a Thing Model Definition
    tabs:
    - snippet: smart-pump-tm
      label: Thing Model
      tab_class: thingmodel
      selected: true
    - snippet: smart-pump-td
      label: Thing Description
      tab_class: thingdescription
```

Renders as a tabbed interface with one tab per snippet. `selected: true` marks the default active tab.

---

## 7. Non-Validating Snippets

**Rule: set `validate: false` only for partial, non-TD/TM, or placeholder-containing snippets.**

Rationale: by default, all snippets are validated against the generated TD/TM JSON Schema. Partial examples (e.g., protocol binding fragments, context expansion examples) fail validation because they are not complete TDs.

```yaml
snippets:
  coap-binding-compact:
    validate: false
  coap-binding-expanded:
    validate: false
```

---

## 8. Common Patterns

**Hiding security boilerplate:** most snippets hide `@context`, `id`, `title`, `securityDefinitions`, and `security` to focus on the relevant affordance structure. Copy this standard set:

```yaml
hide_paths:
- '@context'
- id
- title
- securityDefinitions
- security
```

**Layout `pre` vs `aside` (default):** use `layout: pre` for full TD/TM examples that should render as a standalone `<pre>` block rather than inside an `<aside class="example">` wrapper. Typically used for complete Thing Model or Thing Description examples referenced by `[[[#id]]]`.

---

## 9. Pitfalls

- **Forgetting to register in `_snippets.yaml`** — the JSON file exists but produces no output. No error is raised.
- **Mismatched snippet name** — the key in `_snippets.yaml` must match the filename without `.json`. `simple-td.json` → key is `simple-td`.
- **Non-existent `hide_paths` entry** — a path that does not match anything in the JSON is silently ignored. Verify after generation.
- **Stale group references** — if a group references a snippet key that does not exist, generation fails with a KeyError.

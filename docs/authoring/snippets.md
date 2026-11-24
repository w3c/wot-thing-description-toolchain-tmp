# Snippet Authoring Guide

Worked examples for authoring TD/TM JSON snippets rendered in the generated specification.
Where snippets fit in a schema change is shown in the [authoring guide](../getting-started/first-change.md).

For the schema of `_snippets.yaml`, see `resources/schemas/snippet_schema.yaml`.

---

## 1. Naming Conventions

**Rule: snippet file names use kebab-case matching the logical topic.**

```
action-serialization.json     # good: topic is clear
simple-td.json                # good
myThing_example.json          # wrong: not kebab-case
```

**Rule: `id` in `_snippets.yaml` must be globally unique and use the pattern `{topic}-{qualifier}`.**

Rationale: the `id` becomes the HTML element ID used for cross-referencing with `[[[#id]]]` in the spec. Neither generation nor the tests detect a collision; the generated page then contains two elements with the same ID. Before assigning an `id`, check that it does not conflict with an existing `id` already defined in `resources/index.template.html`. The template contains hand-authored section and element IDs that share the same HTML ID namespace.

```yaml
action-serialization:
  id: action-serialization-sample      # unique, descriptive
```

---

## 2. Metadata Field Reference

Each snippet is registered in `_snippets.yaml`. The following fields are available:

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `id` | for `aside` layout | none | HTML element ID for cross-referencing with `[[[#id]]]` |
| `title` | no | none | Example title displayed in the spec |
| `layout` | no | `aside` | `aside` (wrapped in `<aside class="example">`) or `pre` (`<pre class="example json">`) |
| `validate` | no | `true` | Whether to validate against TD/TM JSON Schema |
| `schema` | no | top-level `default_schema` | Snippet kind to validate against: a key of `generators.spec.snippet_validation_schemas` in `wot-toolchain.yaml` (`tm` for Thing Model snippets) |
| `default_schema` | when a validated snippet has no `schema` | none | **Top-level key** of `_snippets.yaml`, not a snippet field: the snippet kind for every snippet without its own `schema` (`td`) |
| `hide_paths` | no | none | Dot-notation paths to hide (replaced with `// ...`) |
| `show_paths` | no | none | Dot-notation paths to show (everything else becomes `// ...`) |

### Path Notation

Paths use dot-separated keys to target nested JSON properties:

- Top-level: `securityDefinitions`, `id`, `'@context'` (quote keys that start with `@`)
- Nested: `properties.temperature.forms`, `properties.lampState.type`
- Wildcard: `properties.*.forms` (matches any property name)

**Collapse vs hide:**

- `properties.*.forms`: entire `"forms"` key replaced by a `// ...` line
- `properties.*.forms.*`: `"forms": [// ...]` (key visible, contents collapsed)

### Schema Validation

Validate `_snippets.yaml` against its schema with:

```bash
uv run pytest tests/test_snippet_schema.py -v
```

---

## 3. Worked Example: Simple Snippet

A minimal snippet with default settings.

**Step 1: Create the JSON file** (`resources/snippets/simple-td.json`):

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

**Step 2: Register in `_snippets.yaml`**:

```yaml
snippets:
  simple-td:
    id: td-simple
    title: Simple Thing Description
```

With no `hide_paths`, `show_paths`, or `layout` override, the snippet renders in full inside an `<aside class="example">` block with the given title.

**Step 3: Add the template directive** in `resources/index.template.html`:

```
%snippet('simple-td')%
```

**Rendered output:** a titled example block containing the full JSON.

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
                    "from": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "to": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "duration": { "type": "number" }
                },
                "required": [
                    "to",
                    "duration"
                ]
            },
            "output": { "type": "string" },
            "forms": [// ...]
        }
    }
}
```

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

**Effect:** only `properties.lampState.type` and `properties.lampState.properties` are shown in full. Everything else (context, security, forms) is replaced with `// ...`.

**Rule: `hide_paths` and `show_paths` are mutually exclusive.** If both are set, generation applies `hide_paths`, ignores `show_paths`, and `tests/test_snippet_schema.py` fails.

---

## 6. Worked Example: Snippet Group (Toggle)

Groups combine two related snippets into a single rendered block with a toggle. The `with-default` layout shows the expanded version when the page loads, with a checkbox labelled `toggle_label`; clearing it shows the compact version.

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

**Template directive**: same syntax as individual snippets:

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

Rationale: by default, every snippet registered in `_snippets.yaml` is validated during `uv run wot-toolchain generate-wot-resources` against the JSON Schema that `generators.spec.snippet_validation_schemas` in `wot-toolchain.yaml` lists for its kind (`td` or `tm`, chosen by `schema` or `default_schema`). These are the static files under `resources/upstream/schemas/`, not the JSON Schema generated from the LinkML model. A violation fails generation. Partial examples (e.g., protocol binding fragments, context expansion examples) fail validation because they are not complete TDs. With `validate: false` the snippet is not validated at all and is still rendered.

```yaml
snippets:
  context-expansion-compact:
    validate: false
  context-expansion-expanded:
    validate: false
```

---

## 8. Common Patterns

**Layout `pre` vs `aside` (default):** use `layout: pre` for full TD/TM examples that should render as a standalone `<pre>` block rather than inside an `<aside class="example">` wrapper.

---

## 9. Pitfalls

- **Forgetting to register in `_snippets.yaml`**: a `%snippet('name')%` placeholder for an unregistered snippet fails generation with `ERROR: Snippet 'name' not found in _snippets.yaml`. A JSON file that is neither registered nor referenced is silently ignored and never validated.
- **Mismatched snippet name**: the key in `_snippets.yaml` must match the filename without `.json`. `simple-td.json` → key is `simple-td`.
- **Non-existent `hide_paths` entry**: a path that does not match anything in the JSON is silently ignored. Verify after generation.
- **Stale group references**: if a group references a snippet key that does not exist, generation fails with `ERROR: Snippet 'name' not found in _snippets.yaml`, or with a `FileNotFoundError` traceback for `name.json` if that file does not exist either.

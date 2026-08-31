# TD Spec Snippets

JSON example snippets rendered inline in the W3C WoT Thing Description specification.

## Adding a New Snippet

1. Create a `.json` file in this directory (pure JSON, no comments).

2. Register it in `_snippets.yaml` under the `snippets:` section:

   ```yaml
   snippets:
     my-new-snippet:
       id: my-snippet-id          # HTML element ID for [[[#my-snippet-id]]] cross-refs
       title: My Example Title    # displayed above the example block
   ```

3. Add the render directive in `resources/index.template.html`:

   ```
   %snippet('my-new-snippet')%
   ```

4. Run tests to verify cross-references resolve:

   ```bash
   uv run pytest tests/test_snippet_schema.py tests/test_snippet_crossrefs.py -v
   ```

## Snippet Metadata Fields

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `id` | for `aside` layout | - | HTML element ID for cross-referencing with `[[[#id]]]` |
| `title` | no | - | Example title displayed in the spec |
| `layout` | no | `aside` | `aside` (wrapped in `<aside class="example">`) or `pre` (`<pre class="example json">`) |
| `validate` | no | `true` | Whether to validate against TD/TM JSON Schema |
| `hide_paths` | no | - | Dot-notation paths to hide (replaced with `// ...`) |
| `show_paths` | no | - | Dot-notation paths to show (everything else becomes `// ...`) |

`hide_paths` and `show_paths` are mutually exclusive.

## Path Notation

Paths use dot-separated keys to target nested JSON properties:

- Top-level: `securityDefinitions`, `@context`, `id`
- Nested: `properties.temperature.forms`, `properties.lampState.type`
- Wildcard: `properties.*.forms` (matches any property name)

### Wildcards

Use `*` to match any key at a given depth:

```yaml
# Hide the forms array inside every property
my-snippet:
  hide_paths:
    - properties.*.forms
```

```yaml
# Show only the forms array of every property (everything else becomes // ...)
my-snippet:
  show_paths:
    - properties.*.forms
```

### Collapse vs hide

- `properties.*.forms` → entire `"forms"` key hidden (removed from output)
- `properties.*.forms.*` → `"forms": [// ...]` (key visible, contents collapsed)

## Snippet Groups/Composition

Groups or compositions combine multiple snippets into tabbed or toggle views.

### Tabbed Layout

```yaml
groups:
  my-group:
    title: Example With Multiple Views
    tabs:
      - snippet: my-snippet-compact
        label: Without Defaults
        selected: true
      - snippet: my-snippet-expanded
        label: With Defaults
```

### Toggle Layout (`with-default`)

```yaml
groups:
  my-toggle-group:
    layout: with-default
    id: example-my-toggle
    title: Example With Default Values
    toggle_label: with Default Values
    compact: my-snippet-compact
    expanded: my-snippet-expanded
```

Render a group with `%snippet('my-group')%` — same directive, auto-detected from manifest.

## Schema

The snippet LinkML schema is defined in `resources/schemas/snippet_schema.yaml`.
Validate with:

```bash
uv run pytest tests/test_snippet_schema.py -v
```

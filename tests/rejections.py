"""Where and why the generated schema rejected a sample, taken directly
from the jsonschema validation errors."""
import re
from pathlib import Path

from jsonschema.exceptions import best_match

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "resources" / "schemas"

MAX_MESSAGE = 120

# JSON Schema keywords that can appear in a schema path but are not
# definition names in the LinkML source
_KEYWORDS = {
    "$defs", "properties", "items", "anyOf", "allOf", "oneOf", "not",
    "additionalProperties", "patternProperties", "type", "pattern",
    "required", "enum", "const", "format", "contains", "...",
}

_index = None


def _definition_index():
    """{name: ["file.yaml:line", ...]} for every class/slot defined at
    2-space indentation in the LinkML source files."""
    global _index
    if _index is None:
        _index = {}
        entry = re.compile(r"^  ([A-Za-z_@][\w@-]*):\s*(?:#.*)?$")
        for yaml_path in sorted(SCHEMAS_DIR.glob("*.yaml")):
            for lineno, line in enumerate(yaml_path.read_text(encoding="utf-8").splitlines(), 1):
                m = entry.match(line)
                if m:
                    _index.setdefault(m.group(1), []).append(f"{yaml_path.name}:{lineno}")
    return _index


def defined_at(schema_path):
    """LinkML source location of the rightmost definition name in the path."""
    index = _definition_index()
    for part in reversed(schema_path.split("/")):
        if part in _KEYWORDS or part.isdigit():
            continue
        if part in index:
            return ", ".join(index[part][:2])
    return ""


def _short(text):
    text = " ".join(str(text).split())
    return text if len(text) <= MAX_MESSAGE else text[:MAX_MESSAGE] + "..."


def _schema_path(error):
    parts = [str(p) for p in error.absolute_schema_path]
    if len(parts) > 6:
        parts = ["..."] + parts[-6:]
    return "/".join(parts)


def main_rejection(errors):
    """(instance path, schema location, message) of the most relevant error."""
    leaf = best_match(errors)
    if leaf is None:
        return "", "", ""
    return leaf.json_path, _schema_path(leaf), _short(leaf.message)


def rejection_details(errors):
    """One (instance path, schema location, message) per distinct schema
    location, over all top-level errors of one sample."""
    seen = {}
    for err in errors:
        leaf = best_match([err])
        spath = _schema_path(leaf)
        if spath not in seen:
            seen[spath] = (leaf.json_path, spath, _short(leaf.message))
    return list(seen.values())

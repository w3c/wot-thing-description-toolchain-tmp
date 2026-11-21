"""Structural comparison of two JSON documents, reported as JSON paths that were added, removed or changed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from .errors import GenerationError

ChangeKind = Literal["added", "removed", "changed"]
JsonPath = tuple[str | int, ...]
JsonChange = tuple[ChangeKind, JsonPath]

CHANGE_KINDS: tuple[ChangeKind, ...] = ("added", "removed", "changed")
_SECTION_TITLES = {
    "added": "Added (only in generated)",
    "removed": "Removed (only in reference)",
    "changed": "Changed",
}
_ROOT_LABEL = "(document root)"


def json_changes(old: Any, new: Any) -> list[JsonChange]:
    """Lists the paths at which ``new`` differs from ``old``.

    Objects are compared key by key and lists of equal length item by item; any other difference,
    including lists of different length, is one change at the enclosing path.

    Args:
        old: Parsed JSON document taken as the baseline.
        new: Parsed JSON document compared against the baseline.

    Returns:
        The changes in document order, keys of each object sorted.
    """
    changes: list[JsonChange] = []
    _walk(old, new, (), changes)
    return changes


def _walk(old: Any, new: Any, path: JsonPath, changes: list[JsonChange]) -> None:
    if isinstance(old, dict) and isinstance(new, dict):
        for key in sorted(set(old) | set(new)):
            if key not in old:
                changes.append(("added", (*path, key)))
            elif key not in new:
                changes.append(("removed", (*path, key)))
            else:
                _walk(old[key], new[key], (*path, key), changes)
    elif isinstance(old, list) and isinstance(new, list) and len(old) == len(new):
        for index, (old_item, new_item) in enumerate(zip(old, new, strict=True)):
            _walk(old_item, new_item, (*path, index), changes)
    elif old != new:
        changes.append(("changed", path))


def json_pointer(path: JsonPath) -> str:
    """Renders a path as an RFC 6901 JSON Pointer.

    Args:
        path: Object keys and list indexes from the document root.

    Returns:
        The pointer; the empty string for the root.
    """
    return "".join("/" + str(part).replace("~", "~0").replace("/", "~1") for part in path)


def _pattern(path: JsonPath) -> str:
    # names become *: entries of $defs and properties, terms of the root @context, list indexes
    parts: list[str] = []
    # the shifted copy is one longer, its last element has no part to pair with
    for parent, part in zip((None, *path), path, strict=False):
        if isinstance(part, int):
            parts.append("[*]")
        elif parent in ("$defs", "properties") or (parent == "@context" and len(parts) == 1):
            parts.append(".*")
        else:
            parts.append(f".{part}")
    return "$" + "".join(parts)


def json_change_summary(golden: str, current: str) -> list[str]:
    """Summarises the changes from ``golden`` to ``current`` grouped by JSON path pattern.

    Args:
        golden: Baseline JSON text.
        current: JSON text compared against the baseline.

    Returns:
        A headline with the change and pattern counts, then one line per pattern with its count
        and one example path, most frequent pattern first.
    """
    changes = json_changes(json.loads(golden), json.loads(current))
    groups: dict[tuple[ChangeKind, str], tuple[int, JsonPath]] = {}
    for kind, path in changes:
        count, example = groups.get((kind, _pattern(path)), (0, path))
        groups[(kind, _pattern(path))] = (count + 1, example)
    lines = [f"{len(changes)} changes, {len(groups)} patterns"]
    for (kind, pattern), (count, example) in sorted(groups.items(), key=lambda item: -item[1][0]):
        lines.append(f"{count:5}  {kind:8} {pattern}   e.g. $.{'.'.join(map(str, example))}")
    return lines


def load_json(path: Path) -> Any:
    """Reads and parses a JSON file.

    Args:
        path: File to read.

    Returns:
        The parsed document.

    Raises:
        GenerationError: The file cannot be read or is not valid JSON.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise GenerationError(f"Cannot read JSON file {path}: {error}") from error
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise GenerationError(f"Invalid JSON in {path}: {error}") from error


def markdown_report(generated: Path, reference: Path) -> str:
    """Reports in Markdown which JSON paths of ``generated`` differ from ``reference``.

    Args:
        generated: JSON file produced by this toolchain.
        reference: JSON file it is compared against, for example from another toolchain.

    Returns:
        The report: both file names, the number of added, removed and changed paths, and the
        sorted JSON Pointers of each kind.

    Raises:
        GenerationError: Either file cannot be read or is not valid JSON.
    """
    changes = json_changes(load_json(reference), load_json(generated))
    lines = [
        f"## JSON diff: `{generated.name}` vs `{reference.name}`",
        "",
        f"- Generated: `{generated}`",
        f"- Reference: `{reference}`",
        "",
    ]
    if not changes:
        lines.append("No differences.")
        return "\n".join(lines)
    pointers = {kind: sorted(_label(path) for k, path in changes if k == kind) for kind in CHANGE_KINDS}
    lines += ["| Change | Paths |", "| --- | ---: |"]
    lines += [f"| {kind} | {len(pointers[kind])} |" for kind in CHANGE_KINDS]
    for kind in CHANGE_KINDS:
        if pointers[kind]:
            lines += ["", f"### {_SECTION_TITLES[kind]}", "", "```", *pointers[kind], "```"]
    return "\n".join(lines)


def _label(path: JsonPath) -> str:
    return json_pointer(path) or _ROOT_LABEL

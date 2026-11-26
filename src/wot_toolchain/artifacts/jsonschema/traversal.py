"""Applies a function to every object of a JSON Schema tree."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def _walk_schema(obj: Any, fn: Callable[[dict], dict | None]) -> Any:
    if isinstance(obj, dict):
        result = fn(obj)
        if result is not None:
            obj = result
        for key in list(obj.keys()):
            obj[key] = _walk_schema(obj[key], fn)
    elif isinstance(obj, list):
        return [_walk_schema(item, fn) for item in obj]
    return obj

"""Typed options for JSON-LD context generation."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JsonLdContextOptions:
    """The semantic choices of JSON-LD context generation; defaults reproduce the published context."""

    # Published context gives multivalued slots @container @set, inlined dictionaries @container @index
    # (jsonldcontextgen.py:423); False emits no container.
    multivalue_containers: bool = True

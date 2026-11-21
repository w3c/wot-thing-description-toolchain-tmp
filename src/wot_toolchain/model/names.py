"""Name and URI helpers shared by the artifact generators."""

from linkml_runtime.linkml_model.meta import EnumDefinition


def local_name(iri: str) -> str:
    """Return the part of ``iri`` after its last ``#`` and then its last ``/``."""
    return iri.split("#")[-1].split("/")[-1]


def is_non_ontological_enum(enum: EnumDefinition) -> bool:
    """Return whether ``enum`` has no ``enum_uri`` or a ``linkml:`` one, so it has no ontology counterpart."""
    return not enum.enum_uri or str(enum.enum_uri).startswith("linkml:")

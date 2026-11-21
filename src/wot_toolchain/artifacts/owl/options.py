"""Typed options for OWL ontology generation."""

from dataclasses import dataclass
from enum import StrEnum


class MetadataProfile(StrEnum):
    """Vocabulary used for element metadata; values equal upstream ``owlgen.MetadataProfile`` values."""

    LINKML = "linkml"
    RDFS = "rdfs"


class PermissibleValueKind(StrEnum):
    """OWL type given to enum permissible values that do not declare one themselves."""

    CLASS = "class"
    INDIVIDUAL = "individual"


@dataclass(frozen=True, slots=True)
class OwlOptions:
    """The semantic choices of OWL generation; defaults reproduce what the pipeline passed upstream so far."""

    # Descriptions are emitted as skos:definition; RDFS emits rdfs:comment instead (owlgen.py:388).
    metadata_profile: MetadataProfile = MetadataProfile.LINKML
    # Module scoping is done by the preprocessor today; True stops merging imports and emits owl:imports instead.
    only_root_schema: bool = False
    # Upstream default owl:Class; the post passes convert enum values to individuals afterwards.
    permissible_values: PermissibleValueKind = PermissibleValueKind.CLASS

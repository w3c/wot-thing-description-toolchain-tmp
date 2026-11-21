"""Typed options for SHACL shape generation."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ShaclOptions:
    """The semantic choices of SHACL generation; defaults reproduce the published shapes."""

    # Published shapes cover imported classes too; True restricts shapes to classes of the root schema.
    only_root_schema_classes: bool = False
    # Published shapes are closed so undeclared properties fail validation; True emits open shapes.
    open: bool = False

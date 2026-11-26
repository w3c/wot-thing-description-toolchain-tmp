"""Typed options for JSON Schema generation."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JsonSchemaOptions:
    """The semantic choices of JSON Schema generation; the project supplies ``top_class``."""

    # Class whose instance a validated document is; None leaves the choice to the upstream generator.
    top_class: str | None = None
    # Published schema lets objects carry undeclared properties; False emits additionalProperties false.
    open: bool = True
    # Published schema rejects null for optional properties; True also accepts null there.
    include_null: bool = False

"""A slot with a positive minimum cardinality is assigned ``mandatory`` in the spec tables."""

from linkml_runtime.linkml_model.meta import ClassDefinition, SlotDefinition

from wot_toolchain.specgen.tables import get_assignment


def test_positive_minimum_cardinality_is_mandatory() -> None:
    slot = SlotDefinition(name="oneOf", multivalued=True, minimum_cardinality=2)

    assert get_assignment("oneOf", ClassDefinition(name="Combo"), slot) == "mandatory"


def test_slot_usage_minimum_cardinality_is_mandatory() -> None:
    usage = SlotDefinition(name="oneOf", minimum_cardinality=2)
    combo = ClassDefinition(name="Combo", slot_usage={"oneOf": usage})

    assert get_assignment("oneOf", combo, SlotDefinition(name="oneOf", multivalued=True)) == "mandatory"


def test_zero_minimum_cardinality_is_optional() -> None:
    slot = SlotDefinition(name="oneOf", multivalued=True, minimum_cardinality=0)

    assert get_assignment("oneOf", ClassDefinition(name="Combo"), slot) == "optional"

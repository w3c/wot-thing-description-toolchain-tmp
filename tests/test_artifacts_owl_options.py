import dataclasses
import warnings
from pathlib import Path

import pytest
from linkml.generators import owlgen
from linkml.generators.owlgen import OwlSchemaGenerator
from rdflib import OWL, RDF, RDFS, SKOS, XSD, Graph, URIRef
from rdflib.compare import graph_diff, to_isomorphic

from wot_toolchain.artifacts.owl.generator import WotOwlGenerator
from wot_toolchain.artifacts.owl.options import MetadataProfile, OwlOptions, PermissibleValueKind
from wot_toolchain.config import load_project
from wot_toolchain.preprocessors.owl_preprocessor import preprocess_for_gen_owl

MANIFEST = Path(__file__).resolve().parent.parent / "wot-toolchain.yaml"

TODAYS_FLAGS = {
    "metaclasses": False,
    "type_objects": False,
    "use_native_uris": False,
    "skip_vacuous_local_range_axioms": True,
    "skip_vacuous_min_zero_cardinality_axioms": True,
    "consolidate_cardinality_axioms": False,
    "skip_abstract_class_as_unionof_subclasses": True,
}


@pytest.fixture(scope="module")
def hctl_yaml() -> str:
    return _preprocessed_yaml("hctl")


def _preprocessed_yaml(prefix: str) -> str:
    schema = next(module.schema for module in load_project(MANIFEST).modules if module.prefix == prefix)
    return preprocess_for_gen_owl(str(schema))


def _graph(generator: OwlSchemaGenerator) -> Graph:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        graph: Graph = generator.as_graph()
        return graph


def test_options_defaults() -> None:
    assert OwlOptions() == OwlOptions(
        metadata_profile=MetadataProfile.LINKML,
        only_root_schema=False,
        permissible_values=PermissibleValueKind.CLASS,
    )


def test_options_are_frozen_with_exactly_three_fields() -> None:
    options = OwlOptions()
    assert [f.name for f in dataclasses.fields(OwlOptions)] == [
        "metadata_profile",
        "only_root_schema",
        "permissible_values",
    ]
    with pytest.raises(dataclasses.FrozenInstanceError):
        options.only_root_schema = True  # type: ignore[misc]


def test_from_options_returns_wot_generator(hctl_yaml: str) -> None:
    assert isinstance(WotOwlGenerator.from_options(hctl_yaml, OwlOptions()), WotOwlGenerator)


def test_from_options_sets_todays_fixed_flags(hctl_yaml: str) -> None:
    wot = WotOwlGenerator.from_options(hctl_yaml, OwlOptions())
    assert {name: getattr(wot, name) for name in TODAYS_FLAGS} == TODAYS_FLAGS


def test_default_options_map_to_upstream_arguments(hctl_yaml: str) -> None:
    wot = WotOwlGenerator.from_options(hctl_yaml, OwlOptions())
    assert wot.metadata_profiles == [owlgen.MetadataProfile.linkml]
    assert wot.mergeimports is True
    assert wot.default_permissible_value_type == OWL.Class


def test_non_default_options_map_to_upstream_arguments(hctl_yaml: str) -> None:
    options = OwlOptions(
        metadata_profile=MetadataProfile.RDFS,
        only_root_schema=True,
        permissible_values=PermissibleValueKind.INDIVIDUAL,
    )
    wot = WotOwlGenerator.from_options(hctl_yaml, options)
    assert wot.metadata_profiles == [owlgen.MetadataProfile.rdfs]
    assert wot.mergeimports is False
    assert wot.default_permissible_value_type == OWL.NamedIndividual


# WotOwlGenerator emits named rdfs:range values; the RDF list predicates come from bnode relabelling of the
# unchanged enum covering unions in the isomorphic diff.
_NAMED_RANGES = {RDFS.range, OWL.unionOf, RDF.first, RDF.rest}
# Upstream emits slot restrictions, cardinalities and anonymous ranges, which WotOwlGenerator suppresses.
_RESTRICTIONS = {
    RDF.type,
    RDF.first,
    RDF.rest,
    RDFS.range,
    OWL.allValuesFrom,
    OWL.complementOf,
    OWL.datatypeComplementOf,
    OWL.intersectionOf,
    OWL.maxCardinality,
    OWL.minCardinality,
    OWL.onProperty,
    OWL.unionOf,
}


@pytest.mark.parametrize(
    ("prefix", "wot_only_predicates", "upstream_only_predicates"),
    [
        (
            "td",
            {RDFS.isDefinedBy, RDFS.seeAlso, RDFS.subClassOf, RDFS.subPropertyOf, *_NAMED_RANGES},
            {SKOS.exactMatch, RDFS.seeAlso, RDFS.subClassOf, RDFS.subPropertyOf, *_RESTRICTIONS},
        ),
        (
            "hctl",
            {RDFS.isDefinedBy, *_NAMED_RANGES},
            {SKOS.exactMatch, RDFS.subClassOf, OWL.onDatatype, OWL.withRestrictions, XSD.pattern, *_RESTRICTIONS},
        ),
    ],
)
def test_default_options_graph_differs_from_todays_flags_graph_only_by_documented_overrides(
    prefix: str, wot_only_predicates: set[URIRef], upstream_only_predicates: set[URIRef]
) -> None:
    yaml_str = _preprocessed_yaml(prefix)
    wot = _graph(WotOwlGenerator.from_options(yaml_str, OwlOptions()))
    upstream = _graph(OwlSchemaGenerator(yaml_str, **TODAYS_FLAGS))
    _, wot_only, upstream_only = graph_diff(to_isomorphic(wot), to_isomorphic(upstream))
    assert len(wot) > 0
    assert {predicate for _, predicate, _ in wot_only} == wot_only_predicates
    assert len(upstream_only) > 0
    assert {predicate for _, predicate, _ in upstream_only} == upstream_only_predicates

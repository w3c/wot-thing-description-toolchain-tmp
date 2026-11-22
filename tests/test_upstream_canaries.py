"""Canaries that fail once upstream LinkML fixes a defect a toolchain workaround exists for."""

import json
import warnings
from typing import Any

import pytest
from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml.generators.owlgen import OwlSchemaGenerator
from linkml.generators.shaclgen import ShaclGenerator
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS, SH, XSD
from rdflib.term import Node

from wot_toolchain.config import GEN_OWL_OPTIONS

EX = "https://example.org/ex#"

HEADER = """
id: https://example.org/probe
name: probe
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/ex#
  owl: http://www.w3.org/2002/07/owl#
  rdf: http://www.w3.org/1999/02/22-rdf-syntax-ns#
  rdfs: http://www.w3.org/2000/01/rdf-schema#
  dcterms: http://purl.org/dc/terms/
default_prefix: ex
imports: [linkml:types]
"""

DESIGNATOR_SCHEMA = (
    HEADER
    + """
enums:
  Kind:
    permissible_values:
      A: {}
slots:
  kind:
    range: Kind
    designates_type: true
classes:
  A:
    slots: [kind]
"""
)

CONTEXT_SCHEMA = (
    HEADER
    + """
types:
  literal:
    typeof: string
    uri: rdfs:Literal
enums:
  Color:
    permissible_values:
      red:
        meaning: ex:Red
slots:
  label:
    range: literal
  color:
    range: Color
  value:
    range: Any
    implements: [owl:DatatypeProperty]
  part:
    range: Part
    inlined: true
classes:
  Any:
    class_uri: linkml:Any
  Part:
    attributes:
      n:
        range: string
  Thing:
    slots: [label, color, value, part]
"""
)

OWL_SCHEMA = (
    HEADER
    + """
enums:
  Color:
    enum_uri: ex:Color
    annotations:
      rdfs:subClassOf:
        value: http://schema.org/Enumeration
      rdfs:isDefinedBy:
        value: https://example.org/probe
    permissible_values:
      red:
        meaning: ex:Red
slots:
  label:
    slot_uri: ex:label
    range: string
    annotations:
      rdfs:subPropertyOf: dcterms:title
      rdfs:seeAlso:
        value: http://schema.org/name
classes:
  Thing:
    class_uri: ex:Thing
    slots: [label]
"""
)

SHACL_SCHEMA = (
    HEADER
    + """
types:
  literal:
    typeof: string
    uri: rdfs:Literal
  langString:
    uri: rdf:langString
    base: str
slots:
  label:
    slot_uri: ex:label
    range: literal
  title:
    slot_uri: ex:title
    range: string
classes:
  Thing:
    class_uri: ex:Thing
    slots: [label, title]
    slot_usage:
      title:
        exactly_one_of:
          - range: string
          - range: langString
"""
)


@pytest.fixture(scope="module")
def context() -> dict[str, Any]:
    # Same generator options as pipeline._context_generator.
    raw = ContextGenerator(CONTEXT_SCHEMA, mergeimports=True, fix_multivalue_containers=True).serialize()
    terms: dict[str, Any] = json.loads(raw)["@context"]
    return terms


@pytest.fixture(scope="module")
def owl() -> Graph:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        raw = OwlSchemaGenerator(OWL_SCHEMA, **GEN_OWL_OPTIONS).serialize()
    return Graph().parse(data=raw, format="turtle")


@pytest.fixture(scope="module")
def shacl() -> Graph:
    # Same generator options as pipeline._gen_shacl.
    raw = ShaclGenerator(SHACL_SCHEMA, mergeimports=False, closed=True, suffix="Shape").serialize()
    return Graph().parse(data=raw, format="turtle")


def _property_shape(graph: Graph, path: str) -> Node:
    shape = graph.value(predicate=SH.path, object=URIRef(EX + path))
    assert shape is not None
    return shape


def test_jsonschema_crashes_on_enum_ranged_type_designator() -> None:
    """Guards the designates_type toggle in pipeline._gen_jsonschema."""
    generator = JsonSchemaGenerator(
        DESIGNATOR_SCHEMA, mergeimports=True, not_closed=True, include_null=False, preserve_names=True
    )
    with pytest.raises(ValueError, match='No such type: "Kind"'):
        generator.serialize()


def test_context_coerces_literal_typed_slot_to_rdfs_literal(context: dict[str, Any]) -> None:
    """Guards jsonld_context_postprocessor._remove_literal_type_coercion."""
    assert context["label"]["@type"] == "rdfs:Literal"


def test_context_emits_skos_context_for_enum_ranged_slot(context: dict[str, Any]) -> None:
    """Guards jsonld_context_postprocessor._strip_skos_enum_contexts."""
    assert context["color"]["@context"] == {"text": "skos:notation", "description": "skos:prefLabel", "meaning": "@id"}


def test_context_coerces_datatype_property_to_id(context: dict[str, Any]) -> None:
    """Guards jsonld_context_postprocessor._strip_datatype_property_id_coercion."""
    assert context["value"]["@type"] == "@id"


def test_context_coerces_inlined_class_without_identifier_to_id(context: dict[str, Any]) -> None:
    """Guards jsonld_context_postprocessor._strip_inlined_class_id_coercion."""
    assert context["part"]["@type"] == "@id"


def test_owl_emits_subproperty_annotation_as_literal_curie(owl: Graph) -> None:
    """Guards owl_postprocessor._fix_subproperty_literals."""
    assert set(owl.objects(URIRef(EX + "label"), RDFS.subPropertyOf)) == {Literal("dcterms:title")}


@pytest.mark.parametrize(
    ("subject", "predicate", "iri"),
    [
        ("Color", RDFS.subClassOf, "http://schema.org/Enumeration"),
        ("Color", RDFS.isDefinedBy, "https://example.org/probe"),
        ("label", RDFS.seeAlso, "http://schema.org/name"),
    ],
)
def test_owl_emits_uri_annotation_as_literal(owl: Graph, subject: str, predicate: URIRef, iri: str) -> None:
    """Guards WotOwlGenerator.add_metadata."""
    objects = set(owl.objects(URIRef(EX + subject), predicate))
    assert Literal(iri) in objects
    assert URIRef(iri) not in objects


def test_shacl_emits_rdfs_literal_datatype(shacl: Graph) -> None:
    """Guards shacl_postprocessor._remove_literal_datatype."""
    assert (_property_shape(shacl, "label"), SH.datatype, RDFS.Literal) in shacl


def test_shacl_drops_langstring_branch_of_exactly_one_of(shacl: Graph) -> None:
    """Guards the langString sh:or rewrite in shacl_postprocessor.post_process_shacl."""
    shape = _property_shape(shacl, "title")
    assert set(shacl.objects(shape, SH.datatype)) == {XSD.string}
    assert (shape, SH["or"], None) not in shacl
    assert (None, None, RDF.langString) not in shacl

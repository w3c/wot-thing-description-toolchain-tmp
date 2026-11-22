"""WotOwlGenerator tags label, definition and comment text @en, before any post pass."""

import warnings
from pathlib import Path

import pytest
from rdflib import RDFS, SKOS, Graph, Literal, URIRef

from wot_toolchain.artifacts.owl.generator import WotOwlGenerator
from wot_toolchain.artifacts.owl.options import MetadataProfile, OwlOptions, PermissibleValueKind

EX = "https://example.org/s#"

SCHEMA = """\
id: https://example.org/s
name: s
default_prefix: ex
prefixes:
  ex: https://example.org/s#
  rdfs: http://www.w3.org/2000/01/rdf-schema#
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
classes:
  Thing:
    class_uri: ex:Thing
    description: A thing.
    comments:
      - Editorial remark.
    annotations:
      rdfs:seeAlso: see the spec
enums:
  Operation:
    enum_uri: ex:Operation
    permissible_values:
      read:
        meaning: ex:read
"""


@pytest.fixture(scope="module")
def schema_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("schemas") / "s.yaml"
    path.write_text(SCHEMA, encoding="utf-8")
    return path


def _graph(schema_path: Path, options: OwlOptions) -> Graph:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        result: Graph = WotOwlGenerator.from_options(str(schema_path), options).as_graph()
    return result


@pytest.fixture(scope="module")
def graph(schema_path: Path) -> Graph:
    return _graph(schema_path, OwlOptions(permissible_values=PermissibleValueKind.INSTANCE))


def test_description_is_tagged_en(graph: Graph) -> None:
    assert set(graph.objects(URIRef(EX + "Thing"), SKOS.definition)) == {Literal("A thing.", lang="en")}


def test_label_is_tagged_en(graph: Graph) -> None:
    assert set(graph.objects(URIRef(EX + "Thing"), RDFS.label)) == {Literal("Thing", lang="en")}


def test_permissible_value_label_is_tagged_en(graph: Graph) -> None:
    assert set(graph.objects(URIRef(EX + "read"), RDFS.label)) == {Literal("read", lang="en")}


def test_rdfs_profile_description_comment_is_tagged_en(schema_path: Path) -> None:
    graph = _graph(schema_path, OwlOptions(metadata_profile=MetadataProfile.RDFS))
    assert set(graph.objects(URIRef(EX + "Thing"), RDFS.comment)) == {Literal("A thing.", lang="en")}


def test_comments_note_stays_untagged(graph: Graph) -> None:
    assert set(graph.objects(URIRef(EX + "Thing"), SKOS.note)) == {Literal("Editorial remark.")}


def test_string_annotation_stays_untagged(graph: Graph) -> None:
    assert set(graph.objects(URIRef(EX + "Thing"), RDFS.seeAlso)) == {Literal("see the spec")}

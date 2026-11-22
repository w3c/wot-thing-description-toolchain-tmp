"""WotOwlGenerator with only_root_schema emits only the subjects of the root schema's own namespace."""

import warnings
from pathlib import Path

import pytest
from rdflib import Graph, URIRef

from wot_toolchain.artifacts.owl.generator import WotOwlGenerator
from wot_toolchain.artifacts.owl.options import OwlOptions, PermissibleValueKind

# Borrowed, issued and Code are root elements named by a foreign IRI; Part and size come from the import.
ROOT = """\
id: https://example.org/root
name: root
default_prefix: ex
prefixes:
  ex: https://example.org/root#
  part: https://example.org/part#
  other: https://example.org/other#
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
  - part
classes:
  Thing:
    class_uri: ex:Thing
    slots:
      - colour
      - issued
  Borrowed:
    class_uri: other:Borrowed
slots:
  colour:
    slot_uri: ex:colour
    range: Colour
  issued:
    slot_uri: other:issued
    range: Code
types:
  Code:
    uri: other:code
    base: str
enums:
  Colour:
    enum_uri: ex:Colour
    permissible_values:
      red:
        meaning: ex:red
      blue:
        meaning: other:blue
"""

PART = """\
id: https://example.org/part
name: part
default_prefix: part
prefixes:
  part: https://example.org/part#
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
classes:
  Part:
    class_uri: part:Part
    mixin: true
    slots:
      - size
slots:
  size:
    slot_uri: part:size
    range: integer
"""

ONTOLOGY = URIRef("https://example.org/root")
NAMESPACE = "https://example.org/root#"
LOCAL = {URIRef(NAMESPACE + name) for name in ("Thing", "colour", "Colour", "red")}
IMPORTED = URIRef("https://example.org/part#Part")
BORROWED = URIRef("https://example.org/other#Borrowed")


def _graph(directory: Path, *, only_root_schema: bool) -> Graph:
    (directory / "root.yaml").write_text(ROOT, encoding="utf-8")
    (directory / "part.yaml").write_text(PART, encoding="utf-8")
    options = OwlOptions(only_root_schema=only_root_schema, permissible_values=PermissibleValueKind.INSTANCE)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        result: Graph = WotOwlGenerator.from_options(str(directory / "root.yaml"), options).as_graph()
    return result


@pytest.fixture(scope="module")
def scoped(tmp_path_factory: pytest.TempPathFactory) -> Graph:
    return _graph(tmp_path_factory.mktemp("scoped"), only_root_schema=True)


@pytest.fixture(scope="module")
def merged(tmp_path_factory: pytest.TempPathFactory) -> Graph:
    return _graph(tmp_path_factory.mktemp("merged"), only_root_schema=False)


def test_only_root_schema_emits_only_own_namespace_subjects(scoped: Graph) -> None:
    assert set(scoped.subjects()) == LOCAL | {ONTOLOGY}


def test_default_options_keep_imported_and_foreign_subjects(merged: Graph) -> None:
    assert {IMPORTED, BORROWED} <= set(merged.subjects())

from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.collection import Collection
from rdflib.namespace import RDF as RDF_NAMESPACE
from rdflib.namespace import SH, XSD

from src.wotis.postprocessors.shacl_postprocessor import post_process_shacl
from linkml.generators.shaclgen import ShaclGenerator
from linkml_runtime.utils.schemaview import SchemaView


REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "resources" / "schemas" / "thing_description.yaml"
TD_TITLE = URIRef("https://www.w3.org/2019/wot/td#title")
TD_THING = URIRef("https://www.w3.org/2019/wot/td#Thing")
TD_INTERACTION_AFFORDANCE = URIRef("https://www.w3.org/2019/wot/td#InteractionAffordance")
JSONSCHEMA_DATA_SCHEMA = URIRef("https://www.w3.org/2019/wot/json-schema#DataSchema")


def _title_property_shapes(graph: Graph, class_uri: URIRef) -> list[URIRef]:
    node_shape = graph.value(predicate=SH.targetClass, object=class_uri)
    assert node_shape is not None
    return [
        property_shape
        for property_shape in graph.objects(node_shape, SH.property)
        if (property_shape, SH.path, TD_TITLE) in graph
    ]


def test_title_accepts_string_or_langstring_in_shacl() -> None:
    schema_view = SchemaView(SCHEMA_PATH, merge_imports=True)
    raw_shacl = ShaclGenerator(schema_view.schema, mergeimports=False, closed=True, suffix="Shape").serialize()
    graph = Graph().parse(data=post_process_shacl(raw_shacl, schema_view), format="turtle")

    property_shapes = _title_property_shapes(graph, TD_THING)
    assert property_shapes
    for property_shape in property_shapes:
        union = graph.value(property_shape, SH["or"])
        assert union is not None
        branches = list(Collection(graph, union))
        assert {graph.value(branch, SH.datatype) for branch in branches} == {XSD.string, RDF_NAMESPACE.langString}
        assert (property_shape, SH.datatype, None) not in graph


def test_title_remains_string_outside_thing_shape() -> None:
    schema_view = SchemaView(SCHEMA_PATH, merge_imports=True)
    raw_shacl = ShaclGenerator(schema_view.schema, mergeimports=False, closed=True, suffix="Shape").serialize()
    graph = Graph().parse(data=post_process_shacl(raw_shacl, schema_view), format="turtle")

    for class_uri in (TD_INTERACTION_AFFORDANCE, JSONSCHEMA_DATA_SCHEMA):
        property_shapes = _title_property_shapes(graph, class_uri)
        assert property_shapes
        for property_shape in property_shapes:
            assert (property_shape, SH.datatype, XSD.string) in graph
            assert (property_shape, SH["or"], None) not in graph

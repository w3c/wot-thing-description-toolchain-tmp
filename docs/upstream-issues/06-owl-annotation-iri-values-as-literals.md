# gen-owl emits IRI-valued element annotations (rdfs:subPropertyOf, rdfs:seeAlso, ...) as string literals

- **linkml version:** 1.12.0 (linkml-runtime 1.12.0); **generator:** `OwlSchemaGenerator`
- **Classification (my judgment):** bug for `rdfs:subPropertyOf` / `rdfs:subClassOf`, whose objects must
  be resources (a literal object of `rdfs:subPropertyOf` is not valid OWL 2 DL); feature gap for
  `rdfs:seeAlso` / `rdfs:isDefinedBy`, since there is no way to mark an annotation value as an IRI.
- **Backing canaries** (`tests/test_upstream_canaries.py`): `test_owl_emits_subproperty_annotation_as_literal_curie`,
  `test_owl_emits_uri_annotation_as_literal` (3 parametrizations)

## Reproducer (default options; the canaries also reproduce it with this repo's `GEN_OWL_OPTIONS`)

```python
from linkml.generators.owlgen import OwlSchemaGenerator
from rdflib import Graph, URIRef
from rdflib.namespace import RDFS
schema = """
id: https://example.org/probe
name: probe
prefixes:
  linkml: https://w3id.org/linkml/
  ex: https://example.org/ex#
  rdfs: http://www.w3.org/2000/01/rdf-schema#
  dcterms: http://purl.org/dc/terms/
default_prefix: ex
imports: [linkml:types]
enums:
  Color:
    enum_uri: ex:Color
    annotations: {rdfs:subClassOf: "http://schema.org/Enumeration", rdfs:isDefinedBy: "https://example.org/probe"}
    permissible_values: {red: {meaning: ex:Red}}
slots:
  label:
    slot_uri: ex:label
    annotations: {rdfs:subPropertyOf: dcterms:title, rdfs:seeAlso: "http://schema.org/name"}
classes:
  Thing: {class_uri: ex:Thing, slots: [label]}
"""
g = Graph().parse(data=OwlSchemaGenerator(schema).serialize(), format="turtle")
for s, p in [("label", RDFS.subPropertyOf), ("label", RDFS.seeAlso),
             ("Color", RDFS.subClassOf), ("Color", RDFS.isDefinedBy)]:
    for o in g.objects(URIRef("https://example.org/ex#" + s), p):
        print(f"ex:{s} {g.qname(p)} {o!r}")
```

Actual output (stderr deprecation notices omitted):
```
ex:label rdfs:subPropertyOf rdflib.term.Literal('dcterms:title')
ex:label rdfs:seeAlso rdflib.term.Literal('http://schema.org/name')
ex:Color rdfs:subClassOf rdflib.term.Literal('http://schema.org/Enumeration')
ex:Color rdfs:isDefinedBy rdflib.term.Literal('https://example.org/probe')
```

**Expected:** IRI objects, with the CURIE `dcterms:title` expanded. **Actual:** plain string literals.

**Suspected cause:** `linkml/generators/owlgen.py:424-442` (`add_metadata`): the annotation key is expanded to an IRI, but
every string value goes through `self._literal(v.value, e)` (line 439), which always returns a
`Literal`. The value is never checked for being a CURIE or IRI.

**Workaround in this repo:** `_fix_subproperty_literals` and `_fix_uri_annotation_literals` in
`src/wot_toolchain/postprocessors/owl_postprocessor.py`.

# OWL Enum Modeling

How LinkML enums appear in the generated OWL ontologies (`resources/gens/owl/*.ttl`). Cross-references: [OWL/RDF Modeling](../maintainers/owl-rdf-modeling.md) §7, [OWL differences](../differences/owl.md).

## 1. Published Shape

| Element | Emitted triples |
|---------|-----------------|
| Enum | `a owl:Class`, `rdfs:label`, `skos:definition`, `rdfs:isDefinedBy <ontology>`, `skos:inScheme <ontology>` |
| Enum with `rdfs:subClassOf` annotation | additionally `rdfs:subClassOf <IRI>`, e.g. `schema:Enumeration` |
| Permissible value with `meaning` | IRI = `meaning`; `a <Enum>`, `rdfs:label` (the value text), `skos:definition`, `rdfs:isDefinedBy <ontology>` (own namespace only) |
| Permissible value without `meaning` | nothing |

`rdfs:subClassOf schema:Enumeration` is not added by code. It comes from the schema annotation on `OperationType` (`resources/schemas/hypermedia.yaml`), which `WotOwlGenerator.add_metadata` emits as an IRI. Only `td:OperationType` carries it today.

Emitted by `WotOwlGenerator.add_enum` and `_add_enum_instance` in `src/wot_toolchain/artifacts/owl/generator.py`.

## 2. Deliberately Not Emitted

- `owl:NamedIndividual` declaration on values
- `owl:oneOf` covering axiom on the enum class
- `skos:Concept` typing
- `linkml:permissible_values`

## 3. Decision

**Rule: an enum is an open class whose values are typed instances, following the schema.org enumeration pattern, not the closed `owl:oneOf` enumeration of OWL textbooks.**

Consequence: the OWL enum class has no closure axiom, so the ontology does not state that the listed values are the only members. The closed value set is enforced by the validation artifacts instead:

- SHACL: `sh:in ( td:readProperty ... )` on `hctl:hasOperationType` (`resources/gens/shacl/shapes.shacl.ttl`)
- JSON Schema: `"enum": [ "readproperty", ... ]` in the array branch of `op` (`resources/gens/jsonschema/jsonschema.json`)

## 4. Option

Selected by `OwlOptions(permissible_values=PermissibleValueKind.INSTANCE)` (`src/wot_toolchain/artifacts/owl/options.py`), set by the pipeline in `src/wot_toolchain/pipeline.py`. The other kinds (`CLASS`, `INDIVIDUAL`) fall through to upstream `add_enum`.

## 5. Example (`resources/gens/owl/td.ttl`, abridged)

```turtle
td:OperationType
    rdf:type owl:Class ;
    rdfs:label "OperationType"@en ;
    rdfs:subClassOf schema:Enumeration ;
    rdfs:isDefinedBy <https://www.w3.org/2019/wot/td> ;
    skos:inScheme <https://www.w3.org/2019/wot/td> ;
.

td:readProperty
    rdf:type td:OperationType ;
    rdfs:label "readProperty"@en ;
    skos:definition "Identifies the read operation on Property Affordances to retrieve the corresponding data."@en ;
    rdfs:isDefinedBy <https://www.w3.org/2019/wot/td> ;
.
```

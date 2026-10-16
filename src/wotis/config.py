"""Generator configuration — schema-to-artifact module mapping and gen-owl options."""

# Each tuple: (input schema filename, output TTL filename).
# Order within each group is preserved in the pipeline.
OWL_MODULES = (
    ("thing_description.yaml", "td.ttl"),
    ("hypermedia.yaml", "hctl.ttl"),
    ("wot_security.yaml", "wotsec.ttl"),
    ("jsonschema.yaml", "jsonschema.ttl"),
    ("thing_model.yaml", "tm.ttl"),
)

GEN_OWL_OPTIONS = {
    "metaclasses": False,
    "type_objects": False,
    "use_native_uris": False,
    "skip_vacuous_local_range_axioms": True,
    "skip_vacuous_min_zero_cardinality_axioms": True,
    "consolidate_cardinality_axioms": False,
    "skip_abstract_class_as_unionof_subclasses": True,
}

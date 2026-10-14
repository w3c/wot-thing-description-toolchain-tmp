"""Generate readable, module-scoped OWL vocabulary files from LinkML schemas."""
from __future__ import annotations

import os
import tempfile
import warnings
from pathlib import Path

from linkml.generators.owlgen import OwlSchemaGenerator

from ..postprocessors.owl_postprocessor import postprocess_owl
from ..preprocessors.owl_preprocessor import preprocess_for_gen_owl


SCHEMA_DIR = Path("resources/schemas")

_TD_MODULES = (
    ("thing_description.yaml", "td.ttl"),
    ("hypermedia.yaml", "hctl.ttl"),
    ("wot_security.yaml", "wotsec.ttl"),
    ("jsonschema.yaml", "jsonschema.ttl"),
)
_TM_MODULES = (
    ("thing_model.yaml", "tm.ttl"),
)


def generate_owl_vocabularies(output_dir: Path, schema_dir: Path = SCHEMA_DIR) -> None:
    """Write one OWL vocabulary file for every WoT LinkML schema module."""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "ontology.owl.ttl").unlink(missing_ok=True)

    for schema_file, output_file in list(_TD_MODULES) + list(_TM_MODULES):
        ttl = _run_gen_owl(schema_dir / schema_file)
        postprocess_owl(ttl, schema_file, output_file, schema_dir, output_dir)


def _run_gen_owl(schema_path: Path) -> str:
    """Preprocess schema and run gen-owl; return TTL string."""
    yaml_str = preprocess_for_gen_owl(str(schema_path))
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_str)
        tmp = f.name
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            gen = OwlSchemaGenerator(
                tmp,
                metaclasses=False,
                type_objects=False,
                use_native_uris=False,
                default_language="en",
                skip_vacuous_local_range_axioms=True,
                skip_vacuous_min_zero_cardinality_axioms=True,
                consolidate_cardinality_axioms=False,
                skip_abstract_class_as_unionof_subclasses=True,
            )
            return gen.serialize()
    finally:
        os.unlink(tmp)

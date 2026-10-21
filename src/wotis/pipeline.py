"""WoT artifact generation pipeline."""
from __future__ import annotations

import json
import logging
import os
import tempfile
import warnings
from collections.abc import Callable
from pathlib import Path

from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml.generators.linkmlgen import LinkmlGenerator
from linkml.generators.owlgen import OwlSchemaGenerator
from linkml.generators.shaclgen import ShaclGenerator
from linkml_runtime.utils.schemaview import SchemaView

from . import SCHEMA_PATH, GENS_PATH, GENERATORS, EXTRA_ASSERTS_PATH
from .config import JSONLD_CONTEXT_MODULES, OWL_MODULES, GEN_OWL_OPTIONS
from .generators.visualization import generate_visualizations
from .generators.respec import generate_respec_spec
from .postprocessors.jsonschema_postprocessor import post_process_jsonschema
from .postprocessors.jsonld_context_postprocessor import (
    build_module_context,
    post_process_jsonld_context,
)
from .postprocessors.owl_postprocessor import postprocess_owl
from .postprocessors.shacl_postprocessor import post_process_shacl
from .preprocessors.owl_preprocessor import preprocess_for_gen_owl

log = logging.getLogger(__name__)

_ARTIFACT_GENERATORS = [g for g in GENERATORS if g != "visualization"]


def run_pipeline(
    input_path: Path,
    *,
    generate_docs: bool = False,
    assertions_csv_path: Path | None = None,
    extra_asserts_path: Path | None = None,
) -> None:
    schema_view = SchemaView(input_path, merge_imports=True)

    for name in _ARTIFACT_GENERATORS:
        output_dir = GENS_PATH / name
        output_dir.mkdir(parents=True, exist_ok=True)
        _DISPATCH[name](schema_view, output_dir)

    generate_visualizations(SCHEMA_PATH, GENS_PATH / "visualization")

    if generate_docs:
        from . import (
            RESPEC_TEMPLATE_PATH, FINAL_SPEC_PATH,
            CORE_SCHEMA_PLACEHOLDER, ASSERTION_PATH,
        )
        generate_respec_spec(
            input_path,
            RESPEC_TEMPLATE_PATH,
            FINAL_SPEC_PATH,
            CORE_SCHEMA_PLACEHOLDER,
            assertions_csv_path=assertions_csv_path or ASSERTION_PATH,
            extra_asserts_path=extra_asserts_path or EXTRA_ASSERTS_PATH,
        )


def _gen_jsonschema(sv: SchemaView, output_dir: Path) -> None:
    gen = JsonSchemaGenerator(
        sv.schema,
        mergeimports=True,
        top_class="Thing",
        not_closed=True,
        include_null=False,
        preserve_names=True,
    )
    raw = json.loads(gen.serialize())
    processed = post_process_jsonschema(raw, sv)
    with (output_dir / "jsonschema.json").open("w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2, ensure_ascii=False)


def _gen_shacl(sv: SchemaView, output_dir: Path) -> None:
    gen = ShaclGenerator(sv.schema, mergeimports=False, closed=True, suffix="Shape")
    processed = post_process_shacl(gen.serialize(), sv)
    (output_dir / "shapes.shacl.ttl").write_text(processed, encoding="utf-8")


def _gen_owl(sv: SchemaView, output_dir: Path) -> None:
    (output_dir / "ontology.owl.ttl").unlink(missing_ok=True)
    for schema_file, output_file in OWL_MODULES:
        ttl = _run_gen_owl(SCHEMA_PATH / schema_file)
        postprocess_owl(ttl, schema_file, output_file, SCHEMA_PATH, output_dir)


def _gen_jsonldcontext(sv: SchemaView, output_dir: Path) -> None:
    gen = ContextGenerator(sv.schema, mergeimports=True, fix_multivalue_containers=True)
    for prefix, filename in JSONLD_CONTEXT_MODULES:
        module_ctx = build_module_context(sv, gen, prefix)
        doc = json.dumps({"@context": module_ctx}, indent=2)
        (output_dir / filename).write_text(doc)
    merged = post_process_jsonld_context(sv, gen.serialize())
    (output_dir / "context.jsonld").write_text(merged)


def _gen_linkml(sv: SchemaView, output_dir: Path) -> None:
    gen = LinkmlGenerator(sv.schema, mergeimports=True, format="yaml")
    (output_dir / "linkml.yaml").write_text(gen.serialize())


def _run_gen_owl(schema_path: Path) -> str:
    yaml_str = preprocess_for_gen_owl(str(schema_path))
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_str)
        tmp = f.name
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            gen = OwlSchemaGenerator(tmp, **GEN_OWL_OPTIONS)
            return gen.serialize()
    finally:
        os.unlink(tmp)


_DISPATCH: dict[str, Callable[[SchemaView, Path], None]] = {
    "jsonschema": _gen_jsonschema,
    "shacl": _gen_shacl,
    "owl": _gen_owl,
    "jsonldcontext": _gen_jsonldcontext,
    "linkml": _gen_linkml,
}

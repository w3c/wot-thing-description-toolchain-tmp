import json
import logging
import shutil

from copy import deepcopy

from pathlib import Path

from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml.generators.shaclgen import ShaclGenerator
from linkml.generators.owlgen import OwlSchemaGenerator
from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml.generators.linkmlgen import LinkmlGenerator
from linkml_runtime.linkml_model import SchemaDefinition
from linkml_runtime.utils.schemaview import SchemaView

from .config import Config
from .errors import GenerationError, SchemaError
from .artifacts.jsonschema.generator import WotJsonSchemaGenerator
from .artifacts.jsonschema.options import JsonSchemaOptions
from .artifacts.jsonschema.postprocess import post_process_jsonschema
from .artifacts.shacl.postprocess import post_process_shacl
from .generators.visualization import generate_visualizations
from .generators.respec import generate_respec_spec

# Hand-drawn spec figures copied from w3c/wot-thing-description visualization/.
STATIC_VISUALIZATION_PATH = Path('resources') / 'static' / 'visualization'


def _for_rdf(schema: SchemaDefinition) -> SchemaDefinition:
    """Return a copy of ``schema`` without "not empty" on optional slots, which RDF would read as mandatory."""
    rdf_schema = deepcopy(schema)
    for slot in rdf_schema.slots.values():
        if slot.minimum_cardinality == 1 and not slot.required:
            slot.minimum_cardinality = None
    return rdf_schema


def _run_linkml_generator(schema_view: SchemaView, generator: str, output_dir: Path, top_class: str | None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    if generator == 'jsonschema':
        logging.info("Proceeding with LinkML to JSON Schema conversion")
        json_schema_generator = WotJsonSchemaGenerator.from_options(
            schema_view.schema, JsonSchemaOptions(top_class=top_class)
        )
        raw_schema = json.loads(json_schema_generator.serialize())
        processed_schema = post_process_jsonschema(raw_schema, schema_view, top_class)
        output_file = output_dir / 'jsonschema.json'
        with output_file.open('w', encoding='utf-8') as f:
            json.dump(processed_schema, f, indent=2, ensure_ascii=False)
        logging.info(f"JSON Schema saved to {output_file}")

    elif generator == 'shacl':
        logging.info("Proceeding with LinkML to SHACL conversion")
        shacl_generator = ShaclGenerator(_for_rdf(schema_view.schema), mergeimports=False, closed=True, suffix='Shape')
        raw_shacl = shacl_generator.serialize()
        processed_shacl = post_process_shacl(raw_shacl, schema_view)
        (output_dir / 'shapes.shacl.ttl').write_text(processed_shacl, encoding='utf-8')
        logging.info(f"SHACL shapes saved to {output_dir / 'shapes.shacl.ttl'}")

    elif generator == 'owl':
        logging.info("Proceeding with LinkML to OWL conversion")
        owl_generator = OwlSchemaGenerator(_for_rdf(schema_view.schema))
        (output_dir / 'ontology.owl.ttl').write_text(owl_generator.serialize())
        logging.info(f"OWL ontology saved to {output_dir / 'ontology.owl.ttl'}")

    elif generator == 'jsonldcontext':
        logging.info("Proceeding with LinkML to JSON-LD Context conversion")
        context_generator = ContextGenerator(schema_view.schema, mergeimports=True)
        (output_dir / 'context.jsonld').write_text(context_generator.serialize())
        logging.info(f"JSON-LD context saved to {output_dir / 'context.jsonld'}")

    elif generator == 'linkml':
        logging.info("Proceeding with LinkML to LinkML YAML conversion (merged)")
        linkml_generator = LinkmlGenerator(schema_view.schema, mergeimports=True, format='yaml')
        (output_dir / 'linkml.yaml').write_text(linkml_generator.serialize())
        logging.info(f"Merged LinkML schema saved to {output_dir / 'linkml.yaml'}")

    else:
        logging.warning(f"Unknown generator: {generator}")


def run_pipeline(config: Config) -> None:
    """Run the configured generators, the spec last; raises SchemaError or GenerationError."""
    schema_view = _load_schema_view(config.root_schema)
    logging.info(f"Input schema {config.root_schema} loaded successfully!")

    for generator in config.generators:
        if generator in ("visualization", "spec"):
            continue
        logging.info(f"Proceeding with WoT resource generation for {generator}")
        try:
            view = schema_view
            if generator == "jsonschema" and config.jsonschema_profile is not None:
                view = SchemaView(config.jsonschema_profile, merge_imports=True)
            _run_linkml_generator(view, generator, config.output_dir / generator, config.top_class)
        except Exception as exc:
            raise GenerationError(f"{generator} generation failed: {exc}") from exc

    visualization_dir = config.output_dir / "static" / "visualization"
    if "visualization" in config.generators:
        diagrams = [(vocabulary.schema, vocabulary.diagram) for vocabulary in config.vocabularies if vocabulary.diagram]
        generate_visualizations(diagrams, visualization_dir)

    if config.spec is not None:
        shutil.copytree(STATIC_VISUALIZATION_PATH, visualization_dir, dirs_exist_ok=True)
        logging.info("Starting ReSpec specification generation...")
        generate_respec_spec(config.root_schema, config.spec, config.schema_prefixes)
        logging.info("ReSpec specification generation complete.")


def _load_schema_view(schema_path: Path) -> SchemaView:
    if not schema_path.is_file():
        raise SchemaError(f"{schema_path}: LinkML schema file not found.")
    try:
        schema_view = SchemaView(schema_path, merge_imports=True)
        schema_view.all_classes()
    except Exception as exc:
        raise SchemaError(f"{schema_path}: LinkML schema could not be loaded: {exc}") from exc
    return schema_view

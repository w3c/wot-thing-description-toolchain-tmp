import json
import logging

from pathlib import Path
import shutil
import subprocess

from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml.generators.shaclgen import ShaclGenerator
from linkml.generators.owlgen import OwlSchemaGenerator
from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml.generators.linkmlgen import LinkmlGenerator
from linkml.generators import dotgen
from linkml_runtime.utils.schemaview import SchemaView

from . import SCHEMA_PATH


def run_generator(schema_view: SchemaView, generator: str, output_dir: Path):
    """
    Runs the LinkML generator (JSON Schema, SHACL, OWL, JSON-LD Context,
    or LinkML YAML) and saves the output to the designated directory.

    :param schema_view: The loaded SchemaView object.
    :param generator: The name of the generator to run (e.g., 'jsonschema').
    :param output_dir: The target output directory.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if generator == 'jsonschema':
        logging.info("Proceeding with LinkML to JSON Schema conversion")
        json_schema_generator = JsonSchemaGenerator(schema_view.schema, mergeimports=True)
        processed_content = json_schema_generator.serialize()
        output_file = output_dir / 'jsonschema.json'
        with output_file.open('w', encoding='utf-8') as f:
            json.dump(processed_content, f, indent=2, ensure_ascii=False)
        logging.info(f"JSON Schema saved to {output_file}")

    elif generator == 'shacl':
        logging.info("Proceeding with LinkML to SHACL conversion")
        shacl_generator = ShaclGenerator(schema_view.schema, mergeimports=False, closed=True, suffix='Shape')
        (output_dir / 'shapes.shacl.ttl').write_text(shacl_generator.serialize())
        logging.info(f"SHACL shapes saved to {output_dir / 'shapes.shacl.ttl'}")

    elif generator == 'owl':
        logging.info("Proceeding with LinkML to OWL conversion")
        owl_generator = OwlSchemaGenerator(schema_view.schema)
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

    elif generator == "visualization":
        logging.info("Proceeding with UML visualization generation")
        generate_visualizations(SCHEMA_PATH, output_dir)

    else:
        logging.warning(f"Unknown generator: {generator}")


def _require_dot() -> bool:
    """Return True if Graphviz 'dot' is available; otherwise warn once."""
    if shutil.which("dot"):
        return True
    logging.warning("Graphviz 'dot' not found on PATH. Skipping UML diagram generation.")
    return False


def _dot_to_svg(dot_source: str, out_svg: Path) -> None:
    """Write DOT source to a temporary file and convert to SVG via Graphviz."""
    out_svg.parent.mkdir(parents=True, exist_ok=True)
    tmp_dot = out_svg.with_suffix(out_svg.suffix + ".dot")
    tmp_dot.write_text(dot_source, encoding="utf-8")
    subprocess.run(["dot", "-Tsvg", str(tmp_dot), "-o", str(out_svg)], check=True)


def generate_visualizations(schemas_dir: Path, visualization_dir: Path) -> None:
    """
    Generate one SVG figure per LinkML schema file:

      schemas/thing_description.yaml -> gens/visualization/td.svg
      schemas/jsonschema.yaml       -> gens/visualization/jsonschema.svg
      schemas/wot_security.yaml     -> gens/visualization/wotsec.svg
      schemas/hypermedia.yaml       -> gens/visualization/hctl.svg
    """

    if not _require_dot():
        return

    mapping = {
        "thing_description.yaml": ("td.svg", "TD core vocabulary"),
        "jsonschema.yaml": ("jsonschema.svg", "Data schema vocabulary"),
        "wot_security.yaml": ("wotsec.svg", "WoT security vocabulary"),
        "hypermedia.yaml": ("hctl.svg", "Hypermedia controls vocabulary"),
    }

    visualization_dir.mkdir(parents=True, exist_ok=True)

    for filename, (target_svg, label) in mapping.items():
        schema_path = schemas_dir / filename
        out_svg = visualization_dir / target_svg

        if not schema_path.exists():
            logging.warning("Schema not found for diagram (%s). Skipping %s.", schema_path, target_svg)
            continue

        try:
            logging.info("Generating UML diagram for %s → %s (%s)", filename, out_svg.name, label)
            sv = SchemaView(str(schema_path), merge_imports=True)
            dot = dotgen.DotGenerator(sv.schema, mergeimports=True)
            dot_source = dot.serialize()
            _dot_to_svg(dot_source, out_svg)
            logging.info("Saved %s", out_svg)
        except Exception as e:
            logging.error("Failed to generate %s from %s: %s", out_svg.name, schema_path, e, exc_info=True)

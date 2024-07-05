import argparse
import subprocess

from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml.generators.shaclgen import ShaclGenerator
from linkml.generators.owlgen import OwlSchemaGenerator
from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml.generators.docgen import DocGenerator
from linkml.generators.linkmlgen import LinkmlGenerator
from pathlib import Path

RESOURCES_PATH = Path('resources')
GENS_PATH = RESOURCES_PATH / 'gens'
SCHEMA_PATH = RESOURCES_PATH / 'schemas'
YAML_SCHEMA_PATH = SCHEMA_PATH / 'thing_description.yaml'
DOCDIR = GENS_PATH / 'docs' / 'ontology'
GENERATORS = ['jsonschema', 'shacl', 'jsonldcontext', 'linkml']

def serve_docs():
    subprocess.run(['mkdocs', 'serve'], check=True)


def generate_docs():
    DOCDIR.mkdir(parents=True, exist_ok=True)
    doc_generator = DocGenerator(YAML_SCHEMA_PATH, mergeimports=False)
    doc_generator.serialize(directory=str(DOCDIR))

def main(generate_docs_flag, serve_docs_flag):
    if not YAML_SCHEMA_PATH.exists():
        print(f"LinkML schema file does not exist: {YAML_SCHEMA_PATH}")
        return
    for generator in GENERATORS:
        output_dir = GENS_PATH / generator
        output_dir.mkdir(parents=True, exist_ok=True)
        if generator == 'jsonschema':
            # json_schema_generator = JsonSchemaGenerator(yaml_content, top_class="Thing")
            json_schema_generator = JsonSchemaGenerator(YAML_SCHEMA_PATH, mergeimports=True)
            (output_dir / 'jsonschema.json').write_text(json_schema_generator.serialize())
        elif generator == 'shacl':
            shacl_generator = ShaclGenerator(YAML_SCHEMA_PATH, mergeimports=False, closed=True, suffix='Shape')
            (output_dir / 'shapes.shacl.ttl').write_text(shacl_generator.serialize())
        elif generator == 'owl':
            owl_generator = OwlSchemaGenerator(YAML_SCHEMA_PATH,)
            (output_dir / 'ontology.owl.ttl').write_text(owl_generator.serialize())
        elif generator == 'jsonldcontext':
            context_generator = ContextGenerator(YAML_SCHEMA_PATH, mergeimports=False)
            (output_dir / 'context.jsonld').write_text(context_generator.serialize())
        elif generator == 'linkml':
            linkml_generator = LinkmlGenerator(YAML_SCHEMA_PATH, mergeimports=True, format='yaml', output='linkml.yaml')
            (output_dir / 'linkml.yaml').write_text(linkml_generator.serialize())
        else:
            print(f"Unknown generator: {generator}")
            continue

    if generate_docs_flag:
        generate_docs()

    if serve_docs_flag:
        generate_docs()
        serve_docs()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='WoT TD toolchain for automating specification generation')
    parser.add_argument('-l', '--local-docs', action='store_true',
                        help='Boolean for local documentation generation.')

    parser.add_argument('-s', '--serve-docs', action='store_true',
                        help='Boolean for serving the generated documentation.')
    args = parser.parse_args()
    main(args.local_docs, args.serve_docs)

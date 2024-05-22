import argparse
import yaml

from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml.generators.shaclgen import ShaclGenerator
from linkml.generators.shexgen import ShExGenerator
from linkml.generators.owlgen import OwlSchemaGenerator
from linkml.generators.markdowngen import MarkdownGenerator
from linkml.generators.jsonldgen import JSONLDGenerator
from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml.generators.typescriptgen import TypescriptGenerator
from linkml.generators.protogen import ProtoGenerator
from linkml.generators.docgen import DocGenerator
from pathlib import Path

RESOURCES_PATH = Path('resources')
GENS_PATH = RESOURCES_PATH / 'gens'
JSON_SCHEMA_PATH = GENS_PATH / 'jsonschema'
YAML_SCHEMA_PATH = RESOURCES_PATH / 'thing_description_schema.yaml'
SOURCE_PATH = Path('src')
LINKML_PATH = Path('linkml')
LINKML_GENERATORS_CONFIG_YAML_PATH = SOURCE_PATH / LINKML_PATH / 'config.yaml'
DOCDIR = GENS_PATH / 'docs'


def generate_docs(yaml_path, docdir):
    docdir.mkdir(parents=True, exist_ok=True)
    doc_generator = DocGenerator(yaml_path)
    doc_generator.serialize(directory=str(docdir))


def config_file_parse(config_path):
    with open(config_path, 'r') as config_file:
        config_content = config_file.read()
    yaml_content = yaml.safe_load(config_content)
    generator_args = yaml_content.get('generator_args', {})
    generators = list(generator_args.keys())
    return generators


def main(yaml_path, config_path, generate_docs_flag):
    yaml_content = yaml_path.read_text()
    generators = config_file_parse(config_path)

    for generator in generators:
        output_dir = GENS_PATH / generator
        output_dir.mkdir(parents=True, exist_ok=True)

        if generator == 'jsonschema':
            json_schema_generator = JsonSchemaGenerator(yaml_content)
            (JSON_SCHEMA_PATH / f'{yaml_path.stem}.json').write_text(json_schema_generator.serialize())
        elif generator == 'owl':
            owl_generator = OwlSchemaGenerator(yaml_content)
            (output_dir / f'{yaml_path.stem}.owl.ttl').write_text(owl_generator.serialize())
        elif generator == 'markdown':
            markdown_generator = MarkdownGenerator(yaml_content)
            (output_dir / f'{yaml_path.stem}.md').write_text(markdown_generator.serialize(directory=str(output_dir)))
        elif generator == 'shacl':
            shacl_generator = ShaclGenerator(yaml_content)
            (output_dir / f'{yaml_path.stem}.shacl.ttl').write_text(shacl_generator.serialize())
        elif generator == 'shex':
            shex_generator = ShExGenerator(yaml_content)
            (output_dir / f'{yaml_path.stem}.shex').write_text(shex_generator.serialize())
        elif generator == 'jsonld':
            jsonld_generator = JSONLDGenerator(yaml_content)
            (output_dir / f'{yaml_path.stem}.jsonld').write_text(jsonld_generator.serialize())
        elif generator == 'jsonldcontext':
            context_generator = ContextGenerator(yaml_content)
            (output_dir / f'{yaml_path.stem}.context.jsonld').write_text(context_generator.serialize())
        elif generator == 'typescript':
            typescript_generator = TypescriptGenerator(yaml_content)
            (output_dir / f'{yaml_path.stem}.js').write_text(typescript_generator.serialize())
        elif generator == 'protobuf':
            protobuf_generator = ProtoGenerator(yaml_content)
            (output_dir / f'{yaml_path.stem}.js').write_text(protobuf_generator.serialize())
        else:
            print(f"Unknown generator: {generator}")
            continue

    if generate_docs_flag:
        generate_docs(yaml_path, DOCDIR)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='WoT TD toolchain for automating specification generation')
    parser.add_argument('-y', '--yaml', default=YAML_SCHEMA_PATH,
                        help='Path to the LinkML schema formatted as a YAML file.')
    parser.add_argument('-c', '--config-file', default=LINKML_GENERATORS_CONFIG_YAML_PATH,
                        help='Path to YAML configuration for specifying the required LinkML generators.')
    parser.add_argument('-d', '--generate-docs', action='store_true',
                        help='Boolean for documentation generation.')
    args = parser.parse_args()
    main(Path(args.yaml), Path(args.config_file), args.generate_docs)

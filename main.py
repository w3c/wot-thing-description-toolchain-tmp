import argparse

import yaml
from linkml.generators.jsonschemagen import JsonSchemaGenerator
from pathlib import Path

RESOURCES_PATH = Path('resources')
GENS_PATH = RESOURCES_PATH / 'gens'
JSON_SCHEMA_PATH = GENS_PATH / 'jsonschema'
YAML_SCHEMA_PATH = RESOURCES_PATH / 'thing_description_schema.yaml'
SOURCE_PATH = Path('src')
LINKML_PATH = Path('linkml')
LINKML_GENERATORS_CONFIG_YAML_PATH = SOURCE_PATH / LINKML_PATH / 'config.yaml'


def config_file_parse(config_path):
    with open(config_path, 'r') as config_file:
        config_content = config_file.read()
    yaml_content = yaml.safe_load(config_content)
    generator_args = yaml_content.get('generator_args', {})
    generators = list(generator_args.keys())
    return generators


def main(yaml_path, config_path):
    generators = config_file_parse(config_path)
    yaml_content = yaml_path.read_text()
    json_schema_generator = JsonSchemaGenerator(yaml_content)
    (JSON_SCHEMA_PATH / f'{yaml_path.stem}.json').write_text(json_schema_generator.serialize())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='WoT TD toolchain for automating specification generation')
    parser.add_argument('-y', '--yaml', default=YAML_SCHEMA_PATH,
                        help='Path to the LinkML schema formatted as a YAML file.')
    parser.add_argument('-c', '--config-file', default=LINKML_GENERATORS_CONFIG_YAML_PATH,
                        help='Path to YAML configuration for specifying the required LinkML generators.')
    args = parser.parse_args()
    main(Path(args.yaml), Path(args.config_file))

import argparse
from linkml.generators.jsonschemagen import JsonSchemaGenerator
from pathlib import Path

RESOURCES_PATH = Path('resources')
GENS_PATH = RESOURCES_PATH / 'gens'
JSON_SCHEMA_PATH = GENS_PATH / 'jsonschema'
YAML_SCHEMA_PATH = RESOURCES_PATH / 'thing_description_schema.yaml'


def main(yaml_path):
    yaml_content = yaml_path.read_text()
    json_schema_generator = JsonSchemaGenerator(yaml_content)
    (JSON_SCHEMA_PATH / f'{yaml_path.stem}.json').write_text(json_schema_generator.serialize())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-y', '--yaml', default=RESOURCES_PATH / 'thing_description_schema.yaml',
                        help='the YAML file path including the LinkML schema.')
    args = parser.parse_args()
    main(Path(args.yaml))

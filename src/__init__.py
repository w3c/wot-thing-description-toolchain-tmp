from pathlib import Path


RESOURCES_PATH = Path('resources')
GENS_PATH = RESOURCES_PATH / 'gens'
SCHEMA_PATH = RESOURCES_PATH / 'schemas'
YAML_SCHEMA_PATH = SCHEMA_PATH / 'thing_description.yaml'
DOCDIR = GENS_PATH / 'docs' / 'ontology'

GENERATORS = ['jsonschema', 'shacl', 'jsonldcontext', 'linkml']

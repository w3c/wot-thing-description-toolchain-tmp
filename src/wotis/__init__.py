from pathlib import Path

RESOURCES_PATH = Path('resources')
GENS_PATH = RESOURCES_PATH / 'gens'
SCHEMA_PATH = RESOURCES_PATH / 'schemas'
MANUAL_PATH = RESOURCES_PATH / 'manuals'
YAML_SCHEMA_PATH = SCHEMA_PATH / 'thing_description.yaml'
GENERATED_LINKML_SCHEMA = GENS_PATH / 'linkml/linkml.yaml'
DOCDIR = GENS_PATH / 'docs' / 'ontology'

GENERATORS = ['jsonschema', 'shacl', 'jsonldcontext', 'linkml']
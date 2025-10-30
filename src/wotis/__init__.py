from pathlib import Path

RESOURCES_PATH = Path('resources')
GENS_PATH = RESOURCES_PATH / 'gens'
SCHEMA_PATH = RESOURCES_PATH / 'schemas'
MANUAL_PATH = RESOURCES_PATH / 'benchmark_schemas'
YAML_SCHEMA_PATH = SCHEMA_PATH / 'thing_description.yaml'
GENERATED_LINKML_SCHEMA = GENS_PATH / 'linkml/linkml.yaml'
DOCDIR = GENS_PATH / 'docs' / 'ontology'

GENERATORS = ['jsonschema', 'shacl', 'jsonldcontext', 'owl', 'linkml']

RESPEC_TEMPLATE_PATH = RESOURCES_PATH / 'index.template.html'
RESPEC_FRAGMENT_PATH = GENS_PATH / 'schema_fragment.html'
FINAL_SPEC_PATH = GENS_PATH / 'final-spec.html'
JINJA_TEMPLATE_DIR = RESOURCES_PATH / "jinja_templates"
CORE_SCHEMA_PLACEHOLDER = '%s'

from .postprocessors.jsonschema_postprocessor import post_process_jsonschema

__all__ = ['post_process_jsonschema']
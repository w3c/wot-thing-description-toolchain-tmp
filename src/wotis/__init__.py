from pathlib import Path

from .specgen.config import Config


RESOURCES_PATH = Path('resources')
SCHEMA_PATH = RESOURCES_PATH / 'schemas'
GENS_PATH = RESOURCES_PATH / 'gens'

CONFIG = Config.from_resources_dir(RESOURCES_PATH, placeholder="%s")

MANUAL_PATH = RESOURCES_PATH / 'benchmark_schemas'
YAML_SCHEMA_PATH = SCHEMA_PATH / 'thing_description.yaml'
GENERATED_LINKML_SCHEMA = GENS_PATH / 'linkml/linkml.yaml'
RESPEC_TEMPLATE_PATH = RESOURCES_PATH / 'index.template.html'
FINAL_SPEC_PATH = GENS_PATH / 'index.html'
GENERATORS = ['jsonschema', 'shacl', 'jsonldcontext', 'owl', 'linkml', 'visualization']

JINJA_TEMPLATE_DIR = CONFIG.jinja_templates
GLOSSARY_PATH = CONFIG.glossary_path
BIBLIO_PATH = CONFIG.biblio_path
CORE_SCHEMA_PLACEHOLDER = CONFIG.placeholder


__all__ = [
    "CONFIG",
    "RESOURCES_PATH", "SCHEMA_PATH", "GENS_PATH",
    "JINJA_TEMPLATE_DIR", "GLOSSARY_PATH", "BIBLIO_PATH",
    "CORE_SCHEMA_PLACEHOLDER", "YAML_SCHEMA_PATH",
    "GENERATED_LINKML_SCHEMA", "RESPEC_TEMPLATE_PATH", "FINAL_SPEC_PATH",
    "GENERATORS",
]
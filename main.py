import argparse
import json
import subprocess

from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml.generators.shaclgen import ShaclGenerator
from linkml.generators.owlgen import OwlSchemaGenerator
from linkml.generators.jsonldcontextgen import ContextGenerator
from linkml.generators.docgen import DocGenerator
from linkml.generators.linkmlgen import LinkmlGenerator
from linkml_runtime.utils.schemaview import SchemaView
from linkml_runtime.linkml_model.meta import AnonymousSlotExpression
from pathlib import Path
from pyld import jsonld

from linkml_runtime.linkml_model.meta import SlotDefinition

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


#camelCase conversion of class names in the generated context file
    # updated_context = {}
    # for cn, value in generated_context.items():
    #     camel_case_key = cn[0].lower() + cn[1:]
    #     if value != {}:
    #         updated_context[camel_case_key] = value
    # serialized_schema_json['@context'] = updated_context
    # generated_context = updated_context
def post_process_jsonld_context(schema_view: SchemaView, serialized_schema: str) -> str:
    serialized_schema_json = json.loads(serialized_schema)
    generated_context = serialized_schema_json.get('@context', {})
    default_range = schema_view.schema.default_range if schema_view.schema.default_range else "string"
    for slot in schema_view.all_slots().values():
        slot_name = slot.name
        context_entry = generated_context.get(slot_name, {})
        # Update JSON-LD context for slots with multi-language support
        is_langstring = slot.range == 'langString'
        is_exactly_one_language = (
            slot.range is None and
            any(
                expr.range == 'langString'
                for expr in slot.exactly_one_of if isinstance(expr, AnonymousSlotExpression)
            )
        )
        if is_langstring or is_exactly_one_language and isinstance(context_entry, dict):
            serialized_schema_json['@context'][slot_name]['@container'] = '@language'
            if '@type' in serialized_schema_json['@context'][slot_name].keys():
                del serialized_schema_json['@context'][slot_name]['@type']
        # Update JSON-LD context for slots with a specific encoded language
        if slot.in_language and isinstance(context_entry, dict):
            context_entry['@language'] = slot.in_language
        # inlined and multivalued slot conditions are used to identify dictionaries
        if slot.inlined and slot.multivalued and not slot.inlined_as_list and isinstance(context_entry, dict):
            context_entry['@container'] = '@index'
            if not hasattr(context_entry, '@type'):
                context_entry['@type'] = '@id'
            if slot.instantiates:
                context_entry['@index'] = slot.instantiates
        #exactly_one_of expressions
        if hasattr(slot, 'exactly_one_of') and slot.exactly_one_of:
            ranges = [opt['range'] for opt in slot.exactly_one_of if 'range' in opt]
            if len(set(ranges)) == 1:
                range_type = ranges[0]
                context_entry["@type"] = f"xsd:{range_type}"
            else:
                print(f"Warning: Slot {slot_name} has different ranges")
        elif slot.range == default_range:
            context_entry["@type"] = f"xsd:{default_range}"
        #Change property name with those that provide aliases
        # if slot.aliases and isinstance(context_entry, dict):
        #     generated_context[slot.aliases[0]] = generated_context.pop(slot_name)
        #     context_entry = generated_context[slot.aliases[0]]
        generated_context[slot_name] = context_entry
    #The multivalued slots which do not already have a @container are assigned to a @set
    for slot in schema_view.all_slots().values():
        context_entry = generated_context.get(slot.name, {})
        if slot.multivalued and isinstance(context_entry, dict) and '@container' not in context_entry:
            context_entry['@container'] = '@set'
            context_entry.pop('@type', None)
        generated_context[slot.name] = context_entry
    # for c in schema_view.all_classes().values():
    #     class_name = c.name
    #     context_entry = generated_context.get(class_name, {})
    #     if c.aliases and isinstance(context_entry, dict):
    #         generated_context[c.aliases[0]] = generated_context.pop(class_name)
    #         context_entry = generated_context[c.aliases[0]]
    #     generated_context[class_name] = context_entry
    return json.dumps(serialized_schema_json, indent=3)


def main(generate_docs_flag, serve_docs_flag):
    if not YAML_SCHEMA_PATH.exists():
        print(f"LinkML schema file does not exist: {YAML_SCHEMA_PATH}")
        return
    linkml_schema_view = SchemaView(YAML_SCHEMA_PATH, merge_imports=True)
    # TODO: add pre processing for LinkML if needed
    for generator in GENERATORS:
        output_dir = GENS_PATH / generator
        output_dir.mkdir(parents=True, exist_ok=True)
        if generator == 'jsonschema':
            # json_schema_generator = JsonSchemaGenerator(yaml_content, top_class="Thing")
            json_schema_generator = JsonSchemaGenerator(linkml_schema_view.schema, mergeimports=True)
            (output_dir / 'jsonschema.json').write_text(json_schema_generator.serialize())
        elif generator == 'shacl':
            shacl_generator = ShaclGenerator(linkml_schema_view.schema, mergeimports=False, closed=True, suffix='Shape')
            (output_dir / 'shapes.shacl.ttl').write_text(shacl_generator.serialize())
        elif generator == 'owl':
            owl_generator = OwlSchemaGenerator(linkml_schema_view.schema,)
            (output_dir / 'ontology.owl.ttl').write_text(owl_generator.serialize())
        elif generator == 'jsonldcontext':
            context_generator = ContextGenerator(linkml_schema_view.schema, mergeimports=True)
            (output_dir / 'context.jsonld').write_text(post_process_jsonld_context(linkml_schema_view,
                                                                                   context_generator.serialize()))
        elif generator == 'linkml':
            linkml_generator = LinkmlGenerator(linkml_schema_view.schema, mergeimports=True, format='yaml', output='linkml.yaml')
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


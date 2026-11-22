"""Entry point that turns the raw LinkML JSON-LD context into the published merged context."""

import json
from collections.abc import Collection

from linkml_runtime.utils.schemaview import SchemaView

from wot_toolchain.artifacts.jsonld_context.generator import WotContextGenerator
from wot_toolchain.artifacts.jsonld_context.module_context import _module_contexts
from wot_toolchain.artifacts.jsonld_context.options import JsonLdContextOptions
from wot_toolchain.artifacts.jsonld_context.passes import POST_SCOPING_PASSES, PRE_SCOPING_PASSES
from wot_toolchain.artifacts.jsonld_context.scoped_contexts import apply_class_mappings as _apply_class_mappings
from wot_toolchain.artifacts.jsonld_context.scoped_contexts import apply_root_mapping as _apply_root_mapping
from wot_toolchain.artifacts.passes import run_passes


def post_process_jsonld_context(
    schema_view: SchemaView, serialized_schema: str, *, extra_root_terms: Collection[str]
) -> str:
    """Add schema-declared scoped contexts and index predicates to LinkML output.

    LinkML natively emits container mappings when
    ``fix_multivalue_containers`` is enabled. It does not currently emit the
    RDF predicate represented by a keyed map, or scoped vocabulary contexts.

    Args:
        schema_view: SchemaView of the main schema.
        serialized_schema: JSON-LD context serialized by LinkML's ``ContextGenerator``.
        extra_root_terms: Terms outside the schema's default prefix that stay in the root context.

    Returns:
        The post-processed JSON-LD context document, serialized as JSON.

    Raises:
        SchemaError: Schema content cannot be composed into a JSON-LD context (the message names the
            offending element), or an extra root term is not in the generated root context.
    """
    document = json.loads(serialized_schema)
    context = document["@context"]
    run_passes(PRE_SCOPING_PASSES, context, schema_view, extra_root_terms)
    generator = WotContextGenerator.from_options(schema_view.schema, JsonLdContextOptions())
    module_contexts = _module_contexts(schema_view, generator)
    for slot in schema_view.all_slots().values():
        _apply_root_mapping(context, schema_view, slot, module_contexts)
    _apply_class_mappings(schema_view, context, module_contexts)
    run_passes(POST_SCOPING_PASSES, context, schema_view, extra_root_terms)
    context["@version"] = 1.1
    return json.dumps(document, indent=2)

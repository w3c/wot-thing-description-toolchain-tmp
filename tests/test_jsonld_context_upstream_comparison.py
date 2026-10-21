"""Compare generated JSON-LD contexts against upstream W3C contexts.

Each test documents a concrete delta between the LinkML-generated context
and the upstream W3C TD 1.1 context.  Tests are grouped by module and
annotated with a classification:

    BUG_IN_GENERATED   – generated context is wrong, needs a fix
    LINKML_LIMITATION   – known LinkML JSON-LD context generator gap
    DESIGN_CHOICE       – intentional difference (e.g. modular prefixes)

Tests use ``pytest.mark.xfail`` so the suite stays green while deltas
are tracked and prioritised.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
UP = REPO / "resources" / "upstream" / "context"
GEN = REPO / "resources" / "gens" / "jsonldcontext"


def _load(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw.get("@context", raw)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def td_upstream():
    return _load(UP / "td-context.jsonld")


@pytest.fixture(scope="module")
def td_generated():
    return _load(GEN / "td-context.jsonld")


@pytest.fixture(scope="module")
def js_upstream():
    return _load(UP / "json-schema-context.jsonld")


@pytest.fixture(scope="module")
def js_generated():
    return _load(GEN / "json-schema-context.jsonld")


@pytest.fixture(scope="module")
def ws_upstream():
    return _load(UP / "wot-security-context.jsonld")


@pytest.fixture(scope="module")
def ws_generated():
    return _load(GEN / "wot-security-context.jsonld")


@pytest.fixture(scope="module")
def hctl_upstream():
    return _load(UP / "hypermedia-context.jsonld")


@pytest.fixture(scope="module")
def hctl_generated():
    return _load(GEN / "hypermedia-context.jsonld")


@pytest.fixture(scope="module")
def merged():
    return _load(GEN / "context.jsonld")


# ===================================================================
# TD MODULE
# ===================================================================

class TestTdModule:
    """Deltas in the td-context module."""

    def test_name_maps_to_td_name(self, td_upstream, td_generated):
        """name must map to td:name data property, not @id."""
        expected = td_upstream["name"]  # {"@id": "td:name"}
        assert td_generated.get("name") == expected

    @pytest.mark.xfail(reason="INTENTIONAL_DEVIATION: upstream @language: en breaks multilanguage TDs — see jsonld-context-composition.md")
    def test_title_has_language_tag(self, td_upstream, td_generated):
        """title carries @language: "en" upstream but we omit it intentionally.

        Term-level @language overrides document-level @language unconditionally
        (JSON-LD 1.1 §9.8), breaking roundtrips for non-English TDs like
        string-direction-td-valid.jsonld where Arabic text in title gets tagged
        as @language: en. We omit @language to allow document-level override.
        """
        upstream = td_upstream["title"]
        assert "@language" in upstream
        gen = td_generated.get("title", {})
        assert isinstance(gen, dict), f"title should be a dict, got {type(gen)}"
        assert gen.get("@language") == "en"

    @pytest.mark.xfail(reason="INTENTIONAL_DEVIATION: upstream @language: en breaks multilanguage TDs — see jsonld-context-composition.md")
    def test_description_has_language_tag(self, td_upstream, td_generated):
        """description carries @language: "en" upstream but we omit it intentionally.

        Same rationale as title — term-level @language prevents document-level
        override, breaking multilanguage TD roundtrips.
        """
        gen = td_generated.get("description", {})
        assert isinstance(gen, dict)
        assert gen.get("@language") == "en"

    @pytest.mark.xfail(reason="DESIGN_CHOICE: @type: xsd:string is redundant — string is default JSON-LD type")
    def test_security_has_string_type(self, td_upstream, td_generated):
        """Upstream explicitly sets @type: xsd:string on security.

        Upstream: {"@id": "td:hasSecurityConfiguration", "@type": "xsd:string"}
        Generated: {"@id": "hasSecurityConfiguration"}  (no @type)

        String is the default JSON-LD datatype (§4.2.2). Omitting @type
        is semantically equivalent — values stay plain strings either way.
        """
        gen = td_generated.get("security", {})
        assert isinstance(gen, dict)
        assert gen.get("@type") == "xsd:string"

    @pytest.mark.xfail(reason="DESIGN_CHOICE: @type: xsd:string is redundant — string is default JSON-LD type")
    def test_instance_has_string_type(self, td_upstream, td_generated):
        """Upstream explicitly sets @type: xsd:string on instance.

        Upstream: {"@id": "td:instance", "@type": "xsd:string"}
        Generated: {"@id": "td:instance"}  (no @type)

        Same as security — omitting redundant xsd:string is correct.
        """
        gen = td_generated.get("instance", {})
        assert isinstance(gen, dict)
        assert gen.get("@type") == "xsd:string"

    @pytest.mark.xfail(reason="LINKML_LIMITATION: LinkML omits @type: @id for OWL-only object properties without range")
    def test_hasInstanceConfiguration_has_id_type(self, td_upstream, td_generated):
        """hasInstanceConfiguration carries @type: @id upstream.

        Upstream: {"@id": "td:hasInstanceConfiguration", "@type": "@id"}
        Generated: {"@id": "td:hasInstanceConfiguration"}  (missing @type)

        OWL-only object property with no LinkML range — generator cannot
        infer that values are IRIs.
        """
        gen = td_generated.get("hasInstanceConfiguration", {})
        assert isinstance(gen, dict)
        assert gen.get("@type") == "@id"

    def test_extra_hasInteractionAffordance_is_harmless(self, td_upstream, td_generated):
        """DESIGN_CHOICE: generated has hasInteractionAffordance (not in upstream).

        This is a LinkML artifact — the class hierarchy produces a term that
        upstream omits because it uses scoped contexts instead. Harmless.
        """
        assert "hasInteractionAffordance" not in td_upstream
        # Just documenting: generated has it, upstream does not.
        # Not a bug, just a design difference.


# ===================================================================
# JSON SCHEMA MODULE
# ===================================================================

class TestJsonSchemaModule:
    """Deltas in the json-schema-context module."""

    @pytest.mark.xfail(reason="BUG_IN_UPSTREAM: upstream maps type → @type for type discrimination; our jsonschema:type is ontologically correct (+ SKOS leak is separate issue)")
    def test_type_mapping_difference(self, js_upstream, js_generated):
        """Upstream maps `type` → `@type` for JSON-LD type discrimination.

        Upstream: {"@id": "@type"} — overloads `type` key as JSON-LD @type keyword
        Generated: {"@context": {...SKOS...}, "@id": "jsonschema:type"} — maps to ontology predicate

        Our mapping to jsonschema:type is ontologically correct. Upstream's @type
        mapping is a convenience for type discrimination in JSON-LD processing
        but conflates a data property with the RDF type assertion.
        The SKOS @context leak on enum slot is a separate issue.
        """
        assert js_upstream["type"] == {"@id": "@type"}
        gen = js_generated.get("type", {})
        assert gen.get("@id") == "@type", f"type @id should be @type, got {gen.get('@id')}"
        assert "@context" not in gen, "type should not have SKOS @context"

    @pytest.mark.xfail(reason="BUG_IN_GENERATED: enum should not have @type: @id — values are arbitrary JSON")
    def test_enum_no_id_type(self, js_upstream, js_generated):
        """IMPORTANT: `enum` should not have @type: "@id".

        Upstream: {"@id": "jsonschema:enum", "@container": "@set"}
        Generated: {"@type": "@id", "@container": "@set", "@id": "jsonschema:enum"}

        Enum values are arbitrary JSON values (strings, numbers, etc.),
        not IRIs. Forcing @type: @id makes the processor try to resolve
        them as node references.
        """
        gen = js_generated.get("enum", {})
        assert "@type" not in gen or gen["@type"] != "@id"

    @pytest.mark.xfail(reason="BUG_IN_GENERATED: const should not have @type: @id")
    def test_const_no_id_type(self, js_upstream, js_generated):
        """IMPORTANT: `const` should not have @type: "@id"."""
        gen = js_generated.get("const", {})
        assert "@type" not in gen or gen["@type"] != "@id"

    @pytest.mark.xfail(reason="BUG_IN_GENERATED: default should not have @type: @id")
    def test_default_no_id_type(self, js_upstream, js_generated):
        """IMPORTANT: `default` should not have @type: "@id"."""
        gen = js_generated.get("default", {})
        assert "@type" not in gen or gen["@type"] != "@id"

    @pytest.mark.xfail(reason="BUG_IN_GENERATED: SKOS @context leak on contentEncoding")
    def test_contentEncoding_no_skos(self, js_upstream, js_generated):
        """IMPORTANT: `contentEncoding` should be a plain string, no SKOS.

        Upstream: {"@id": "jsonschema:contentEncoding"}
        Generated: {"@context": {...SKOS...}, "@id": "jsonschema:contentEncoding"}
        """
        gen = js_generated.get("contentEncoding", {})
        assert "@context" not in gen

    @pytest.mark.xfail(reason="BUG_IN_GENERATED: SKOS @context leak on contentMediaType")
    def test_contentMediaType_no_skos(self, js_upstream, js_generated):
        """IMPORTANT: `contentMediaType` should be a plain string, no SKOS."""
        gen = js_generated.get("contentMediaType", {})
        assert "@context" not in gen

    @pytest.mark.xfail(reason="BUG_IN_GENERATED: anyOf missing from generated context")
    def test_anyOf_present(self, js_upstream, js_generated):
        """IMPORTANT: `anyOf` must be present with @container: @set.

        Upstream: {"@id": "jsonschema:anyOf", "@container": "@set"}
        Generated: MISSING
        """
        assert js_upstream["anyOf"] == {"@id": "jsonschema:anyOf", "@container": "@set"}
        assert "anyOf" in js_generated

    @pytest.mark.xfail(reason="BUG_IN_GENERATED: unit missing — should map to schema:unitCode with @type: @vocab")
    def test_unit_present(self, js_upstream, js_generated):
        """IMPORTANT: `unit` must map to schema:unitCode with @type: @vocab.

        Upstream: {"@id": "schema:unitCode", "@type": "@vocab"}
        Generated: MISSING
        """
        assert js_upstream["unit"] == {"@id": "schema:unitCode", "@type": "@vocab"}
        assert "unit" in js_generated
        gen = js_generated["unit"]
        assert gen.get("@id") == "schema:unitCode"
        assert gen.get("@type") == "@vocab"

    @pytest.mark.xfail(reason="LINKML_LIMITATION: explicit @type on numeric/boolean slots (upstream omits, JSON-LD 1.1 handles natively)")
    def test_no_explicit_type_on_numeric_terms(self, js_upstream, js_generated):
        """MINOR: Numeric terms should not need explicit @type.

        JSON-LD 1.1 natively handles numeric and boolean coercion, so
        upstream omits @type on minimum, maximum, readOnly, writeOnly, etc.
        LinkML generator adds explicit types which are harmless but noisy.
        """
        for term in ("minimum", "maximum", "readOnly", "writeOnly"):
            up = js_upstream.get(term, {})
            gen = js_generated.get(term, {})
            assert "@type" not in up, f"upstream {term} should not have @type"
            if "@type" in gen:
                pytest.fail(f"generated {term} has unnecessary @type: {gen['@type']}")

    @pytest.mark.xfail(reason="LINKML_LIMITATION: lowercase type aliases not emitted by LinkML generator")
    def test_lowercase_type_aliases(self, js_upstream, js_generated):
        """IMPORTANT: Lowercase type aliases (object, array, etc.) must exist.

        Upstream maps: object → jsonschema:ObjectSchema, array → jsonschema:ArraySchema, etc.
        These enable `"type": "object"` to expand to the correct RDF class.
        """
        aliases = {
            "object": "jsonschema:ObjectSchema",
            "array": "jsonschema:ArraySchema",
            "boolean": "jsonschema:BooleanSchema",
            "string": "jsonschema:StringSchema",
            "number": "jsonschema:NumberSchema",
            "integer": "jsonschema:IntegerSchema",
            "null": "jsonschema:NullSchema",
        }
        for alias, expected_iri in aliases.items():
            assert alias in js_upstream, f"upstream should have {alias}"
            assert js_upstream[alias] == expected_iri
            assert alias in js_generated, f"generated missing type alias: {alias}"


# ===================================================================
# WOT SECURITY MODULE
# ===================================================================

class TestWotSecurityModule:
    """Deltas in the wot-security-context module."""

    @pytest.mark.xfail(reason="BUG_IN_GENERATED: URI properties use xsd:anyURI instead of @id — produces literals instead of links")
    @pytest.mark.parametrize("term", ["authorization", "token", "refresh", "proxy"])
    def test_uri_properties_use_id_type(self, ws_upstream, ws_generated, term):
        """CRITICAL: URI properties must use @type: "@id", not xsd:anyURI.

        Using xsd:anyURI produces RDF literals instead of IRI references.
        JSON-LD processors cannot follow literal URIs for dereferencing.
        """
        up = ws_upstream[term]
        assert up["@type"] == "@id"
        gen = ws_generated.get(term, {})
        assert gen.get("@type") == "@id", f"{term}: got @type={gen.get('@type')}, expected @id"

    @pytest.mark.xfail(reason="LINKML_LIMITATION: scheme → @type mapping not emitted by LinkML generator")
    def test_scheme_maps_to_at_type(self, ws_upstream, ws_generated):
        """CRITICAL: `scheme` must map to @type.

        Upstream: {"@id": "@type"}
        Generated: MISSING

        This enables `"scheme": "nosec"` to expand to rdf:type.
        """
        assert ws_upstream["scheme"] == {"@id": "@type"}
        assert "scheme" in ws_generated
        assert ws_generated["scheme"].get("@id") == "@type"

    @pytest.mark.xfail(reason="LINKML_LIMITATION: short scheme aliases not emitted by LinkML generator")
    @pytest.mark.parametrize("alias,expected_iri", [
        ("nosec", "wotsec:NoSecurityScheme"),
        ("basic", "wotsec:BasicSecurityScheme"),
        ("digest", "wotsec:DigestSecurityScheme"),
        ("bearer", "wotsec:BearerSecurityScheme"),
        ("psk", "wotsec:PSKSecurityScheme"),
        ("oauth2", "wotsec:OAuth2SecurityScheme"),
        ("apikey", "wotsec:APIKeySecurityScheme"),
        ("auto", "wotsec:AutoSecurityScheme"),
        ("combo", "wotsec:ComboSecurityScheme"),
        ("cert", "wotsec:CertSecurityScheme"),
        ("pop", "wotsec:PoPSecurityScheme"),
    ])
    def test_scheme_aliases_present(self, ws_upstream, ws_generated, alias, expected_iri):
        """CRITICAL: Short scheme aliases must exist for type coercion.

        These enable `"scheme": "nosec"` to expand to wotsec:NoSecurityScheme.
        Without them, the scheme string stays a literal.
        """
        assert ws_upstream.get(alias) == expected_iri
        assert ws_generated.get(alias) == expected_iri

    @pytest.mark.xfail(reason="BUG_IN_GENERATED: SKOS @context leak on enum properties")
    @pytest.mark.parametrize("term", ["in", "alg", "flow", "qop", "format"])
    def test_enum_properties_no_skos(self, ws_upstream, ws_generated, term):
        """IMPORTANT: Enum properties should not have SKOS @context.

        LinkML emits SKOS context blocks for enum-valued slots. Upstream
        treats them as plain strings. The SKOS leak adds noise and can
        interfere with term resolution.
        """
        gen = ws_generated.get(term, {})
        assert "@context" not in gen, f"{term} has SKOS @context leak"

    @pytest.mark.xfail(reason="LINKML_LIMITATION: cross-module terms not duplicated in per-module context")
    @pytest.mark.parametrize("term,expected_id", [
        ("description", "td:description"),
        ("descriptions", "td:descriptionInLanguage"),
    ])
    def test_cross_module_terms_present(self, ws_upstream, ws_generated, term, expected_id):
        """IMPORTANT: Cross-module terms must be present in each module.

        Upstream duplicates description/descriptions in the wotsec module
        because security schemes need them. The generated per-module context
        omits them since LinkML maps them to the td module only.
        """
        assert term in ws_upstream
        assert ws_upstream[term]["@id"] == expected_id
        assert term in ws_generated


# ===================================================================
# HCTL (HYPERMEDIA) MODULE
# ===================================================================

class TestHctlModule:
    """Deltas in the hypermedia-context module."""

    @pytest.mark.xfail(reason="BUG_IN_GENERATED: op missing @type: @vocab — breaks operation type resolution")
    def test_op_has_vocab_type(self, hctl_upstream, hctl_generated):
        """CRITICAL: `op` must have @type: "@vocab".

        Upstream: {"@id": "hctl:hasOperationType", "@type": "@vocab"}
        Generated: {"@id": "hctl:hasOperationType"}  (missing @type)

        Without @vocab, operation type strings like "readproperty" stay
        as plain literals instead of resolving to td:readProperty via
        the @vocab + alias mechanism.
        """
        gen = hctl_generated.get("op", {})
        assert gen.get("@type") == "@vocab"

    @pytest.mark.xfail(reason="LINKML_LIMITATION: operation type aliases not emitted by LinkML generator")
    @pytest.mark.parametrize("alias,expected_iri", [
        ("readproperty", "td:readProperty"),
        ("writeproperty", "td:writeProperty"),
        ("observeproperty", "td:observeProperty"),
        ("unobserveproperty", "td:unobserveProperty"),
        ("invokeaction", "td:invokeAction"),
        ("queryaction", "td:queryAction"),
        ("cancelaction", "td:cancelAction"),
        ("subscribeevent", "td:subscribeEvent"),
        ("unsubscribeevent", "td:unsubscribeEvent"),
        ("readallproperties", "td:readAllProperties"),
        ("writeallproperties", "td:writeAllProperties"),
        ("readmultipleproperties", "td:readMultipleProperties"),
        ("writemultipleproperties", "td:writeMultipleProperties"),
        ("observeallproperties", "td:observeAllProperties"),
        ("unobserveallproperties", "td:unobserveAllProperties"),
        ("queryallactions", "td:queryAllActions"),
        ("subscribeallevents", "td:subscribeAllEvents"),
        ("unsubscribeallevents", "td:unsubscribeAllEvents"),
    ])
    def test_operation_type_aliases(self, hctl_upstream, hctl_generated, alias, expected_iri):
        """CRITICAL: All 18 operation type aliases must exist.

        These lowercase aliases enable `"op": "readproperty"` to resolve
        to td:readProperty via the @vocab mechanism.
        """
        assert hctl_upstream.get(alias) == expected_iri
        assert alias in hctl_generated, f"missing operation alias: {alias}"
        assert hctl_generated[alias] == expected_iri

    @pytest.mark.xfail(reason="BUG_IN_GENERATED: anchor uses xsd:anyURI instead of @id")
    def test_anchor_uses_id_type(self, hctl_upstream, hctl_generated):
        """IMPORTANT: `anchor` must use @type: "@id", not xsd:anyURI.

        Same pattern as wotsec URI properties — xsd:anyURI produces
        literals, @id produces IRI references.
        """
        assert hctl_upstream["anchor"]["@type"] == "@id"
        gen = hctl_generated.get("anchor", {})
        assert gen.get("@type") == "@id"

    @pytest.mark.xfail(reason="LINKML_LIMITATION: LinkML omits @type: @id for string-ranged slot used as IRI reference")
    def test_schema_has_id_type(self, hctl_upstream, hctl_generated):
        """schema (additionalOutputSchema) needs @type: @id upstream.

        Upstream: {"@id": "hctl:hasAdditionalOutputSchema", "@type": "@id"}
        Generated: {"@id": "hctl:hasAdditionalOutputSchema"}  (missing @type)

        LinkML generator cannot infer @type: @id from range: string.
        """
        assert hctl_upstream["schema"]["@type"] == "@id"
        gen = hctl_generated.get("schema", {})
        assert gen.get("@type") == "@id"

    @pytest.mark.xfail(reason="LINKML_LIMITATION: response has extra @type: @id (upstream omits)")
    def test_response_no_extra_id_type(self, hctl_upstream, hctl_generated):
        """MINOR: `response` should not have @type: "@id".

        Upstream: {"@id": "hctl:returns"}
        Generated: {"@type": "@id", "@id": "hctl:returns"}

        Harmless but diverges from upstream. The response object is
        typically embedded (inlined), not referenced by IRI.
        """
        up = hctl_upstream["response"]
        assert "@type" not in up
        gen = hctl_generated.get("response", {})
        assert "@type" not in gen

    @pytest.mark.xfail(reason="LINKML_LIMITATION: additionalResponses has extra @type: @id")
    def test_additionalResponses_no_extra_id_type(self, hctl_upstream, hctl_generated):
        """MINOR: `additionalResponses` should not have @type: "@id"."""
        up = hctl_upstream["additionalResponses"]
        assert "@type" not in up
        gen = hctl_generated.get("additionalResponses", {})
        assert "@type" not in gen

    @pytest.mark.xfail(reason="LINKML_LIMITATION: success has explicit xsd:boolean (upstream omits, JSON-LD 1.1 handles natively)")
    def test_success_no_explicit_boolean_type(self, hctl_upstream, hctl_generated):
        """MINOR: `success` should not need explicit xsd:boolean type."""
        up = hctl_upstream.get("success", {})
        assert "@type" not in up
        gen = hctl_generated.get("success", {})
        assert "@type" not in gen

    @pytest.mark.xfail(reason="BUG_IN_GENERATED: SKOS @context leak on subprotocol")
    def test_subprotocol_no_skos(self, hctl_upstream, hctl_generated):
        """MINOR: `subprotocol` should not have SKOS @context."""
        gen = hctl_generated.get("subprotocol", {})
        assert "@context" not in gen


# ===================================================================
# CROSS-MODULE PATTERNS
# ===================================================================

class TestCrossModulePatterns:
    """Tests for patterns that repeat across modules."""

    @pytest.mark.xfail(reason="BUG_IN_GENERATED: SKOS @context leak affects multiple modules")
    def test_no_skos_context_leak_anywhere(self, merged):
        """Cross-cutting: No term should have a SKOS @context block.

        LinkML emits SKOS context (text/description/meaning) for enum-valued
        slots. Upstream never uses this pattern. The SKOS blocks pollute
        the context and can interfere with term resolution.
        """
        skos_leaks = []
        for key, value in merged.items():
            if isinstance(value, dict) and "@context" in value:
                ctx = value["@context"]
                if isinstance(ctx, dict) and "meaning" in ctx:
                    skos_leaks.append(key)
        assert skos_leaks == [], f"SKOS @context leak in: {skos_leaks}"

    @pytest.mark.xfail(reason="BUG_IN_GENERATED: xsd:anyURI used where @id is needed")
    def test_no_xsd_anyuri_for_link_properties(self, merged):
        """Cross-cutting: Link properties must use @type: @id, not xsd:anyURI.

        xsd:anyURI produces RDF Literal nodes. @id produces IRI references
        that JSON-LD processors can follow. The upstream context uses @id
        for all dereferenceable URI properties.
        """
        # These are documented in upstream as @type: @id
        link_properties = ["authorization", "token", "refresh", "proxy", "anchor"]
        wrong = []
        for key in link_properties:
            # Check in merged context and all scoped contexts
            val = merged.get(key, {})
            if isinstance(val, dict) and val.get("@type") == "xsd:anyURI":
                wrong.append(key)
            # Also check inside securityDefinitions @context
            sd = merged.get("securityDefinitions", {})
            if isinstance(sd, dict) and "@context" in sd:
                sd_val = sd["@context"].get(key, {})
                if isinstance(sd_val, dict) and sd_val.get("@type") == "xsd:anyURI":
                    if key not in wrong:
                        wrong.append(key)
        assert wrong == [], f"Properties using xsd:anyURI instead of @id: {wrong}"

"""Systematic JSON-LD round-trip tests using jsonld.js over real TD instances.

Uses Node.js subprocess with Digital Bazaar's jsonld.js (JSON-LD 1.1 reference
processor) because pyld does not implement property-based @index containers.
"""

from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path
from typing import Any

import pytest

from .baselines import load_baseline

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTEXT_PATH = REPO_ROOT / "resources/gens/jsonldcontext/context.jsonld"
TEST_DATA = Path(__file__).parent / "data"
JSONLD_MODULE = str(REPO_ROOT / "node_modules" / "jsonld")

_WOT_CONTEXT_URLS = {
    "https://www.w3.org/2022/wot/td/v1.1",
    "https://www.w3.org/2019/wot/td/v1",
    "https://www.w3.org/ns/wot-next/td",
}


def _valid_instances() -> list[Path]:
    return sorted(TEST_DATA.glob("**/*-valid.jsonld"))


def _instance_id(path: Path) -> str:
    return str(path.relative_to(TEST_DATA))


KNOWN_ROUNDTRIP_FAILURES = Path(__file__).parent / "known_failures" / "jsonld_roundtrip.txt"

_instances = _valid_instances()
_instance_ids = [_instance_id(p) for p in _instances]


def _run_jsonld_js(script: str, timeout: int = 30) -> dict[str, Any]:
    """Run a Node.js script using jsonld.js and return parsed JSON result."""
    result = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        raise RuntimeError(f"jsonld.js error: {result.stderr}")
    return json.loads(result.stdout)


def _substitute_context_js() -> str:
    """Return JS code for context substitution helpers."""
    return textwrap.dedent(f"""\
        const jsonld = require('{JSONLD_MODULE}');
        const fs = require('fs');
        const WOT_URLS = new Set({json.dumps(sorted(_WOT_CONTEXT_URLS))});
        const ctx = JSON.parse(fs.readFileSync('{CONTEXT_PATH}', 'utf8'))['@context'];

        function substituteContext(doc) {{
            const raw = doc['@context'];
            if (!raw) {{ doc['@context'] = ctx; return doc; }}
            if (typeof raw === 'string') {{ doc['@context'] = ctx; return doc; }}
            if (Array.isArray(raw)) {{
                const ext = raw.filter(e => !(typeof e === 'string' && WOT_URLS.has(e)));
                doc['@context'] = ext.length ? [ctx, ...ext] : ctx;
                return doc;
            }}
            doc['@context'] = ctx;
            return doc;
        }}

        function getCompactionContext(doc) {{
            return doc['@context'];
        }}
    """)


def _normalize_helpers_js() -> str:
    """Return JS code for comparison normalization."""
    return textwrap.dedent("""\
        const SPEC_META_KEYS = new Set(["$title", "$description"]);

        function isBcp47Tag(s) {
            return /^[a-zA-Z]{2,3}(-[a-zA-Z0-9]{1,8})*$/.test(s);
        }

        function stripMeta(obj) {
            if (Array.isArray(obj)) return obj.map(stripMeta);
            if (obj && typeof obj === 'object') {
                const result = {};
                for (const [k, v] of Object.entries(obj)) {
                    if (SPEC_META_KEYS.has(k)) continue;
                    const nk = k === '@id' ? 'id' : k;
                    result[nk] = stripMeta(v);
                }
                return result;
            }
            return obj;
        }

        function normalize(obj) {
            if (Array.isArray(obj)) {
                if (obj.length === 1 && typeof obj[0] !== 'object') return normalize(obj[0]);
                return obj.map(normalize);
            }
            if (obj && typeof obj === 'object') {
                const result = {};
                for (const k of Object.keys(obj).sort()) {
                    const nk = isBcp47Tag(k) ? k.toLowerCase() : k;
                    result[nk] = normalize(obj[k]);
                }
                return result;
            }
            if (typeof obj === 'number' && obj === Math.floor(obj)) return Math.floor(obj);
            return obj;
        }

        function comparable(doc) {
            const stripped = {};
            for (const [k, v] of Object.entries(doc)) {
                if (k !== '@context') stripped[k] = v;
            }
            return normalize(stripMeta(stripped));
        }
    """)


def _expand_script(instance_path: Path) -> str:
    """Generate JS script to test expansion."""
    return (
        _substitute_context_js()
        + _normalize_helpers_js()
        + textwrap.dedent(f"""\
        async function main() {{
            const raw = JSON.parse(fs.readFileSync('{instance_path}', 'utf8'));
            const doc = substituteContext(JSON.parse(JSON.stringify(raw)));
            try {{
                const expanded = await jsonld.expand(doc);
                const types = expanded[0] ? (expanded[0]['@type'] || []) : [];
                const allIris = types.every(t => t.startsWith('http'));
                console.log(JSON.stringify({{
                    status: 'ok',
                    count: expanded.length,
                    typesAreIris: allIris
                }}));
            }} catch (e) {{
                console.log(JSON.stringify({{ status: 'error', message: e.message }}));
            }}
        }}
        main();
    """)
    )


def _roundtrip_script(instance_path: Path) -> str:
    """Generate JS script to test expand→compact roundtrip."""
    return (
        _substitute_context_js()
        + _normalize_helpers_js()
        + textwrap.dedent(f"""\
        async function main() {{
            const raw = JSON.parse(fs.readFileSync('{instance_path}', 'utf8'));
            const doc = substituteContext(JSON.parse(JSON.stringify(raw)));
            try {{
                const compactCtx = getCompactionContext(doc);
                const expanded = await jsonld.expand(doc);
                const compacted = await jsonld.compact(expanded, compactCtx);
                const original = comparable(doc);
                const result = comparable(compacted);
                const origStr = JSON.stringify(original);
                const resStr = JSON.stringify(result);
                if (origStr === resStr) {{
                    console.log(JSON.stringify({{ status: 'pass' }}));
                }} else {{
                    const allKeys = new Set([...Object.keys(original), ...Object.keys(result)]);
                    const diverged = [];
                    for (const k of [...allKeys].sort()) {{
                        if (JSON.stringify(original[k]) !== JSON.stringify(result[k])) {{
                            diverged.push(k);
                        }}
                    }}
                    console.log(JSON.stringify({{ status: 'fail', diverged }}));
                }}
            }} catch (e) {{
                console.log(JSON.stringify({{ status: 'error', message: e.message }}));
            }}
        }}
        main();
    """)
    )


@pytest.mark.parametrize("instance_path", _instances, ids=_instance_ids)
class TestJsonldExpand:
    """Verify expansion produces valid expanded form."""

    def test_expand_produces_nonempty_result(self, instance_path: Path) -> None:
        result = _run_jsonld_js(_expand_script(instance_path))
        assert result["status"] == "ok", f"Expansion error: {result.get('message')}"
        assert result["count"] > 0

    def test_expand_resolves_type_to_iri(self, instance_path: Path) -> None:
        result = _run_jsonld_js(_expand_script(instance_path))
        assert result["status"] == "ok", f"Expansion error: {result.get('message')}"
        assert result["typesAreIris"], "@type not expanded to IRI"


def _roundtrip_params() -> list[Any]:
    known = load_baseline(KNOWN_ROUNDTRIP_FAILURES)
    return [
        pytest.param(
            path,
            id=sample,
            marks=[pytest.mark.xfail(strict=True, reason="known JSON-LD roundtrip divergence")]
            if sample in known
            else [],
        )
        for path, sample in zip(_instances, _instance_ids, strict=True)
    ]


@pytest.mark.parametrize("instance_path", _roundtrip_params())
class TestJsonldCompactRoundtrip:
    """Verify expand → compact recovers original document."""

    def test_compact_roundtrip(self, instance_path: Path) -> None:
        result = _run_jsonld_js(_roundtrip_script(instance_path))
        if result["status"] == "error":
            pytest.fail(f"JSON-LD processing error: {result['message']}")
        if result["status"] == "fail":
            pytest.fail(f"Compact roundtrip diverged on key(s): {result['diverged']}")

"""Shared helpers for the TD sample tests: baseline lists and the
td11 -> td20 sample derivation."""
from pathlib import Path

TD_VERSIONS = ("td11", "td20")

TD11_CONTEXT_URLS = {
    "https://www.w3.org/2019/wot/td/v1",
    "https://www.w3.org/2022/wot/td/v1.1",
}
TD20_CONTEXT_URL = "https://www.w3.org/ns/wot-next/td"


def load_baseline(path: Path) -> set[str]:
    """Read a known-failure list: one entry per line, '#' comments ignored."""
    if not path.exists():
        return set()
    entries = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            entries.add(line.split()[0])
    return entries


def as_td20(instance):
    """The td20 variant is the same document with the td11 context URL(s)
    replaced by the wot-next one."""
    if not isinstance(instance, dict):
        return instance
    ctx = instance.get("@context")
    if isinstance(ctx, str):
        new_ctx = TD20_CONTEXT_URL if ctx in TD11_CONTEXT_URLS else ctx
    elif isinstance(ctx, list):
        new_ctx = []
        for entry in ctx:
            if isinstance(entry, str) and entry in TD11_CONTEXT_URLS:
                entry = TD20_CONTEXT_URL
            if entry not in new_ctx:  # both td11 URLs map to the same td20 URL
                new_ctx.append(entry)
    else:
        return instance
    out = dict(instance)
    out["@context"] = new_ctx
    return out

from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import re, yaml

@lru_cache(maxsize=1)
def load_bibliography(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {k.upper(): v for k, v in (data.get("bibliography") or {}).items()}

def link_biblio_keys(html: str, biblio: dict[str, dict[str, str]]) -> str:
    def sub(m: re.Match) -> str:
        key = m.group(1)
        ref = biblio.get(key.upper())
        if not ref:
            return f"[[{key}]]"
        href = ref.get("href", "")
        title = ref.get("title", key)
        return f'<a href="{href}" title="{title}">[{key}]</a>'
    return re.sub(r"\[\[([^\]]+)\]\]", sub, html)

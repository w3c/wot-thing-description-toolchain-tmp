from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re, yaml
from typing import Iterable, Tuple, Pattern


@dataclass(frozen=True)
class GlossaryTerm:
    name: str
    id: str
    aliases: list[str]

@lru_cache(maxsize=1)
def load_glossary(path: Path) -> tuple[list[GlossaryTerm], list[Tuple[Pattern[str], str]], dict[str, str]]:
    if not path.exists():
        return [], [], {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    terms: list[GlossaryTerm] = []
    phrase_to_id: dict[str, str] = {}
    for canonical, payload in (data.get("terms") or {}).items():
        gid = payload.get("id")
        aliases = payload.get("aliases", []) or []
        terms.append(GlossaryTerm(canonical, gid, aliases))
        for p in [canonical, *aliases]:
            phrase_to_id[p.lower()] = gid

    # xref, single big alternation, longest-first
    alternation = "|".join(re.escape(p) for p in sorted(phrase_to_id, key=len, reverse=True))
    pattern = re.compile(rf"(?<![>/])\b(?:{alternation})\b(?![^<]*?>)", re.IGNORECASE) if alternation else None
    patterns = [(pattern, "__all__")] if pattern else []
    return terms, patterns, phrase_to_id

def annotate_html(text: str, phrase_to_id: dict[str, str]) -> str:
    """Longest-first, one-pass linker; skips inside <a>…</a> and <code>…</code>."""
    if not text or "<table" in text or not phrase_to_id:
        return text
    alternation = "|".join(re.escape(p) for p in sorted(phrase_to_id, key=len, reverse=True))
    pat = re.compile(rf"(?<![>/])\b(?:{alternation})\b(?![^<]*?>)", re.IGNORECASE)
    splitter = re.compile(r"(<a\b[^>]*>.*?</a>|<code>.*?</code>)", re.DOTALL | re.IGNORECASE)

    def repl(m: re.Match) -> str:
        t = m.group(0)
        gid = phrase_to_id.get(t.lower())
        return f'<a href="#{gid}">{t}</a>' if gid else t

    parts = splitter.split(text)
    for i in range(0, len(parts), 2):
        parts[i] = pat.sub(repl, parts[i])
    return "".join(parts)

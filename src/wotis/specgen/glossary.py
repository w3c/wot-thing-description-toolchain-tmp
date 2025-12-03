from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re
from typing import Dict, Tuple


@dataclass(frozen=True)
class GlossaryEntry:
    key: str        # canonical key from YAML
    id: str | None  # for internal fragments
    href: str | None  # for external or explicit links
    aliases: list[str]


@lru_cache(maxsize=1)
def load_glossary(path: Path) -> Tuple[Dict[str, GlossaryEntry], Dict[str, str]]:
    """
    Load glossary.yaml and return:
      - entries:  canonical_key -> GlossaryEntry
      - phrase_to_key: lowercase phrase -> canonical_key
    """
    if not path.exists():
        return {}, {}

    import yaml
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    terms = data.get("terms") or {}

    entries: Dict[str, GlossaryEntry] = {}
    phrase_to_key: Dict[str, str] = {}

    for canonical, payload in terms.items():
        entry = GlossaryEntry(
            key=canonical,
            id=payload.get("id"),
            href=payload.get("href"),
            aliases=payload.get("aliases", []) or [],
        )
        entries[canonical] = entry

        for phrase in [canonical] + entry.aliases:
            phrase_to_key[phrase.lower()] = canonical

    return entries, phrase_to_key


def annotate_html(html: str, entries: Dict[str, GlossaryEntry], phrase_to_key: Dict[str, str]) -> str:
    """
    Link phrases found in HTML based on glossary entries.

    - Avoids touching existing <a>...</a> and <code>...</code> blocks.
    - Longest-phrase-first matching via a combined regex.
    - If entry.href is set, uses that.
      Else if entry.id is set, uses '#id'.
    """

    if not html:
        return html

    # Build single alternation of all phrases (longest first)
    phrases_sorted = sorted(phrase_to_key.keys(), key=len, reverse=True)
    if not phrases_sorted:
        return html

    alternation = "|".join(re.escape(p) for p in phrases_sorted)
    token_re = re.compile(
        rf"(?<![>/])\b(?:{alternation})\b(?![^<]*?>)",
        flags=re.IGNORECASE,
    )

    def repl(match: re.Match) -> str:
        text = match.group(0)
        key = phrase_to_key.get(text.lower())
        if not key:
            return text
        entry = entries.get(key)
        if not entry:
            return text

        href = entry.href
        if not href and entry.id:
            href = f"#{entry.id}"
        if not href:
            return text

        return f'<a href="{href}">{text}</a>'

    # Protect existing <a> and <code> blocks
    splitter = re.compile(r"(<a\b[^>]*>.*?</a>|<code>.*?</code>)", flags=re.DOTALL | re.IGNORECASE)
    parts = splitter.split(html)
    for i in range(0, len(parts), 2):  # even indices are outside protected blocks
        parts[i] = token_re.sub(repl, parts[i])

    return "".join(parts)

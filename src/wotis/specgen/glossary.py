from __future__ import annotations

import re
import yaml

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class GlossaryEntry:
    key: str
    id: str | None
    href: str | None
    aliases: list[str]

def _clean_yaml_string(s: Any | None) -> str | None:
    """Strips quotes and whitespace from a string loaded from YAML."""
    if s is None:
        return None
    return str(s).strip().strip('"').strip("'")


@lru_cache(maxsize=1)
def load_glossary(path: Path) -> Tuple[Dict[str, GlossaryEntry], Dict[str, str]]:
    """
    Load glossary.yaml and return:
      - entries:  canonical_key -> GlossaryEntry
      - phrase_to_key: lowercase phrase -> canonical_key
    """
    if not path.exists():
        return {}, {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    terms = data.get("terms") or {}
    entries: Dict[str, GlossaryEntry] = {}
    phrase_to_key: Dict[str, str] = {}

    for canonical, payload in terms.items():
        entry = GlossaryEntry(
            key=canonical,
            id=_clean_yaml_string(payload.get("id")),
            href=_clean_yaml_string(payload.get("href")),
            aliases=payload.get("aliases", []) or [],
        )
        entries[canonical] = entry

        for phrase in [canonical] + entry.aliases:
            cleaned_phrase = _clean_yaml_string(phrase)
            if cleaned_phrase:
                phrase_to_key[cleaned_phrase] = canonical
    return entries, phrase_to_key


def annotate_html(html: str, entries: Dict[str, GlossaryEntry], phrase_to_key: Dict[str, str]) -> str:
    """
    Link phrases found in HTML based on glossary entries.

    - Uses ! to exclude terms (e.g., !Consumer is unlinked).
    - Ensures whole word matching.
    - Avoids touching existing <a>...</a> and <code>...</code> blocks.
    - Matches longest phrase first.
    - If entry.href is set in the glossary, uses that.
      Else if entry.id is set, uses '#id'.
    """
    if not html:
        return html

    sorted_phrases = sorted(phrase_to_key.keys(), key=len, reverse=True)
    if not sorted_phrases:
        return html
    alternation = "|".join(re.escape(p) for p in sorted_phrases)
    token_re = re.compile(
        rf"(?<![>/])(!?)\b({alternation})\b(?![\w-])(?![^<]*?>)",
        flags=re.IGNORECASE  # Assuming matching is case-insensitive
    )

    def repl(match: re.Match) -> str:
        exclusion_char = match.group(1)
        text = match.group(2)
        # Check for exclusion
        if exclusion_char == '!':
            return text

        key = phrase_to_key.get(text)
        entry = entries.get(key)
        if not entry:
            return text

        href_value = entry.href
        is_external = bool(href_value)
        class_names = ""
        data_link_value = ""

        if not href_value and entry.id:
            # Internal DFN Link: use #id
            href_value = f"#{entry.id}"
            class_names = "internalDFN"
            data_link_value = "dfn"
            is_external = False
        elif not href_value:
            return text

        class_attr = f'class="{class_names}"' if class_names else ""
        data_attr = f'data-link-type="{data_link_value}"' if data_link_value else ""
        if is_external:
            return f'<a href="{href_value}" {class_attr} {data_attr}><code translate="no">{text}</code></a>'
        else:
            return f'<a href="{href_value}" {class_attr} {data_attr}>{text}</a>'

     # Protect existing <a> and <code> blocks
    splitter = re.compile(r"(<a\b[^>]*>.*?</a>|<code>.*?</code>)", flags=re.DOTALL | re.IGNORECASE)
    parts = splitter.split(html)

    for i in range(0, len(parts), 2):
        parts[i] = token_re.sub(repl, parts[i])

    return "".join(parts)
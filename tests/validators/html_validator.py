from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from colorama import Fore, Style
from lxml import html


@dataclass
class Issue:
    level: str
    title: str
    details: List[str]


class HTMLValidator:
    """
    Validate ReSpec sections by ID.

    Checks for each section id in target_group_ids:
      - section exists in golden + generated
      - duplicate ids within section subtree
      - broken same-page links within section subtree
      - required ids on assertion rows/spans
      - compare assertion-id sets
    """

    def __init__(
        self,
        golden_path: Path,
        generated_path: Path,
        target_group_ids: Optional[List[str]] = None,
    ):
        self.golden_path = Path(golden_path)
        self.generated_path = Path(generated_path)

        self.target_group_ids = target_group_ids or [
            "sec-core-vocabulary-definition",
            "sec-data-schema-vocabulary-definition",
            "sec-security-vocabulary-definition",
            "sec-hypermedia-vocabulary-definition",
            "sec-default-values",
        ]

        self.issues: List[Issue] = []
        self._golden_raw: str = ""
        self._generated_raw: str = ""

    def validate(self) -> bool:
        print(f"\n{Style.BRIGHT}Validating HTML section group:")
        for sid in self.target_group_ids:
            print(f"  - #{sid}")
        print()

        golden_root = self._parse(self.golden_path, store="golden")
        gen_root = self._parse(self.generated_path, store="generated")

        print(f"{Fore.BLUE}{'-' * 70}")
        print(f"{Style.BRIGHT}{Fore.BLUE}HTML DIFF REPORT (section group)")
        print(f"{Fore.BLUE}{'-' * 70}\n")

        # Collect all defined ids in each document for link validation
        golden_defined_ids = self._collect_defined_ids(golden_root)
        gen_defined_ids = self._collect_defined_ids(gen_root)
        overall_success = True
        for sid in self.target_group_ids:
            g_sec = self._find_by_id(golden_root, sid)
            r_sec = self._find_by_id(gen_root, sid)
            if g_sec is None or r_sec is None:
                overall_success = False
                self._report_missing_section(sid, g_sec is not None, r_sec is not None)
                continue

            # Integrity checks
            self._validate_section_integrity(
                label="Golden",
                section_id=sid,
                root=golden_root,
                section=g_sec,
                defined_ids=golden_defined_ids,
                source_path=self.golden_path,
            )
            self._validate_section_integrity(
                label="Generated",
                section_id=sid,
                root=gen_root,
                section=r_sec,
                defined_ids=gen_defined_ids,
                source_path=self.generated_path,
            )

            # compare IDs of assertions
            self._compare_assertion_id_sets(section_id=sid, golden_section=g_sec, gen_section=r_sec)

        self._print_report()
        return overall_success and not any(i.level == "ERROR" for i in self.issues)


    def _parse(self, path: Path, store: str):
        raw = path.read_text(encoding="utf-8", errors="replace")
        if store == "golden":
            self._golden_raw = raw
        else:
            self._generated_raw = raw
        return html.fromstring(raw)

    def _find_by_id(self, root, element_id: str):
        nodes = root.cssselect(f"#{element_id}")
        return nodes[0] if nodes else None

    def _collect_defined_ids(self, root) -> Set[str]:
        return {el.get("id") for el in root.cssselect("[id]") if el.get("id")}

    # ----------------------------
    # Reporting helpers
    # ----------------------------

    def _add(self, level: str, title: str, *details: str):
        self.issues.append(Issue(level=level, title=title, details=list(details)))

    def _print_report(self):
        errors = sum(1 for i in self.issues if i.level == "ERROR")
        warns = sum(1 for i in self.issues if i.level == "WARN")
        infos = sum(1 for i in self.issues if i.level == "INFO")

        print(f"Summary: {errors} error(s), {warns} warning(s), {infos} info\n")

        for issue in self.issues:
            color = Fore.RED if issue.level == "ERROR" else (Fore.YELLOW if issue.level == "WARN" else Fore.CYAN)
            print(f"{color}[{issue.level}] {issue.title}")
            for d in issue.details:
                print(f"  - {d}")
            print()

        print(f"{Fore.BLUE}{'-' * 70}\n")

    def _report_missing_section(self, sid: str, golden_has: bool, generated_has: bool):
        # Add a hint: show raw occurrences of id="sid" if present in text but missing in DOM
        g_hits = self._raw_find_id_occurrences(self._golden_raw, sid)
        r_hits = self._raw_find_id_occurrences(self._generated_raw, sid)

        self._add(
            "ERROR",
            f"Scope: Required section '#{sid}' missing",
            f"Golden present: {golden_has}",
            *(f"Golden raw hit: {h}" for h in g_hits[:3]),
            f"Generated present: {generated_has}",
            *(f"Generated raw hit: {h}" for h in r_hits[:3]),
            f"Golden path: {self.golden_path}",
            f"Generated path: {self.generated_path}",
        )

    def _raw_find_id_occurrences(self, raw: str, sid: str) -> List[str]:
        needles = [f'id="{sid}"', f"id='{sid}'"]
        hits: List[str] = []
        for i, line in enumerate(raw.splitlines(), start=1):
            if any(n in line for n in needles):
                snippet = line.strip()
                if len(snippet) > 180:
                    snippet = snippet[:179] + "…"
                hits.append(f"line {i}: {snippet}")
                if len(hits) >= 10:
                    break
        return hits

    # ----------------------------
    # Validation checks
    # ----------------------------

    def _validate_section_integrity(
        self,
        label: str,
        section_id: str,
        root,
        section,
        defined_ids: Set[str],
        source_path: Path,
    ):
        # Duplicate ids within subtree
        subtree_ids = [el.get("id") for el in section.cssselect("[id]") if el.get("id")]
        dupes = self._find_duplicates(subtree_ids)
        if dupes:
            self._add(
                "ERROR",
                f"{label} #{section_id}: Duplicate IDs inside section subtree",
                f"Found duplicates: {', '.join(sorted(dupes)[:30])}" + (" ..." if len(dupes) > 30 else ""),
                f"File: {source_path}",
            )

        # Broken same-page links (href="#...")
        broken: Set[str] = set()
        for a in section.cssselect('a[href^="#"]'):
            href = (a.get("href") or "").strip()
            if href in ("#", ""):
                continue
            target = href[1:]
            if target and target not in defined_ids:
                broken.add(target)

        if broken:
            b = sorted(broken)
            self._add(
                "ERROR",
                f"{label} #{section_id}: Broken same-page links inside section subtree",
                f"Missing targets (first 30): {', '.join(b[:30])}" + (" ..." if len(b) > 30 else ""),
                f"File: {source_path}",
            )

        # Assertions should have ids
        self._warn_if_missing_ids(label, section_id, source_path, section, ".rfc2119-assertion", "span.rfc2119-assertion")
        self._warn_if_missing_ids(label, section_id, source_path, section, "tr.rfc2119-table-assertion", "tr.rfc2119-table-assertion")
        self._warn_if_missing_ids(label, section_id, source_path, section, "tr.rfc2119-default-assertion", "tr.rfc2119-default-assertion")

    def _warn_if_missing_ids(
        self,
        label: str,
        section_id: str,
        source_path: Path,
        section,
        css: str,
        human: str,
    ):
        for el in section.cssselect(css):
            if not el.get("id"):
                self._add(
                    "WARN",
                    f"{label} #{section_id}: {human} missing id",
                    f"Snippet: {self._snippet(el)}",
                    f"File: {source_path}",
                )

    def _compare_assertion_id_sets(self, section_id: str, golden_section, gen_section):
        # RFC2119 assertions
        g_rfc = {el.get("id") for el in golden_section.cssselect(".rfc2119-assertion[id]") if el.get("id")}
        r_rfc = {el.get("id") for el in gen_section.cssselect(".rfc2119-assertion[id]") if el.get("id")}

        # Table assertions
        g_tbl = {el.get("id") for el in golden_section.cssselect("tr.rfc2119-table-assertion[id]") if el.get("id")}
        r_tbl = {el.get("id") for el in gen_section.cssselect("tr.rfc2119-table-assertion[id]") if el.get("id")}

        # Default assertions
        g_def = {el.get("id") for el in golden_section.cssselect("tr.rfc2119-default-assertion[id]") if el.get("id")}
        r_def = {el.get("id") for el in gen_section.cssselect("tr.rfc2119-default-assertion[id]") if el.get("id")}

        self._diff_id_sets(section_id, "RFC2119 assertions", g_rfc, r_rfc, error_on_missing=True)
        self._diff_id_sets(section_id, "Table assertions", g_tbl, r_tbl, error_on_missing=True)
        self._diff_id_sets(section_id, "Default assertions", g_def, r_def, error_on_missing=False)  # some docs omit defaults in subsets

    def _diff_id_sets(
        self,
        section_id: str,
        label: str,
        golden_ids: Set[str],
        gen_ids: Set[str],
        error_on_missing: bool,
    ):
        missing = sorted(golden_ids - gen_ids)
        extra = sorted(gen_ids - golden_ids)

        if missing:
            lvl = "ERROR" if error_on_missing else "WARN"
            self._add(
                lvl,
                f"Diff #{section_id}: Missing {label} IDs in Generated (present in Golden)",
                f"Count: {len(missing)}",
                f"First 30: {', '.join(missing[:30])}" + (" ..." if len(missing) > 30 else ""),
            )

        if extra:
            self._add(
                "WARN",
                f"Diff #{section_id}: Extra {label} IDs in Generated (not in Golden)",
                f"Count: {len(extra)}",
                f"First 30: {', '.join(extra[:30])}" + (" ..." if len(extra) > 30 else ""),
            )


    def _find_duplicates(self, items: List[str]) -> Set[str]:
        seen: Set[str] = set()
        dupes: Set[str] = set()
        for x in items:
            if x in seen:
                dupes.add(x)
            else:
                seen.add(x)
        return dupes


    def _snippet(self, el, max_len: int = 140) -> str:
        text = " ".join((el.text_content() or "").split())
        return text[: max_len - 1] + "…" if len(text) > max_len else text
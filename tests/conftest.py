"""Shared test options, the rejection summary and the spec-structure
known-failures baseline."""
import os
from pathlib import Path

import pytest

from .baselines import load_baseline
from .rejections import defined_at

TESTS_DIR = Path(__file__).resolve().parent
SPEC_STRUCTURE_BASELINE = TESTS_DIR / "spec_structure_known_failures.txt"


def pytest_addoption(parser):
    parser.addoption(
        "--update-goldens",
        action="store_true",
        help="Overwrite golden files with the current generated output.",
    )


def pytest_configure(config):
    config.rejections = {}
    config.new_failures = []


@pytest.fixture
def rejections(request):
    """{(td version, schema location): {"count": n, "example": message}}"""
    return request.config.rejections


@pytest.fixture
def new_failures(request):
    """One line per failure that is not covered by the baseline lists."""
    return request.config.new_failures


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    fails = config.new_failures
    if not config.rejections and not fails:
        return
    versions = sorted({v for v, _ in config.rejections})
    # regroup per schema location, with per-version counts and one example message
    locations = {}
    for (version, spath), entry in config.rejections.items():
        loc = locations.setdefault(spath, {"example": entry["example"], "total": 0})
        loc[version] = loc.get(version, 0) + entry["count"]
        loc["total"] += entry["count"]
    ordered = sorted(locations.items(), key=lambda kv: -kv[1]["total"])

    # plain text for the terminal
    if fails:
        terminalreporter.write_line("NEW failures, not in the baseline lists:")
        for rec in fails:
            terminalreporter.write_line("  " + rec)
    if ordered:
        terminalreporter.write_line(f"rejected valid samples by schema location ({' / '.join(versions)}):")
        for spath, loc in ordered:
            nums = " / ".join(str(loc.get(v, 0)).rjust(3) for v in versions)
            src = defined_at(spath)
            terminalreporter.write_line(f"  {spath}: {nums}" + (f"  (defined at {src})" if src else ""))
            terminalreporter.write_line(f"      e.g. {loc['example']}")

    # markdown for the GitHub step summary
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if not step_summary:
        return
    md = ["## Test gates report", ""]
    if fails:
        md.append("### New failures, not in the baseline lists")
        md.append("")
        md += [f"- `{rec}`" for rec in fails]
        md.append("")
    if ordered:
        md.append("### Rejected valid samples, by the schema location that rejected them")
        md.append("")
        md.append("| schema location | " + " | ".join(versions) + " | example error | defined at |")
        md.append("|---|" + "---:|" * len(versions) + "---|---|")
        for spath, loc in ordered:
            nums = " | ".join(str(loc.get(v, 0)) for v in versions)
            example = loc["example"].replace("|", "\\|")
            src = defined_at(spath)
            md.append(f"| `{spath}` | {nums} | `{example}` | " + (f"`{src}` |" if src else "|"))
        md.append("")
    with open(step_summary, "a", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")


def pytest_collection_modifyitems(config, items):
    """xfail the ReSpec/HTML tests listed in the spec-structure baseline.

    A fix makes a listed test XPASS (strict), which fails until its line is
    removed, so the list can only shrink.
    """
    listed = load_baseline(SPEC_STRUCTURE_BASELINE)
    for item in items:
        if item.nodeid in listed:
            item.add_marker(pytest.mark.xfail(strict=True, reason="known spec-content gap"))

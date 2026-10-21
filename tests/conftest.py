"""Provide shared pytest options and test reporting."""
import os
from pathlib import Path

import pytest

from .baselines import load_baseline
from .rejections import defined_at


def pytest_addoption(parser):
    parser.addoption(
        "--update-goldens",
        action="store_true",
        help="Overwrite golden files with the current generated output.",
    )


def pytest_configure(config):
    config.rejections = {}
    config.spec_html_findings = []
    config.new_failures = []


def pytest_collection_modifyitems(config, items):
    baseline = load_baseline(Path(__file__).parent / "known_failures" / "spec_structure.txt")
    if not baseline:
        return
    for item in items:
        if item.nodeid in baseline:
            item.add_marker(pytest.mark.xfail(strict=True, reason="known spec structure gap"))


@pytest.fixture
def rejections(request):
    """{(td version, schema location): {"count": n, "example": message}}"""
    return request.config.rejections


@pytest.fixture
def new_failures(request):
    return request.config.new_failures


@pytest.fixture
def spec_html_findings(request):
    """One line per difference between the generated spec HTML and the golden.

    The four spec HTML tests fail one per section, so pytest prints four
    separate stack traces. Collecting the lines here gives one readable list
    for the whole run instead.
    """
    return request.config.spec_html_findings


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    new_failures = config.new_failures
    if new_failures:
        terminalreporter.write_line("")
        terminalreporter.write_line(f"NEW failures not in any baseline ({len(new_failures)}):")
        for entry in new_failures:
            terminalreporter.write_line(f"  {entry}")
        terminalreporter.write_line("")

    html_findings = config.spec_html_findings
    if not config.rejections and not html_findings:
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
    if ordered:
        terminalreporter.write_line(f"rejected valid samples by schema location ({' / '.join(versions)}):")
        for spath, loc in ordered:
            nums = " / ".join(str(loc.get(v, 0)).rjust(3) for v in versions)
            src = defined_at(spath)
            terminalreporter.write_line(f"  {spath}: {nums}" + (f"  (defined at {src})" if src else ""))
            terminalreporter.write_line(f"      e.g. {loc['example']}")
    if html_findings:
        terminalreporter.write_line(f"spec HTML vs manual golden, {len(html_findings)} difference(s):")
        for line in html_findings:
            terminalreporter.write_line("  " + line)

    # markdown for the GitHub step summary
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if not step_summary:
        return
    md = ["## Test gates report", ""]
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
    if html_findings:
        md.append(f"### Spec HTML vs manual golden, {len(html_findings)} differences")
        md.append("")
        # a code block, the findings are multi line and would break a list
        md.append("```")
        md += html_findings
        md.append("```")
        md.append("")
    with open(step_summary, "a", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")

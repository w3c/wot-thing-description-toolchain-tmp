"""The wheel must declare exactly what the package imports.

A missing declaration only shows up in a clean install; an unused one makes
every consumer download packages the toolchain never loads.
"""

from __future__ import annotations

import ast
import re
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_ROOT = REPO_ROOT / "src" / "wot_toolchain"

# Declared but never imported, with the reason each one is still required.
RUNTIME_ONLY = {
    "bikeshed": "invoked as an executable by the spec generator",
    "cssselect": "required by lxml for HtmlElement.cssselect()",
}


# Import names that differ from the name of the distribution providing them.
DISTRIBUTION_OF = {"yaml": "pyyaml"}


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _declared() -> set[str]:
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    return {_normalize(re.split(r"[<>=!~;\[ ]", spec, maxsplit=1)[0]) for spec in project["dependencies"]}


def _imported_modules() -> set[str]:
    modules: set[str] = set()
    for path in PACKAGE_ROOT.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules.add(node.module.split(".")[0])
    return modules - set(sys.stdlib_module_names) - {"wot_toolchain"}


def _imported_distributions() -> set[str]:
    return {_normalize(DISTRIBUTION_OF.get(module, module)) for module in _imported_modules()}


def test_every_imported_distribution_is_declared() -> None:
    assert _imported_distributions() - _declared() == set()


def test_every_declared_distribution_is_used() -> None:
    assert _declared() - _imported_distributions() - set(RUNTIME_ONLY) == set()

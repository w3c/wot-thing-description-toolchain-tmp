"""The Jinja templates ship inside the package, so an installed wheel can render the specification."""

from __future__ import annotations

import subprocess
import zipfile
from importlib.resources import files
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_NAMES = ("class_section.jinja2", "class_table.jinja2", "snippet_with_default.jinja2", "thing_table.jinja2")


@pytest.mark.parametrize("name", TEMPLATE_NAMES)
def test_template_is_package_data(name: str) -> None:
    assert (files("wot_toolchain") / "templates" / name).is_file()


def test_built_wheel_contains_the_templates(tmp_path: Path) -> None:
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(tmp_path)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    (wheel,) = tmp_path.glob("*.whl")

    with zipfile.ZipFile(wheel) as archive:
        packaged = {name for name in archive.namelist() if name.startswith("wot_toolchain/templates/")}

    assert packaged == {f"wot_toolchain/templates/{name}" for name in TEMPLATE_NAMES}

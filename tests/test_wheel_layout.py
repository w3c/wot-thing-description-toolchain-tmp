"""The built wheel must install an importable ``wot_toolchain`` package and CLI."""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def wheel(tmp_path_factory: pytest.TempPathFactory) -> zipfile.ZipFile:
    out_dir = tmp_path_factory.mktemp("dist")
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(out_dir)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    (wheel_path,) = out_dir.glob("wot_toolchain-*.whl")
    return zipfile.ZipFile(wheel_path)


def test_wheel_top_level_package_is_wot_toolchain(wheel: zipfile.ZipFile) -> None:
    top_level = {name.split("/")[0] for name in wheel.namelist() if not name.split("/")[0].endswith(".dist-info")}
    assert top_level == {"wot_toolchain"}


def test_wheel_console_script_targets_wot_toolchain(wheel: zipfile.ZipFile) -> None:
    (entry_points,) = [name for name in wheel.namelist() if name.endswith("entry_points.txt")]
    assert "wot-toolchain = wot_toolchain.cli:main" in wheel.read(entry_points).decode("utf-8")

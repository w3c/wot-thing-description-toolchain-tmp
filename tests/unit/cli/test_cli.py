"""Exit codes of the wot-toolchain command line interface."""

import shutil
from pathlib import Path

import yaml
from click.testing import CliRunner

from wot_toolchain.cli import main

REPO_CONFIG = Path(__file__).parents[3] / "wot-toolchain.yaml"
REPO = REPO_CONFIG.parent


def _config(tmp_path: Path, *generators: str, **spec) -> Path:
    """Write a copy of the repository config that runs only the named generators into tmp_path."""
    text = REPO_CONFIG.read_text(encoding="utf-8").replace(" resources/", f" {REPO}/resources/")
    data = yaml.safe_load(text.replace(f"{REPO}/resources/gens", str(tmp_path / "gens")))
    data["generators"] = {name: data["generators"][name] for name in generators}
    if spec:
        data["generators"]["spec"] |= spec
    config = tmp_path / "wot-toolchain.yaml"
    config.write_text(yaml.safe_dump(data), encoding="utf-8")
    return config


def test_missing_config_exits_3(tmp_path):
    result = CliRunner().invoke(main, ["generate-wot-resources", "-c", str(tmp_path / "nope.yaml")])
    assert result.exit_code == 3


def test_unknown_config_key_exits_3(tmp_path):
    config = tmp_path / "wot-toolchain.yaml"
    text = REPO_CONFIG.read_text(encoding="utf-8").replace(" resources/", f" {REPO_CONFIG.parent}/resources/")
    config.write_text(text + "bogus: 1\n", encoding="utf-8")
    result = CliRunner().invoke(main, ["generate-wot-resources", "-c", str(config)])
    assert result.exit_code == 3


def test_missing_input_schema_exits_4(tmp_path):
    schema = tmp_path / "nope.yaml"
    result = CliRunner().invoke(main, ["generate-wot-resources", "-c", str(REPO_CONFIG), "-i", str(schema)])
    assert result.exit_code == 4


def test_removed_generate_docs_option_exits_2():
    result = CliRunner().invoke(main, ["generate-wot-resources", "-d"])
    assert result.exit_code == 2
    assert "No such option '-d'" in result.output


def test_invalid_snippet_exits_5(tmp_path, caplog):
    snippets = tmp_path / "snippets"
    shutil.copytree(REPO / "resources" / "snippets", snippets)
    (snippets / "action-serialization.json").write_text("{}", encoding="utf-8")
    config = _config(tmp_path, "spec", snippets=str(snippets))
    result = CliRunner().invoke(main, ["generate-wot-resources", "-c", str(config)])
    assert result.exit_code == 5
    assert "action-serialization.json" in caplog.text


def test_prose_file_of_unknown_class_exits_5(tmp_path, caplog):
    prose = tmp_path / "sections"
    shutil.copytree(REPO / "resources" / "spec" / "sections", prose)
    (prose / "NoSuchClass.html").write_text("<p>Orphan.</p>\n", encoding="utf-8")
    config = _config(tmp_path, "spec", prose=str(prose))
    result = CliRunner().invoke(main, ["generate-wot-resources", "-c", str(config)])
    assert result.exit_code == 5
    assert "NoSuchClass.html" in caplog.text


def test_unwritable_assertions_csv_exits_5(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("", encoding="utf-8")
    config = _config(tmp_path, "spec", assertions_csv=str(blocker / "assertions.csv"))
    result = CliRunner().invoke(main, ["generate-wot-resources", "-c", str(config)])
    assert result.exit_code == 5


def test_missing_graphviz_exits_5(tmp_path, monkeypatch, caplog):
    monkeypatch.setenv("PATH", str(tmp_path))
    result = CliRunner().invoke(main, ["generate-wot-resources", "-c", str(_config(tmp_path, "visualization"))])
    assert result.exit_code == 5
    assert "dot" in caplog.text


def test_invalid_snippet_metadata_exits_5(tmp_path, caplog):
    snippets = tmp_path / "snippets"
    shutil.copytree(REPO / "resources" / "snippets", snippets)
    metadata = yaml.safe_load((snippets / "_snippets.yaml").read_text(encoding="utf-8"))
    metadata["snippets"]["action-serialization"]["layout"] = "sidebar"
    (snippets / "_snippets.yaml").write_text(yaml.safe_dump(metadata), encoding="utf-8")
    config = _config(tmp_path, "spec", snippets=str(snippets))
    result = CliRunner().invoke(main, ["generate-wot-resources", "-c", str(config)])
    assert result.exit_code == 5
    assert "_snippets.yaml" in caplog.text
    assert "sidebar" in caplog.text

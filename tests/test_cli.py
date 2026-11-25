"""Exit codes of the wot-toolchain command line interface."""

from pathlib import Path

from click.testing import CliRunner

from wot_toolchain.cli import main

REPO_CONFIG = Path(__file__).parents[1] / "wot-toolchain.yaml"


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

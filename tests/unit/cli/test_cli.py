"""Exit codes of the wot-toolchain command line interface and of the snippet validation script."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from click.testing import CliRunner
import rdflib

from wot_toolchain.cli import main

REPO_CONFIG = Path(__file__).parents[3] / "wot-toolchain.yaml"
REPO = REPO_CONFIG.parent
VALIDATE_SNIPPETS = REPO / "scripts" / "validate_snippets.py"


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


def _validate_snippets(tmp_path: Path, snippets: Path) -> subprocess.CompletedProcess[str]:
    """Generate the JSON Schema into tmp_path and run the snippet validation script against it."""
    config = _config(tmp_path, "jsonschema")
    assert CliRunner().invoke(main, ["generate-wot-resources", "-c", str(config)]).exit_code == 0
    command = [sys.executable, str(VALIDATE_SNIPPETS), "--snippets", str(snippets)]
    command += ["--td-schema", str(tmp_path / "gens" / "jsonschema" / "jsonschema.json")]
    return subprocess.run(command, capture_output=True, text=True, check=False)


def test_snippet_script_accepts_repository_snippets(tmp_path):
    result = _validate_snippets(tmp_path, REPO / "resources" / "snippets")
    assert result.returncode == 0, result.stderr


def test_snippet_script_rejects_td_snippet_that_generated_json_schema_rejects(tmp_path):
    snippets = tmp_path / "snippets"
    shutil.copytree(REPO / "resources" / "snippets", snippets)
    snippet = json.loads((snippets / "action-serialization.json").read_text(encoding="utf-8"))
    snippet["@type"] = []  # The upstream TD schema accepts an empty @type; the generated JSON Schema rejects it.
    (snippets / "action-serialization.json").write_text(json.dumps(snippet), encoding="utf-8")
    result = _validate_snippets(tmp_path, snippets)
    assert result.returncode == 1
    assert "action-serialization.json: @type" in result.stderr


def test_snippet_script_rejects_invalid_thing_model_snippet(tmp_path):
    snippets = tmp_path / "snippets"
    shutil.copytree(REPO / "resources" / "snippets", snippets)
    snippet = json.loads((snippets / "basic-on-off-tm.json").read_text(encoding="utf-8"))
    snippet["title"] = None
    (snippets / "basic-on-off-tm.json").write_text(json.dumps(snippet), encoding="utf-8")
    result = _validate_snippets(tmp_path, snippets)
    assert result.returncode == 1
    assert "basic-on-off-tm.json: title" in result.stderr


def test_snippet_script_without_json_schema_exits_2(tmp_path):
    command = [sys.executable, str(VALIDATE_SNIPPETS), "--td-schema", str(tmp_path / "nope.json")]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 2
    assert "nope.json" in result.stderr


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


_RANGE_CONFLICT_SCHEMA = """\
id: https://example.org/probe
name: probe
prefixes:
  linkml: https://w3id.org/linkml/
  pb: https://example.org/probe#
default_prefix: pb
default_range: string
imports:
  - linkml:types
classes:
  Endpoint:
    class_uri: pb:Endpoint
    attributes:
      local:
        slot_uri: pb:local
        range: integer
  Other:
    class_uri: pb:Other
    attributes:
      local:
        slot_uri: pb:local
        range: {other_range}
"""


def _one_ontology_config(tmp_path: Path, other_range: str) -> Path:
    """Write a schema whose two classes define pb:local, and a config that generates only its ontology."""
    (tmp_path / "probe.yaml").write_text(_RANGE_CONFLICT_SCHEMA.format(other_range=other_range), encoding="utf-8")
    vocabulary = {"schema": "probe.yaml", "prefix": "pb", "ontology": "probe.ttl"}
    data = {"root_schema": "probe.yaml", "output_dir": "out", "vocabularies": [vocabulary]}
    data["generators"] = {"owl": yaml.safe_load(REPO_CONFIG.read_text(encoding="utf-8"))["generators"]["owl"]}
    config = tmp_path / "wot-toolchain.yaml"
    config.write_text(yaml.safe_dump(data), encoding="utf-8")
    return config


def test_one_property_with_two_ranges_exits_4(tmp_path, caplog):
    result = CliRunner().invoke(main, ["generate-wot-resources", "-c", str(_one_ontology_config(tmp_path, "string"))])
    assert result.exit_code == 4
    expected = "has range 'integer' in class 'Endpoint' and 'string' in class 'Other'; one property has one range."
    assert f"property <https://example.org/probe#local> {expected}" in caplog.text


def test_one_property_with_one_range_in_two_classes_is_generated(tmp_path):
    result = CliRunner().invoke(main, ["generate-wot-resources", "-c", str(_one_ontology_config(tmp_path, "integer"))])
    assert result.exit_code == 0
    ontology = rdflib.Graph().parse(tmp_path / "out" / "owl" / "probe.ttl")
    assert list(ontology.objects(rdflib.URIRef("https://example.org/probe#local"), rdflib.RDFS.range)) == [
        rdflib.XSD.integer
    ]

"""The OWL artifact package serializes and preprocesses without the legacy wrapper modules."""

import subprocess
import sys

_PROBE = """
import sys
from rdflib import Graph
from wot_toolchain.artifacts.owl.postprocess import postprocess_owl, postprocess_owl_graph
from wot_toolchain.artifacts.owl.preprocess import preprocess_for_gen_owl
legacy = sorted(name for name in sys.modules if name.endswith(("owl_postprocessor", "owl_preprocessor")))
assert not legacy, legacy
assert Graph().serialize(format="wot-turtle") is not None
"""


def test_wot_turtle_is_registered_by_the_owl_artifact_package_alone() -> None:
    result = subprocess.run([sys.executable, "-c", _PROBE], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr

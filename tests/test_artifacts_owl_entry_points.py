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


def test_legacy_modules_re_export_the_owl_artifact_functions() -> None:
    from wot_toolchain.artifacts.owl import postprocess, pre_passes, preprocess
    from wot_toolchain.postprocessors import owl_postprocessor
    from wot_toolchain.preprocessors import owl_preprocessor

    assert owl_postprocessor.postprocess_owl is postprocess.postprocess_owl
    assert owl_postprocessor.postprocess_owl_graph is postprocess.postprocess_owl_graph
    assert owl_preprocessor.preprocess_for_gen_owl is preprocess.preprocess_for_gen_owl
    assert owl_preprocessor._attr_slot_name is pre_passes._attr_slot_name
    assert owl_preprocessor._strip_non_ontological_enums is pre_passes._strip_non_ontological_enums

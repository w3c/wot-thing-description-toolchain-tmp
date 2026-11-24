"""Generate the config file reference page from the LinkML schema of the config file.

Usage:
    uv run --group docs python scripts/gen_config_docs.py

Input:  src/wot_toolchain/schemas/config.yaml
Output: docs/reference/config-file.md (not tracked; run before building the docs site)
"""

import re
import tempfile
from pathlib import Path

from linkml.generators.docgen import DocGenerator

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_SCHEMA = REPO_ROOT / "src" / "wot_toolchain" / "schemas" / "config.yaml"
TEMPLATE_DIRECTORY = REPO_ROOT / "scripts" / "templates" / "config-docs"
OUTPUT = REPO_ROOT / "docs" / "reference" / "config-file.md"


def main() -> None:
    """Render the index template of gen-doc into a single reference page."""
    generator = DocGenerator(str(CONFIG_SCHEMA), template_directory=str(TEMPLATE_DIRECTORY), mergeimports=False)
    with tempfile.TemporaryDirectory() as directory:
        generator.serialize(directory=directory)
        page = (Path(directory) / "index.md").read_text(encoding="utf-8")
    OUTPUT.write_text(re.sub(r"\n{3,}", "\n\n", page).strip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

<div align="center">

<img src="images/wot-logo.png" alt="Web of Things" width="200">

# WoT Toolchain

**LinkML-based generation of Web of Things artifacts.**

[![CI](https://github.com/w3c/wot-thing-description-toolchain-tmp/actions/workflows/main.yaml/badge.svg?branch=main)](https://github.com/w3c/wot-thing-description-toolchain-tmp/actions/workflows/main.yaml)
[![W3C WoT TD](https://img.shields.io/badge/W3C-WoT%20Thing%20Description-005A9C?logo=w3c&logoColor=white)](https://www.w3.org/WoT/)
[![Python 3.14](https://img.shields.io/badge/python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![LinkML](https://img.shields.io/badge/schema--driven-LinkML-2D6A4F?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAAAXNSR0IArs4c6QAAAERlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAA6ABAAMAAAABAAEAAKACAAQAAAABAAAAFKADAAQAAAABAAAAFAAAAACy3fD9AAAD7UlEQVQ4EX1UYWwURRSeNzu3t3ctJwrt9VQiILGRSAzaaIJ/1CjVPyaKPWNMRf9pQqjJebXSFrbXohwHxDSEhEaDEotaAqap8QcxqVEjRn8QNQ0m0kCVQu9soRze3e7tzjxnNt3L2lbfj31v3/veN2/mzRsg/yHx/tw6XddbK9Vqr8V5FAhCWGNFg7GMAHrmSlfHH8ulwmLn3blc440ydiKFBCH0O0r5WXSwQCIS6UITImwBAltQiCmDuQemd+2aC3L8izAxkG2xOTGpBsM73PJnpmmKINi3HzVNNsHqXxKCP68J2l0w07/4sRphfG/uPscV+8OUpK72vnXeB/yfbtx38H7Xdt+NRoyOy50dvyssVZ/bTTPqctGnAetWZA2Zg5sfPHo0qmLLyYbBwYbm9440F7pSPzOg/ZZlDUhfWGE9wqpW106A/PjX7tQ55ay41W0XZ+YPI5HeRXLnoUORuXnr+PVS5WEVKuxOnyVAzxeLlaT6p7KSEBH4GDNix5TDE0TLCRuvrurP9vgupdUCUCVbXYSHLGp878d0oB9wAU+1jYxodDpfuocAXs+nXy/4AJmGxHWJQ2hmdSb7mk+W6M/1cTBue2Dl/NtjLZ+rvntypSf1pzSsbyan72ICRDNFuLgQW1CCEtfhOmMf2QiHGwdy+dVcbHRdnnpi1Y1N2+LjR6ZuRmXB5Fc/T57NFLrOBkaBrBBIi37A1xKgxQwjM18uz1oCT0u/cCDS/krTcLysG63y52Mfq7QQWASKKykSYckqa+XXQADEcaqha73pLk2IEzpAX8XsOHENI4ZMrsF8AxgYCLTM5EjJ7YLXMT8op8zLEFRecXmeJmL7HqlVyzmXKiQNAU4NLw2ZsZaF2BjFMJ0QiHfEc7m6IEA2Rm5aUxzEBBDS8BahmhxA9YPW9uOntzZ6OeaELvvADas4SfPpdIlSmMAKeTZASIkcViRQCfg8M8rjP9kWeUfT8WnBy+OfjD75zPub0onCmpbUJdO0vItdr5MhTvAFWaW3otwoYwT2Xn1zx5IXJZk8Wdne9m23a2svyias4VgZDWHxh5FbB9arFT3CS52dM/KEhhwLB5uz2RX1Gh1O4LoBGV96+l6dhLzc9vWngpNTug4kEqFNtgv31giVMbsnPcYQvpi1yYfq7CbMZHUhd1m11jxmhI36A7ZNviyXxFAsFD2jgN6hBzMaM/sfkdt/Q87npKaxUQPCv623CzcV5kIsFhNVbWOVO89pKAr5ns59wVxlLyFUTjXfl+f+bpWP6ePyzWvgCxdPk90jFPJA6Ve31LHxCzt32goflGUJgwA18OdmZrwrtbmpqXQymeTB+GL7H5S4pwvLuAY7AAAAAElFTkSuQmCC&logoColor=white)](https://linkml.io/)
[![License: W3C](https://img.shields.io/badge/license-W3C%20Software%20and%20Document-0B7A75)](LICENSE.md)

</div>

The WoT Toolchain is a work area for moving Web of Things (WoT) resource generation to LinkML schema modules. It is intended to replace the manual maintenance of WoT resources — SHACL shapes, JSON Schema, JSON-LD context files, OWL ontologies — and the `index.html` specification generation currently handled by the [existing toolchain](https://github.com/w3c/wot-thing-description/tree/main/toolchain) in the [W3C WoT Thing Description repository](https://github.com/w3c/wot-thing-description).

The toolchain models WoT resources in LinkML and generates the related artifacts from the same schema modules. Its aim is to prevent drift between those resources and the generated HTML sections of the [WoT Thing Description specification](https://www.w3.org/TR/wot-thing-description/).

> [!IMPORTANT]
> This work area is in progress. The toolchain is intended to be integrated into the official [TD](https://github.com/w3c/wot-thing-description/) repository after review and Working Group consensus.

## Usage

Requirements:

- Python 3.14, as declared in `pyproject.toml`;
- [uv](https://docs.astral.sh/uv/); and
- [Graphviz](https://graphviz.org/), required by `generate-wot-resources` to generate class-hierarchy diagrams for the index.html.

```bash
git clone https://github.com/w3c/wot-thing-description-toolchain-tmp.git
cd wot-thing-description-toolchain-tmp
uv sync --locked
uv run wot-toolchain generate-wot-resources
uv run pytest tests/ -v
```

`wot-toolchain` is the Python command-line interface installed from this checkout by `uv sync`. `generate-wot-resources` runs every generator listed under `generators` in the config file; the `spec` generator builds the ReSpec TD specification and its assertion CSV inventory. `--only GENERATOR` runs a subset of the config file's generators and `--output-dir DIR` redirects the resource artifacts. Run `uv run wot-toolchain generate-wot-resources --help` for all options.

`wot-toolchain diff-report GENERATED REFERENCE` prints a Markdown report of the JSON paths added, removed or changed in a generated JSON Schema or JSON-LD context relative to a reference file; it exits 0 whether or not they differ, so its output can be appended to `$GITHUB_STEP_SUMMARY`.

What is generated, from which schemas and into which files is described by the project config file [`wot-toolchain.yaml`](wot-toolchain.yaml); select another config file with `-c`.

### Use from another repository

The toolchain contains no schemas of its own. A repository that owns LinkML schemas and a config file installs a tagged release and runs it against that config file:

```bash
uv tool install git+https://github.com/w3c/wot-thing-description-toolchain-tmp@<tag>
wot-toolchain generate-wot-resources -c path/to/wot-toolchain.yaml
```

The toolchain is not published on PyPI. Bikeshed, used by the `spec` generator, is installed with the toolchain. The visualization generator needs Graphviz `dot` on `PATH`.

Generated files are written under `resources/gens/`. Do not edit them directly.

## How It Works

The source models are maintained manually by the WoT Working Group:

- **WoT LinkML schema modules** — the root module [`td-linkml`](resources/schemas/thing_description.yaml) imports [`hctl-linkml`](resources/schemas/hypermedia.yaml), [`wotsec-linkml`](resources/schemas/wot_security.yaml), and [`jsonschema-linkml`](resources/schemas/jsonschema.yaml)
- **Static ReSpec template and Jinja templates** — `resources/index.template.html` and `src/wot_toolchain/templates/`
- **TD/TM JSON snippets** — example snippets with `_snippets.yaml` metadata

From these source models, the generation pipeline has two paths:

1. **LinkML resource generation + postprocessors** takes the schema modules and produces the following WoT resource artifacts under `resources/gens/`:
   - **JSON Schema** (`jsonschema/jsonschema.json`) — validation of TD and TM JSON representations
   - **JSON-LD context** (`jsonldcontext/context.jsonld` and one context per schema module) — TD JSON-LD terms, types, and containers
   - **SHACL shapes** (`shacl/shapes.shacl.ttl`, experimental) — validation of RDF representations of TD and TM instances
   - **OWL ontologies** (`owl/td.ttl`, `owl/tm.ttl`, `owl/hctl.ttl`, `owl/wotsec.ttl`, `owl/jsonschema.ttl`, experimental) — WoT vocabulary terms and relationships
   - **Visualizations** (`visualization/*.svg`, experimental) — class-hierarchy diagrams

2. **Snippet rendering + ReSpec specification generation**, enabled by `-d`, takes the schema modules, `resources/index.template.html`, Jinja templates, and the TD/TM JSON snippets. It produces:
   - **Generated ReSpec `index.html`** — vocabulary tables, assertions, and rendered TD/TM example snippets
   - **Assertion CSV inventory** (`assertions/`) — inventory of assertions in the TD specification

![WoT Toolchain generation flow](images/wot-toolchain.svg)

Postprocessors are custom Python functions in [`src/wot_toolchain/postprocessors/`](src/wot_toolchain/postprocessors/). They modify a raw LinkML generator output only where the generator cannot represent a TD requirement directly or needs a documented adjustment to produce the required TD representation. [`Known LinkML Gaps`](docs/known-linkml-gaps.md) records each known limitation and workaround.

## Testing

Run the complete checks after generating artifacts:

```bash
uv run pytest tests/ -v
```

The checks include:

- `tests/test_td_instance_gate.py`: validates the valid and invalid TD test instances in `tests/data/`, as TD 1.1 and as td-next, against the generated JSON Schema.
- `tests/test_td_crosscheck.py`: compares generated-schema validation verdicts with the upstream W3C TD schemas manually specified in `resources/upstream/schemas/`.
- `tests/test_golden_diff.py`: compares generated JSON Schema, JSON-LD context, OWL modules, SHACL shapes, and generated specification sections with machine-updatable snapshots in `tests/snapshots/`.
- `tests/test_golden_form_structure.py` and `tests/test_spec_content_rendering.py`: check generated ReSpec structure and rendering behavior.
- `tests/test_snippet_schema.py` and `tests/test_snippet_crossrefs.py`: validate snippet metadata, source files, and ReSpec cross-references.
- `tests/test_jsonld_roundtrip.py`: round-trips the valid TD test instances through `jsonld.js`; requires Node.js with the `jsonld` package in `node_modules/`.

`resources/upstream/html/index.html` and `resources/upstream/assertions.csv` are upstream reference files used for TD specification and assertion-inventory comparison. `tests/snapshots/` contains this toolchain's generated-output snapshots; update them only with `uv run pytest tests/test_golden_diff.py --update-goldens` after reviewing an intended change.

Known failures are listed one per line in `tests/known_failures/` and marked as strict expected failures: a listed case that starts passing fails the suite until its entry is removed. Any other rejection of a valid sample or mismatch with the W3C reference schema fails the relevant test directly.

See [tests/README.md](tests/README.md) for the complete test inventory and the upstream reference files used by each check.

## Development

Useful commands:

```bash
# Generate resource artifacts only
uv run wot-toolchain generate-wot-resources

# Generate resource artifacts and the ReSpec TD specification
uv run wot-toolchain generate-wot-resources

# Run the complete test suite
uv run pytest tests/ -v

# Check linting
uv run ruff check .
```

Before changing a schema or generator, read the [modeling guidelines](docs/guidelines/index.md) for naming conventions, custom annotations, postprocessor patterns, and snippet authoring. For documented LinkML limitations and workarounds, see [`Known LinkML Gaps`](docs/known-linkml-gaps.md). Files under `resources/gens/` are generated outputs and should not be edited manually. Each postprocessor should document the LinkML limitation it addresses.

## Current Status

Current work focuses on JSON Schema parity, generated TD specification vocabulary tables, snippet validation, and assertion inventory comparison with the upstream TD repository. The JSON Schema, the JSON-LD context, and the specification HTML with its assertion inventory are the release targets. The OWL, SHACL, and visualization outputs are experimental: they are generated and covered by snapshot and structural tests, but deeper automated consistency checks for them are not currently part of the CI test gates.

## Contributing

Contributions, issue reports, and review are welcome. Keep each change focused, generate the affected artifacts, and run the relevant checks before opening a pull request. For schema and generated-output changes, describe the compatibility impact in the pull request.

## License

Licensed under the [W3C Software and Document License](http://www.w3.org/Consortium/Legal/copyright-software), the same license as
[w3c/wot-thing-description](https://github.com/w3c/wot-thing-description). See [LICENSE.md](LICENSE.md).

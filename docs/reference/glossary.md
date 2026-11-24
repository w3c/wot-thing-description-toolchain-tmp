# Glossary

Words these pages use with a meaning of their own.

**td-next**
: The next version of the Thing Description, which the schemas in this repository target. Each schema carries `version: "td-next"`, which the generated ontology headers repeat as `owl:versionInfo`.

**Upstream**
: Two meanings, told apart by context. Upstream *LinkML* is the LinkML generators this toolchain builds on, as in "upstream bug". The upstream *artifacts* are the files published with TD 1.1 and kept in `resources/upstream/`.

**Published artifact**
: A file published with TD 1.1: the JSON Schema, JSON-LD context, ontologies and SHACL shapes in `resources/upstream/`. The [differences pages](../status/differences/index.md) compare the generated artifacts with them.

**Snapshot** (also **golden**)
: A committed copy of the toolchain's current output in `tests/snapshots/`. `tests/test_golden_diff.py` fails when the output changes. A snapshot records what this toolchain produces, not what is correct; see [Testing](../internals/testing.md).

**Config file**
: The YAML file of a project, by default `wot-toolchain.yaml`, that names its schemas, generators and output paths. See [Config file](config-file.md).

**Config schema**
: `src/wot_toolchain/schemas/config.yaml`, the LinkML schema of the config file format. The toolchain validates every config file against it, and the config file reference is generated from it. It is not one of the vocabulary schemas in `resources/schemas/`.

**Pass**
: One named transformation applied to a generated artifact, with a `PassKind` and a written reason. See [Postprocessors](../internals/postprocessors.md).

**Workaround**
: Status of a [LinkML gaps](../status/linkml-gaps.md) entry: upstream LinkML does not produce what the TD needs, and the toolchain compensates.

**Shaping**
: Status of a LinkML gaps entry: the toolchain reshapes valid upstream output so that it has the shape of the published artifact.

**Undecided**
: Status of a LinkML gaps or differences entry: the generated artifact differs from the published one, and no decision has been taken.

**Published defect**
: Status of a differences entry: the published artifact is wrong against the TD 1.1 Recommendation or inconsistent with a companion artifact, and the generated artifact does not reproduce it.

**Canary**
: A test in `tests/test_upstream_canaries.py` that pins a behaviour of upstream LinkML. It fails once LinkML changes that behaviour, which is the signal to remove the matching workaround.

**Known failure**
: A test case listed in `tests/known_failures/` and marked `xfail(strict=True)`; the only failures the suite accepts.

**Snippet**
: A TD or TM example in `resources/snippets/`, registered in `_snippets.yaml` and rendered into the specification. See [Snippets](../authoring/snippets.md).

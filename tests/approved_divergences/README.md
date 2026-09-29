# Approved Divergences

These files record explicit, reviewed differences between generated artifacts
and their upstream W3C reference material. They are not a general allowlist.

Every entry MUST identify the upstream location, explain why the generated
value is preferable, and state the exact generated value expected by the test.
The associated comparison test MUST fail when the generated value changes or
when upstream is corrected and the entry becomes stale.

Use `html.yaml` for corrections to upstream generated HTML, including
assertion wording. Use `snippets.yaml` only when a complete generated TD or TM
must differ from an illustrative upstream inline example.

Do not add an entry for a semantic change to a normative requirement without
Working Group agreement. Remove an entry when upstream aligns or when the
toolchain should again reproduce the upstream value.

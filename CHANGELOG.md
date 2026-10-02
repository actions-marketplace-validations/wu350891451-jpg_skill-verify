# Changelog

## 0.1.1 - 2026-10-02

- Fixed a path-escape false negative: `SV012` now checks containment for every
  candidate reference instead of only absolute targets and literal `../`
  prefixes. A target such as `scripts/../../outside.md` is reported again.
- Added regression tests for that shape and for `--allow-missing` not waiving
  an escape.
- Replaced the `xargs`-based input trim in `action.yml` with pure shell
  parameter expansion, so inputs containing quotes or backslashes no longer
  fail with `unmatched quote`.
- Corrected the Pages rule-range wording to match the published rule ids and
  documented pinning the action to a commit SHA for production use.

## 0.1.0 - 2026-10-02

Initial release.

- Dependency-free Python 3.8+ CLI.
- Agent Skills frontmatter validation.
- Local reference resolution for Markdown links, HTML attributes, and inline
  code paths.
- Path-escape detection and explicit `--allow-missing` patterns for generated
  runtime files.
- High-signal instruction-risk rules for prompt injection, credential
  disclosure, remote shell execution, destructive deletion, hidden Unicode,
  and instruction-like HTML comments.
- Text, JSON, and SARIF output.
- GitHub composite Action with result and count outputs.
- Positive and negative CI fixtures.

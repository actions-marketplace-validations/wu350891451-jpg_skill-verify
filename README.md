# Skill Verify

[![CI](https://github.com/wu350891451-jpg/skill-verify/actions/workflows/ci.yml/badge.svg)](https://github.com/wu350891451-jpg/skill-verify/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Fail CI when an Agent Skill has broken local references, path escapes, hidden
Unicode, or high-signal prompt-injection text.

`SKILL.md` files are executable supply-chain inputs for coding agents. They
often reference scripts and assets, but the reference can be stale, and the
text can contain instructions no reviewer intended. `skill-verify` turns the
mechanically checkable part into a stable exit code.

It is deliberately smaller than a general Markdown linter:

1. It resolves the local files a skill claims to ship.
2. It fails closed on malformed frontmatter and broken paths.
3. It reports a narrow, documented set of instruction-risk patterns with line
   numbers and machine-readable output.

## 30-second demo

```bash
git clone https://github.com/wu350891451-jpg/skill-verify.git
cd skill-verify

python3 scripts/skill_verify.py demo/good-skill
# Scanned 1 skill(s): 1 passed, 0 failed

python3 scripts/skill_verify.py demo/broken-skill
# ERROR SV010 line 8: referenced local path does not exist
# exit code 1
```

No dependencies. Python 3.8 or newer.

## GitHub Action

```yaml
name: Verify skills

on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: wu350891451-jpg/skill-verify@v0.1.0
        with:
          path: skills
          recursive: "true"
```

The action writes `result`, `errors`, `warnings`, `failed-skills`, and
`scanned-skills` outputs. For a monorepo, use `path: .` and
`recursive: "true"`.

For GitHub code scanning, request SARIF:

```yaml
      - uses: wu350891451-jpg/skill-verify@v0.1.0
        with:
          path: skills
          recursive: "true"
          format: sarif
          output: skill-verify.sarif
```

Then upload `skill-verify.sarif` with `github/codeql-action/upload-sarif`.

## Command line

```bash
# One skill directory
python3 scripts/skill_verify.py path/to/skill

# Every nested SKILL.md
python3 scripts/skill_verify.py skills/ --recursive

# JSON for automation
python3 scripts/skill_verify.py skills/ --recursive --format json

# Fail on warnings too
python3 scripts/skill_verify.py skills/ --recursive --fail-on warning

# Suppress a reviewed rule
python3 scripts/skill_verify.py path/to/skill --exclude-rule SV025

# Mark a generated runtime file as intentionally absent
python3 scripts/skill_verify.py path/to/skill --allow-missing full_text.txt
```

| Exit code | Meaning |
|---:|---|
| `0` | No finding reached `--fail-on` |
| `1` | A finding reached `--fail-on` |
| `2` | Usage, missing path, or no `SKILL.md` found |

## Rules

The full catalog is in [references/rules.md](references/rules.md). The core
checks are:

- required frontmatter, valid kebab-case `name`, matching directory name;
- every referenced `scripts/`, `assets/`, `references/`, Markdown link, and
  known local file must exist;
- generated files can be declared with `--allow-missing`; path escapes cannot;
- references may not escape the skill directory;
- common instruction-override, credential-disclosure, credential-exfiltration,
  remote shell, destructive deletion, hidden-user, invisible Unicode, and
  hidden-comment patterns;
- stable text, JSON, and SARIF output.

## Boundary

A pass means the checked files satisfy the current deterministic rules. It does
not prove that a skill is safe, correct, or authentic. The tool does not run
shell commands, install dependencies, or fetch URLs. For provenance and
signing, use Sigstore, cosign, in-toto, or SLSA. For a real sandbox, run the
skill inside an isolated environment.

See [SECURITY.md](SECURITY.md) for the threat model and reporting process.

## Development

```bash
python3 -m compileall -q src tests scripts
python3 tests/test_skill_verify.py
python3 scripts/skill_verify.py demo/good-skill
python3 scripts/skill_verify.py demo/broken-skill || true
```

The CI pipeline runs the tests on Python 3.8 and 3.12, requires the good demo
to pass, requires the broken demo to fail, validates SARIF as JSON, and
exercises the composite action.

## License

MIT. See [LICENSE](LICENSE).

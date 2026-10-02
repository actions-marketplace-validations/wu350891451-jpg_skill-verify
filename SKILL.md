---
name: skill-verify
description: Statically verify an Agent Skill before installation or publication. Use when checking a SKILL.md for schema problems, broken local references, path escapes, prompt-injection phrases, credential-exfiltration text, remote shell execution, destructive commands, hidden Unicode, or instruction-like HTML comments.
metadata:
  short-description: Verify Agent Skills before trusting them
---

# Skill Verify

Run deterministic checks over `SKILL.md` files. The tool does not execute the
skill, call a model, or make network requests. It resolves local references,
parses frontmatter, and scans text for a small set of high-signal risk
patterns.

## Workflow

1. Point the CLI at a skill directory, a `SKILL.md`, or a tree with the
   `--recursive` flag.
2. Treat exit code 1 as a failing gate.
3. Read the rule id, line number, evidence, and remediation for each finding.
4. Use SARIF output when the result should appear in GitHub code scanning.

```bash
python3 scripts/skill_verify.py path/to/skill
python3 scripts/skill_verify.py skills/ --recursive --format json
python3 scripts/skill_verify.py path/to/skill --format sarif --output results.sarif
```

The rule catalog is in `references/rules.md`. The verifier checks mechanically
observable properties only. A pass is not a sandbox result, a provenance
signature, or proof that the skill is harmless.

## Rules that matter

- Fail closed on missing frontmatter, invalid names, missing local paths, or
  references that escape the skill directory.
- Scan for instruction-override and credential-disclosure text, remote
  download-to-shell pipelines, unbounded deletion commands, and hidden
  direction-control characters.
- Keep the output stable enough for CI: text for humans, JSON for automation,
  SARIF for code scanning.


# Rule catalog

`skill-verify` uses stable rule ids so CI output can be compared across runs.

## Structure and references

| Rule | Severity | Check |
|---|---|---|
| `SV000` | error | `SKILL.md` could not be read |
| `SV001` | error | YAML frontmatter is missing or unterminated |
| `SV002` | error | frontmatter has no `name` |
| `SV003` | error | `name` is not lowercase kebab-case |
| `SV004` | error | frontmatter has no `description` |
| `SV005` | warning | `description` exceeds 1024 characters |
| `SV006` | error | `name` does not match the containing directory |
| `SV010` | error | a referenced local path does not exist |
| `SV012` | error | a referenced path escapes the skill directory |

Local references are collected from Markdown links, HTML `src`/`href`
attributes, and inline code spans. URLs, anchors, shell commands, glob
patterns, and template placeholders are ignored.

If a path is created at runtime, keep the check explicit by passing
`--allow-missing <glob>`. This exemption only applies to missing files; a path
that escapes the skill directory remains `SV012`.

## Instruction risk

| Rule | Severity | Check |
|---|---|---|
| `SV020` | error | phrase instructs the agent to ignore prior or system instructions |
| `SV021` | error | phrase asks to reveal hidden instructions, secrets, or credentials |
| `SV022` | error | phrase asks to exfiltrate secrets, tokens, or environment files |
| `SV023` | error | remote content is piped directly into a shell |
| `SV024` | error | unbounded destructive deletion command |
| `SV025` | warning | instruction asks the agent to hide behavior from the user |
| `SV026` | error | invisible or bidirectional Unicode control character |
| `SV027` | warning | HTML comment contains instruction-like hidden text |

These checks are intentionally narrow. They catch common strings that should
not appear in an untrusted skill, but they do not prove intent and do not make
the skill safe. A malicious skill can avoid every pattern in this file.

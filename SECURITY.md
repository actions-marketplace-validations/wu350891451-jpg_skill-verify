# Security policy

## Threat model

`skill-verify` is a static checker. It assumes the repository and the `PATH`
provided by the caller are untrusted input.

It does not:

- execute scripts referenced by a skill;
- install packages;
- make network requests;
- follow instructions found in a skill;
- prove that a skill is harmless.

It does:

- read `SKILL.md` files and referenced local paths;
- inspect bytes for malformed structure, broken references, path escapes, and
  a narrow set of instruction-risk patterns;
- return a non-zero exit code suitable for CI.

## Reporting a vulnerability

Open a private security advisory on GitHub:
https://github.com/wu350891451-jpg/skill-verify/security/advisories/new

Include the affected version, a minimal input, the observed result, and the
expected result. Do not include live credentials or private skill content.

## Supported versions

Security fixes are applied to the latest tagged release and `main`.


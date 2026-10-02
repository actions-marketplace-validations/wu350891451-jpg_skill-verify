"""Extract and validate local paths referenced by a SKILL.md."""

from __future__ import annotations

import re
from fnmatch import fnmatchcase
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence
from urllib.parse import unquote

from .model import Finding


KNOWN_DIRS = ("scripts/", "references/", "assets/", "examples/", "templates/", "data/")
KNOWN_EXTENSIONS = (
    ".md",
    ".py",
    ".sh",
    ".bash",
    ".zsh",
    ".js",
    ".mjs",
    ".ts",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".txt",
    ".html",
    ".css",
    ".csv",
)

MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]\n]*\]\(\s*([^)\n]*)\)")
HTML_REF_RE = re.compile(r"""\b(?:src|href)\s*=\s*["']([^"']+)["']""", re.I)
INLINE_CODE_RE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")
BARE_FILE_RE = re.compile(
    r"^[A-Za-z0-9._-]+\.(?:md|py|sh|bash|zsh|js|mjs|ts|json|ya?ml|toml|txt|html|css|csv)$"
)


@dataclass(frozen=True)
class Reference:
    target: str
    line: int
    source: str


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _normalise_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    return target.strip().rstrip(".,;:")


def _normalise_markdown_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        return _normalise_target(target[: target.index(">") + 1])

    # A quoted destination may be followed by a title.
    if target[:1] in ("'", '"'):
        quote = target[0]
        end = target.find(quote, 1)
        if end != -1:
            return _normalise_target(target[1:end])

    # Unescaped spaces are accepted when there is no title-like suffix. This
    # keeps existing local links such as `references/a long name.md` usable.
    parts = target.split()
    if len(parts) > 1 and parts[-1][:1] in ("'", '"', "("):
        return _normalise_target(parts[0])
    return _normalise_target(target)


def _is_candidate(target: str) -> bool:
    if not target or len(target) > 300:
        return False
    lowered = target.lower()
    if lowered.startswith(
        (
            "http://",
            "https://",
            "mailto:",
            "data:",
            "tel:",
            "javascript:",
            "#",
            "~/",
        )
    ):
        return False
    if any(token in target for token in ("*", "{", "}", "$", "<", ">", "|")):
        return False
    if any(char.isspace() for char in target):
        return False
    if target.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", target):
        return True
    if target.startswith(("./", "../")):
        return True
    if target.startswith(KNOWN_DIRS):
        return True
    return bool(BARE_FILE_RE.match(target))


def extract_references(text: str) -> List[Reference]:
    refs: List[Reference] = []
    for match in MARKDOWN_LINK_RE.finditer(text):
        target = _normalise_markdown_target(match.group(1))
        if _is_candidate(target):
            refs.append(Reference(target, _line_number(text, match.start()), "markdown-link"))
    for match in HTML_REF_RE.finditer(text):
        target = _normalise_target(match.group(1))
        if _is_candidate(target):
            refs.append(Reference(target, _line_number(text, match.start()), "html-reference"))
    for match in INLINE_CODE_RE.finditer(text):
        target = _normalise_target(match.group(1))
        if _is_candidate(target):
            refs.append(Reference(target, _line_number(text, match.start()), "inline-code"))

    deduped = []
    seen = set()
    for ref in refs:
        key = (ref.target, ref.line)
        if key not in seen:
            seen.add(key)
            deduped.append(ref)
    return deduped


def validate_references(
    references: Iterable[Reference],
    skill_root: Path,
    allow_missing: Sequence[str] = (),
) -> List[Finding]:
    findings: List[Finding] = []
    resolved_root = skill_root.resolve()
    for ref in references:
        target = unquote(ref.target)
        candidate = Path(target)
        if not candidate.is_absolute():
            candidate = skill_root / candidate
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate

        if candidate.is_absolute() or target.startswith("../"):
            try:
                resolved.relative_to(resolved_root)
            except ValueError:
                findings.append(
                    Finding(
                        rule_id="SV012",
                        severity="error",
                        line=ref.line,
                        message="referenced path escapes the skill directory",
                        evidence=ref.target,
                        remediation="Keep skill resources inside the skill directory.",
                    )
                )
                continue

        if not resolved.exists():
            if any(fnmatchcase(target, pattern) for pattern in allow_missing):
                continue
            findings.append(
                Finding(
                    rule_id="SV010",
                    severity="error",
                    line=ref.line,
                    message="referenced local path does not exist",
                    evidence=ref.target,
                    remediation="Create the referenced file or remove the stale path.",
                )
            )
    return findings

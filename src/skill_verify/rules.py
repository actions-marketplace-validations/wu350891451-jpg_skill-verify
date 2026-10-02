"""Deterministic prompt-injection and unsafe-instruction checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List

from .model import Finding


@dataclass(frozen=True)
class PatternRule:
    rule_id: str
    severity: str
    pattern: str
    message: str
    remediation: str
    flags: int = re.IGNORECASE

    def compiled(self) -> re.Pattern:
        return re.compile(self.pattern, self.flags)


RULES = (
    PatternRule(
        "SV020",
        "error",
        r"\b(?:ignore|disregard|forget)\b.{0,60}\b(?:previous|prior|above|earlier|system)\b"
        r".{0,40}\b(?:instructions?|prompts?|rules?)\b",
        "instruction-override phrase",
        "Rewrite the skill so it cannot be read as an instruction to ignore higher-priority rules.",
    ),
    PatternRule(
        "SV021",
        "error",
        r"\b(?:reveal|print|show|dump|expose|leak)\b.{0,60}"
        r"\b(?:system prompt|developer message|hidden instructions?|secrets?|credentials?|api[_-]?keys?|tokens?)\b",
        "prompt or credential disclosure phrase",
        "Remove requests to expose hidden instructions or credentials.",
    ),
    PatternRule(
        "SV022",
        "error",
        r"\b(?:exfiltrate|steal|upload|send)\b.{0,80}"
        r"\b(?:secrets?|tokens?|credential|password|api[_-]?key|\.env)\b",
        "credential exfiltration phrase",
        "Remove data-transfer instructions that target credentials.",
    ),
    PatternRule(
        "SV023",
        "error",
        r"\b(?:curl|wget|iwr|Invoke-WebRequest)\b[^\n|]{0,160}\|\s*"
        r"(?:bash|sh|zsh|pwsh|powershell|iex|Invoke-Expression)\b",
        "remote content is piped directly into a shell",
        "Download to a file, verify its digest, and then execute it.",
    ),
    PatternRule(
        "SV024",
        "error",
        r"\brm\s+(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*)\s+(?:/|~|\*)",
        "unbounded destructive command",
        "Narrow the target and require an explicit confirmation step.",
    ),
    PatternRule(
        "SV025",
        "warning",
        r"\b(?:do not|don't|never)\b.{0,40}\b(?:tell|show|inform|mention|notify)\b"
        r".{0,40}\b(?:user|human)\b",
        "instruction asks the agent to hide behavior from the user",
        "State the behavior explicitly instead of asking the agent to conceal it.",
    ),
)

INVISIBLE_CHARS = {
    "\u200b": "zero width space",
    "\u200c": "zero width non-joiner",
    "\u200d": "zero width joiner",
    "\u200e": "left-to-right mark",
    "\u200f": "right-to-left mark",
    "\u202a": "left-to-right embedding",
    "\u202b": "right-to-left embedding",
    "\u202c": "pop directional formatting",
    "\u202d": "left-to-right override",
    "\u202e": "right-to-left override",
    "\u2060": "word joiner",
    "\u2066": "left-to-right isolate",
    "\u2067": "right-to-left isolate",
    "\u2068": "first strong isolate",
    "\u2069": "pop directional isolate",
    "\ufeff": "zero width no-break space",
}

HIDDEN_COMMENT_RE = re.compile(r"<!--(.*?)-->", re.DOTALL)
HIDDEN_KEYWORD_RE = re.compile(
    r"\b(?:ignore|disregard|system prompt|secret|token|credential|exfiltrate|"
    r"do not tell|hide from)\b",
    re.IGNORECASE,
)


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _context(text: str, start: int, end: int, limit: int = 120) -> str:
    left = max(0, start - limit // 3)
    right = min(len(text), end + limit // 3)
    return " ".join(text[left:right].split())


def scan_text(
    text: str, excluded_rules: Iterable[str] = ()
) -> List[Finding]:
    excluded = set(excluded_rules)
    findings: List[Finding] = []

    for rule in RULES:
        if rule.rule_id in excluded:
            continue
        for match in rule.compiled().finditer(text):
            findings.append(
                Finding(
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    line=_line_number(text, match.start()),
                    message=rule.message,
                    evidence=_context(text, match.start(), match.end()),
                    remediation=rule.remediation,
                )
            )

    if "SV026" not in excluded:
        for index, char in enumerate(text):
            if char in INVISIBLE_CHARS:
                # A UTF-8 BOM at byte zero is tolerated; elsewhere it is hidden text.
                if char == "\ufeff" and index == 0:
                    continue
                findings.append(
                    Finding(
                        rule_id="SV026",
                        severity="error",
                        line=_line_number(text, index),
                        message="invisible or bidirectional Unicode control character",
                        evidence=INVISIBLE_CHARS[char],
                        remediation="Remove hidden direction or zero-width characters.",
                    )
                )

    if "SV027" not in excluded:
        for match in HIDDEN_COMMENT_RE.finditer(text):
            if HIDDEN_KEYWORD_RE.search(match.group(1)):
                findings.append(
                    Finding(
                        rule_id="SV027",
                        severity="warning",
                        line=_line_number(text, match.start()),
                        message="HTML comment contains hidden instruction-like text",
                        evidence=_context(text, match.start(), match.end()),
                        remediation="Move useful guidance into visible skill documentation.",
                    )
                )

    return findings

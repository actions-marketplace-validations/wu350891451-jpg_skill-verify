"""Small, dependency-free parser for Agent Skills frontmatter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from .model import Finding


@dataclass
class FrontMatter:
    name: str = ""
    description: str = ""
    body_start: int = 1
    raw: str = ""


def _strip_inline_comment(value: str) -> str:
    quote = ""
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in ("'", '"'):
            if quote == char:
                quote = ""
            elif not quote:
                quote = char
            continue
        if char == "#" and not quote and index > 0 and value[index - 1].isspace():
            return value[:index].rstrip()
    return value.rstrip()


def _unquote(value: str) -> str:
    value = _strip_inline_comment(value).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1]
        if value[:1] == "'":
            return value.replace("''", "'")
        return value.replace('\\"', '"').replace("\\n", "\n")
    return value


def parse_frontmatter(
    text: str, path: Path
) -> Tuple[Optional[FrontMatter], List[Finding]]:
    """Parse the common Agent Skills frontmatter shape.

    This intentionally implements only the scalar/block-scalar subset needed by
    SKILL.md files. Nested metadata is tolerated and ignored.
    """

    findings: List[Finding] = []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        findings.append(
            Finding(
                rule_id="SV001",
                severity="error",
                line=1,
                message="missing YAML frontmatter delimited by ---",
                remediation="Start SKILL.md with name and description in YAML frontmatter.",
            )
        )
        return None, findings

    closing = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing = index
            break
    if closing is None:
        findings.append(
            Finding(
                rule_id="SV001",
                severity="error",
                line=1,
                message="unterminated YAML frontmatter",
                remediation="Add a closing --- line before the Markdown body.",
            )
        )
        return None, findings

    raw_lines = lines[1:closing]
    values = {}
    index = 0
    while index < len(raw_lines):
        line = raw_lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        if line[0].isspace():
            index += 1
            continue
        if ":" not in line:
            findings.append(
                Finding(
                    rule_id="SV004",
                    severity="warning",
                    line=index + 2,
                    message="frontmatter line is not a key: value pair",
                    evidence=line.strip(),
                )
            )
            index += 1
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value in ("|", "|-", ">", ">-"):
            block_lines = []
            cursor = index + 1
            while cursor < len(raw_lines):
                candidate = raw_lines[cursor]
                if candidate and not candidate[0].isspace():
                    break
                block_lines.append(candidate[1:] if candidate[:1] == " " else candidate)
                cursor += 1
            if value.startswith(">"):
                values[key] = " ".join(part.strip() for part in block_lines).strip()
            else:
                values[key] = "\n".join(block_lines).rstrip()
            index = cursor
            continue

        if key in ("name", "description"):
            values[key] = _unquote(value)
        index += 1

    name = values.get("name", "").strip()
    description = values.get("description", "").strip()
    frontmatter = FrontMatter(
        name=name,
        description=description,
        body_start=closing + 2,
        raw="\n".join(raw_lines),
    )
    return frontmatter, findings


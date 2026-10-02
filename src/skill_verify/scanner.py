"""Top-level skill and directory scanner."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable, List, Sequence

from .frontmatter import parse_frontmatter
from .model import Finding, ScanReport, SkillResult
from .references import extract_references, validate_references
from .rules import scan_text


SKIP_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "__pycache__"}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def scan_skill(
    skill_md: Path,
    excluded_rules: Sequence[str] = (),
    allow_missing: Sequence[str] = (),
) -> SkillResult:
    skill_md = skill_md.resolve()
    root = skill_md.parent
    try:
        text = skill_md.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        result = SkillResult(path=skill_md, root=root)
        result.add(
            Finding(
                rule_id="SV000",
                severity="error",
                line=1,
                message="SKILL.md could not be read",
                evidence=str(exc),
            )
        )
        return result

    if text.startswith("\ufeff"):
        text = text[1:]

    frontmatter, findings = parse_frontmatter(text, skill_md)
    result = SkillResult(path=skill_md, root=root)
    for finding in findings:
        result.add(finding)

    if frontmatter is not None:
        result.name = frontmatter.name
        result.description = frontmatter.description
        if "SV002" not in excluded_rules and not frontmatter.name:
            result.add(
                Finding(
                    rule_id="SV002",
                    severity="error",
                    line=2,
                    message="frontmatter is missing name",
                    remediation="Add a kebab-case name to SKILL.md frontmatter.",
                )
            )
        elif "SV003" not in excluded_rules and not NAME_RE.match(frontmatter.name):
            result.add(
                Finding(
                    rule_id="SV003",
                    severity="error",
                    line=2,
                    message="skill name must be lowercase kebab-case",
                    evidence=frontmatter.name,
                    remediation="Use only lowercase letters, digits, and single hyphens.",
                )
            )
        if "SV004" not in excluded_rules and not frontmatter.description:
            result.add(
                Finding(
                    rule_id="SV004",
                    severity="error",
                    line=2,
                    message="frontmatter is missing description",
                    remediation="Add a specific one-paragraph description.",
                )
            )
        elif "SV005" not in excluded_rules and len(frontmatter.description) > 1024:
            result.add(
                Finding(
                    rule_id="SV005",
                    severity="warning",
                    line=2,
                    message="description exceeds 1024 characters",
                    evidence=str(len(frontmatter.description)),
                    remediation="Keep the description concise and move detail into the body.",
                )
            )
        if (
            "SV006" not in excluded_rules
            and frontmatter.name
            and NAME_RE.match(frontmatter.name)
            and root.name != frontmatter.name
        ):
            result.add(
                Finding(
                    rule_id="SV006",
                    severity="error",
                    line=2,
                    message="skill name does not match its directory name",
                    evidence="name={} directory={}".format(frontmatter.name, root.name),
                    remediation="Rename the directory or update the frontmatter name.",
                )
            )

    for finding in scan_text(text, excluded_rules=excluded_rules):
        result.add(finding)
    for finding in validate_references(
        extract_references(text), root, allow_missing=allow_missing
    ):
        result.add(finding)
    return result


def discover_skills(path: Path, recursive: bool = False) -> List[Path]:
    path = path.resolve()
    if path.is_file():
        return [path]
    if not path.is_dir():
        return []
    direct = path / "SKILL.md"
    if direct.is_file() and not recursive:
        return [direct]
    if not recursive:
        return []

    found: List[Path] = []
    for current_root, dirnames, filenames in os.walk(str(path)):
        dirnames[:] = sorted(name for name in dirnames if name not in SKIP_DIRS)
        if "SKILL.md" in filenames:
            found.append((Path(current_root) / "SKILL.md").resolve())
    return sorted(found)


def scan_paths(
    paths: Iterable[Path],
    recursive: bool = False,
    excluded_rules: Sequence[str] = (),
    allow_missing: Sequence[str] = (),
) -> ScanReport:
    roots = [path.resolve() for path in paths]
    skill_files: List[Path] = []
    for path in roots:
        skill_files.extend(discover_skills(path, recursive=recursive))

    deduped = sorted(set(skill_files))
    common_root = Path(os.path.commonpath([str(path) for path in roots])) if roots else Path.cwd()
    if common_root.is_file():
        common_root = common_root.parent
    return ScanReport(
        skills=[
            scan_skill(
                path,
                excluded_rules=excluded_rules,
                allow_missing=allow_missing,
            )
            for path in deduped
        ],
        root=common_root,
        excluded_rules=excluded_rules,
    )

"""Shared result types for skill verification."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence


SEVERITY_ORDER: Dict[str, int] = {"error": 0, "warning": 1}


@dataclass(frozen=True)
class Finding:
    """One mechanically detected issue."""

    rule_id: str
    severity: str
    line: int
    message: str
    evidence: str = ""
    remediation: str = ""

    def sort_key(self) -> tuple:
        return (
            self.line if self.line > 0 else 10**9,
            SEVERITY_ORDER.get(self.severity, 9),
            self.rule_id,
            self.message,
        )


@dataclass
class SkillResult:
    """Verification result for one SKILL.md."""

    path: Path
    root: Path
    name: str = ""
    description: str = ""
    findings: List[Finding] = field(default_factory=list)

    @property
    def errors(self) -> List[Finding]:
        return [item for item in self.findings if item.severity == "error"]

    @property
    def warnings(self) -> List[Finding]:
        return [item for item in self.findings if item.severity == "warning"]

    @property
    def status(self) -> str:
        return "fail" if self.errors else "pass"

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    def sorted_findings(self) -> Sequence[Finding]:
        return sorted(self.findings, key=lambda item: item.sort_key())

    def relative_path(self, base: Path) -> str:
        try:
            return str(self.path.relative_to(base))
        except ValueError:
            return str(self.path)


@dataclass
class ScanReport:
    """Aggregate result for a CLI or Action run."""

    skills: List[SkillResult]
    root: Path
    excluded_rules: Sequence[str] = ()

    @property
    def errors(self) -> int:
        return sum(len(skill.errors) for skill in self.skills)

    @property
    def warnings(self) -> int:
        return sum(len(skill.warnings) for skill in self.skills)

    @property
    def failed_skills(self) -> int:
        return sum(1 for skill in self.skills if skill.status == "fail")

    def exceeds(self, fail_on: str) -> bool:
        if fail_on == "none":
            return False
        if fail_on == "warning":
            return bool(self.errors or self.warnings)
        return bool(self.errors)


"""Render scan reports as text, JSON, or SARIF."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List

from . import __version__
from .model import Finding, ScanReport, SkillResult
from .rules import RULES


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def render_text(report: ScanReport) -> str:
    lines = [
        "skill-verify {}".format(__version__),
        "Scanned {} skill(s): {} passed, {} failed".format(
            len(report.skills),
            len(report.skills) - report.failed_skills,
            report.failed_skills,
        ),
    ]
    for skill in report.skills:
        rel = skill.relative_path(report.root)
        lines.append("")
        lines.append("{} {}".format(skill.status.upper(), rel))
        if not skill.findings:
            lines.append("  no findings")
            continue
        for finding in skill.sorted_findings():
            lines.append(
                "  {} {} line {}: {}".format(
                    finding.severity.upper(),
                    finding.rule_id,
                    finding.line,
                    finding.message,
                )
            )
            if finding.evidence:
                lines.append("    evidence: {}".format(finding.evidence))
            if finding.remediation:
                lines.append("    fix: {}".format(finding.remediation))
    lines.append("")
    lines.append(
        "Summary: {} error(s), {} warning(s)".format(report.errors, report.warnings)
    )
    return "\n".join(lines) + "\n"


def report_as_dict(report: ScanReport) -> Dict:
    return {
        "tool": "skill-verify",
        "version": __version__,
        "root": str(report.root),
        "summary": {
            "skills": len(report.skills),
            "passed": len(report.skills) - report.failed_skills,
            "failed": report.failed_skills,
            "errors": report.errors,
            "warnings": report.warnings,
        },
        "excluded_rules": list(report.excluded_rules),
        "skills": [
            {
                "path": _relative(skill.path, report.root),
                "root": _relative(skill.root, report.root),
                "name": skill.name,
                "status": skill.status,
                "errors": len(skill.errors),
                "warnings": len(skill.warnings),
                "findings": [
                    {
                        "rule_id": finding.rule_id,
                        "severity": finding.severity,
                        "line": finding.line,
                        "message": finding.message,
                        "evidence": finding.evidence,
                        "remediation": finding.remediation,
                    }
                    for finding in skill.sorted_findings()
                ],
            }
            for skill in report.skills
        ],
    }


def render_json(report: ScanReport) -> str:
    return json.dumps(report_as_dict(report), indent=2, sort_keys=True) + "\n"


def render_sarif(report: ScanReport) -> str:
    rules: List[Dict] = []
    known_rules = {rule.rule_id: rule for rule in RULES}
    extra_rules = [
        ("SV000", "Read error"),
        ("SV001", "Frontmatter syntax"),
        ("SV002", "Missing name"),
        ("SV003", "Invalid name"),
        ("SV004", "Missing description"),
        ("SV005", "Long description"),
        ("SV006", "Name/directory mismatch"),
        ("SV010", "Missing local reference"),
        ("SV012", "Reference escapes skill root"),
        ("SV026", "Invisible Unicode"),
        ("SV027", "Hidden instruction comment"),
    ]
    used_ids = sorted(
        {
            finding.rule_id
            for skill in report.skills
            for finding in skill.findings
        }
    )
    for rule_id in used_ids:
        if rule_id in known_rules:
            rule = known_rules[rule_id]
            rules.append(
                {
                    "id": rule_id,
                    "name": rule.message,
                    "shortDescription": {"text": rule.message},
                    "help": {"text": rule.remediation},
                }
            )
        else:
            label = dict(extra_rules).get(rule_id, rule_id)
            rules.append(
                {
                    "id": rule_id,
                    "name": label,
                    "shortDescription": {"text": label},
                }
            )

    results = []
    for skill in report.skills:
        for finding in skill.sorted_findings():
            results.append(
                {
                    "ruleId": finding.rule_id,
                    "level": finding.severity,
                    "message": {"text": finding.message},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {
                                    "uri": _relative(skill.path, report.root),
                                },
                                "region": {"startLine": max(1, finding.line)},
                            }
                        }
                    ],
                    "properties": {"evidence": finding.evidence},
                }
            )
    payload = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "skill-verify",
                        "version": __version__,
                        "informationUri": "https://github.com/wu350891451-jpg/skill-verify",
                        "rules": rules,
                    }
                },
                "results": results,
            }
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_github_outputs(path: Path, report: ScanReport, failed: bool) -> None:
    values = {
        "result": "fail" if failed else "pass",
        "errors": str(report.errors),
        "warnings": str(report.warnings),
        "failed-skills": str(report.failed_skills),
        "scanned-skills": str(len(report.skills)),
    }
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write("{}={}\n".format(key, value))


def write_output(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


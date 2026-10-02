"""Command-line interface for skill-verify."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from . import __version__
from .model import Finding, ScanReport
from .report import (
    render_json,
    render_sarif,
    render_text,
    write_github_outputs,
    write_output,
)
from .scanner import scan_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skill-verify",
        description="Statically verify Agent Skills for broken and unsafe instructions.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Skill directory, SKILL.md, or a directory to search (default: .)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively discover nested SKILL.md files.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "sarif"),
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Write the report to this file instead of stdout.",
    )
    parser.add_argument(
        "--fail-on",
        choices=("error", "warning", "none"),
        default="error",
        help="Exit 1 when findings reach this severity (default: error).",
    )
    parser.add_argument(
        "--exclude-rule",
        action="append",
        default=[],
        help="Suppress one rule id; may be repeated.",
    )
    parser.add_argument(
        "--allow-missing",
        action="append",
        default=[],
        help="Glob for a generated/runtime path that may be absent; may be repeated.",
    )
    parser.add_argument(
        "--github-output",
        default="",
        help="Append Action outputs to this file when set.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def _error(message: str) -> int:
    print("skill-verify: error: {}".format(message), file=sys.stderr)
    return 2


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    paths = [Path(item) for item in args.paths]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        return _error("path does not exist: {}".format(", ".join(missing)))

    excluded = sorted(set(args.exclude_rule))
    report = scan_paths(
        paths,
        recursive=args.recursive,
        excluded_rules=excluded,
        allow_missing=sorted(set(args.allow_missing)),
    )
    if not report.skills:
        return _error(
            "no SKILL.md found under: {}. Use --recursive for nested skills.".format(
                ", ".join(str(path) for path in paths)
            )
        )

    if args.format == "json":
        content = render_json(report)
    elif args.format == "sarif":
        content = render_sarif(report)
    else:
        content = render_text(report)

    if args.output:
        write_output(Path(args.output), content)
    else:
        sys.stdout.write(content)

    failed = report.exceeds(args.fail_on)
    if args.github_output:
        write_github_outputs(Path(args.github_output), report, failed)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

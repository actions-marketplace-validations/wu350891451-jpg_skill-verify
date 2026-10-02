#!/usr/bin/env python3
"""Repository wrapper so the tool runs without installation."""

import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skill_verify.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())


#!/usr/bin/env python3
"""Repo-root convenience wrapper: ``python install.py --global --hooks``.

The real installer lives inside the skill (``.claude/skills/super-skill/install.py``)
so it is also available after ``npx skills add`` installs only the skill folder.
"""
import runpy
import sys
from pathlib import Path

target = Path(__file__).resolve().parent / ".claude" / "skills" / "super-skill" / "install.py"
sys.argv[0] = str(target)
runpy.run_path(str(target), run_name="__main__")

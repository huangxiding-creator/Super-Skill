"""Deterministic toy mutator: reads MUTATION_PROMPT.md, finds the failed tasks'
``missing keyword '<kw>'`` feedback and appends ONE line containing the first
missing keyword to the target (smallest change). Writes MUTATION_DESC.txt.

    python toy_mutator.py <prompt> <target>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional, Sequence

_MISSING = re.compile(r"missing keyword '([^']+)'")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print("usage: toy_mutator.py <prompt> <target>", file=sys.stderr)
        return 2
    prompt_path, target = Path(args[0]), Path(args[1])
    prompt = prompt_path.read_text(encoding="utf-8")
    failed_section = prompt.split("## Gene strategy", 1)[0]
    missing = _MISSING.findall(failed_section)
    if not missing:
        return 0  # nothing to fix -> no-op
    kw = missing[0]
    text = target.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    target.write_text(text + f"- {kw}: covered.\n", encoding="utf-8")
    (prompt_path.parent / "MUTATION_DESC.txt").write_text(f"add keyword {kw}\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Lint CONTEXT.md glossaries and docs/adr/ numbering (real-engineering skill).

Verifies the two artifacts the ubiquitous-language discipline produces:

- CONTEXT.md  — every **Term** header is followed by a non-empty definition;
                _Avoid_ lines only appear inside a term entry and carry values;
                no duplicate terms.
- docs/adr/   — files match NNNN-slug.md; numbers are unique; each file has
                an H1. Gaps are allowed (superseded ADRs may be removed).

Missing paths are NOT errors: both formats are created lazily by design.

Usage:
    python context_lint.py [CONTEXT.md-path] [adr-dir]... [--json]
Exit code 0 = clean (or nothing to lint); 1 = lint errors found.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TERM_HEADER_RE = re.compile(r"^\*\*(?P<term>.+?)\*\*:?\s*$")
AVOID_RE = re.compile(r"^_Avoid_\s*:\s*(?P<value>.*)$", re.IGNORECASE)
ADR_FILE_RE = re.compile(r"^(?P<num>\d{4})-[a-z0-9][a-z0-9-]*\.md$")
HEADING_RE = re.compile(r"^#\s+")


def _force_utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def lint_context_text(text: str) -> list[str]:
    """Return a list of error strings for a CONTEXT.md glossary body."""
    errors: list[str] = []
    seen_terms: dict[str, int] = {}
    current_term: str | None = None
    definition_lines: list[str] = []

    def _close(term: str, lines: list[str], lineno: int) -> None:
        if not any(part.strip() for part in lines):
            errors.append(f"line {lineno}: term '{term}' has no definition")

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        term_match = TERM_HEADER_RE.match(line)

        if term_match:
            if current_term is not None:
                _close(current_term, definition_lines, lineno - 1)
            current_term = term_match.group("term").strip()
            key = current_term.casefold()
            if key in seen_terms:
                errors.append(
                    f"line {lineno}: duplicate term '{current_term}' "
                    f"(first defined on line {seen_terms[key]})"
                )
            else:
                seen_terms[key] = lineno
            definition_lines = []
            continue

        avoid_match = AVOID_RE.match(line.strip())
        if avoid_match:
            if current_term is None:
                errors.append(
                    f"line {lineno}: _Avoid_ entry outside any term definition"
                )
            elif not avoid_match.group("value").strip():
                errors.append(
                    f"line {lineno}: _Avoid_ entry for '{current_term}' is empty"
                )
            continue

        if line.strip() == "" or HEADING_RE.match(line):
            if current_term is not None:
                _close(current_term, definition_lines, lineno)
                current_term = None
                definition_lines = []
            continue

        if current_term is not None:
            definition_lines.append(line)

    if current_term is not None:
        _close(current_term, definition_lines, len(text.splitlines()))

    return errors


def lint_adr_dir(adr_dir: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for an ADR directory."""
    errors: list[str] = []
    warnings: list[str] = []
    if not adr_dir.is_dir():
        return errors, warnings

    numbers: dict[str, str] = {}
    for entry in sorted(adr_dir.iterdir()):
        if not entry.is_file():
            continue
        match = ADR_FILE_RE.match(entry.name)
        if match is None:
            if entry.suffix.lower() == ".md":
                warnings.append(
                    f"{entry.name}: ADR filename must match NNNN-slug.md"
                )
            continue
        num = match.group("num")
        if num in numbers:
            errors.append(
                f"{entry.name}: duplicate ADR number {num} "
                f"(also used by {numbers[num]})"
            )
        else:
            numbers[num] = entry.name
        try:
            content = entry.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{entry.name}: unreadable ({exc})")
            continue
        first_line = content.splitlines()[0] if content.splitlines() else ""
        if not HEADING_RE.match(first_line):
            warnings.append(f"{entry.name}: missing H1 title on first line")

    return errors, warnings


def _classify(paths: list[Path]) -> tuple[Path, list[Path]]:
    """Split CLI paths into (context file, ADR dirs) — .md files vs the rest."""
    context_candidates = [p for p in paths if p.suffix.lower() == ".md"]
    adr_dirs = [p for p in paths if p.suffix.lower() != ".md"]
    context_path = context_candidates[-1] if context_candidates else Path("CONTEXT.md")
    if not adr_dirs:
        adr_dirs = [Path("docs/adr")]
    return context_path, adr_dirs


def run(context_path: Path, adr_dirs: list[Path]) -> dict:
    result: dict = {"context": [], "adr_errors": [], "adr_warnings": [], "checked": {}}

    if context_path.is_file():
        text = context_path.read_text(encoding="utf-8", errors="replace")
        result["context"] = lint_context_text(text)
        result["checked"]["context"] = str(context_path)
    else:
        result["checked"]["context"] = None

    for adr_dir in adr_dirs:
        errors, warnings = lint_adr_dir(adr_dir)
        result["adr_errors"].extend(f"{adr_dir}: {e}" for e in errors)
        result["adr_warnings"].extend(f"{adr_dir}: {w}" for w in warnings)
        result["checked"][str(adr_dir)] = adr_dir.is_dir()

    return result


def main(argv: list[str] | None = None) -> int:
    _force_utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "paths",
        nargs="*",
        help="CONTEXT.md path and/or ADR directories (default: CONTEXT.md docs/adr)",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    context_path, adr_dirs = _classify([Path(p) for p in args.paths])
    result = run(context_path, adr_dirs)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["checked"]["context"] is None:
            print("note: no CONTEXT.md found (lazy creation — nothing to lint)")
        for err in result["context"]:
            print(f"CONTEXT.md: {err}")
        for err in result["adr_errors"]:
            print(f"error: {err}")
        for warn in result["adr_warnings"]:
            print(f"warning: {warn}")
        total = len(result["context"]) + len(result["adr_errors"])
        print(
            f"context_lint: {total} error(s), "
            f"{len(result['adr_warnings'])} warning(s)"
        )

    return 1 if (result["context"] or result["adr_errors"]) else 0


if __name__ == "__main__":
    sys.exit(main())
